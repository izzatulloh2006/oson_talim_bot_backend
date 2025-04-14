import logging
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.database import db
from bot.handlers.base import ADMIN_CHAT_ID

router = Router(name='subscriptions')

@router.message(F.text == "ℹ️ Obuna vaqti")
async def show_subscription_info(message: Message):
    try:
        user_info = await db.get_user_info(message.from_user.id)

        if not user_info:
            await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
            return

        if not (user_info.get('approved') or user_info.get('is_active')):
            await message.answer("❌ Obunangiz hali tasdiqlanmagan. Admin bilan bog'laning: @adm_tbizness")
            return

        # Obuna boshlanish va tugash sanasini olish
        subscription_start = user_info.get('subscription_start')
        subscription_end = user_info.get('subscription_end')

        # 🕓 Naive datetime bo‘lsa, UTC timezone bilan bog‘lab qo‘yamiz
        def make_aware(dt):
            if dt and dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        if not subscription_start:
            fallback_start = user_info.get('activated_at') or user_info.get('created_at')
            if fallback_start:
                if isinstance(fallback_start, str):
                    fallback_start = datetime.fromisoformat(fallback_start)
                subscription_start = make_aware(fallback_start)
                await db.update_user_subscription(
                    user_id=message.from_user.id,
                    subscription_start=subscription_start.isoformat()
                )
            else:
                await message.answer("❌ Obuna boshlanish vaqti topilmadi. Admin bilan bog'laning")
                return
        else:
            if isinstance(subscription_start, str):
                subscription_start = datetime.fromisoformat(subscription_start)
            subscription_start = make_aware(subscription_start)

        if not subscription_end:
            subscription_end = subscription_start + timedelta(days=30)
            await db.update_user_subscription(
                user_id=message.from_user.id,
                subscription_end=subscription_end.isoformat()
            )
        else:
            if isinstance(subscription_end, str):
                subscription_end = datetime.fromisoformat(subscription_end)
            subscription_end = make_aware(subscription_end)

        # Hisoblashlar
        now = datetime.now(timezone.utc)
        duration = (subscription_end - subscription_start).days
        time_left = max((subscription_end - now).days, 0)

        response = f"""📅 Obuna ma'lumotlari:

Boshlangan sana: {subscription_start.strftime('%d-%m-%Y %H:%M')}
Davomiyligi: {duration} kun
Qolgan vaqt: {time_left} kun"""

        if time_left <= 0:
            await db.update_user_subscription(user_id=message.from_user.id, is_active=False)
            response = f"""⚠️ Obunangiz tugagan!
{response}

Yangi obuna uchun: @adm_tbizness"""
        elif time_left <= 3:
            response += "\n\n⚠️ Obunangiz yaqinda tugaydi!"

        await message.answer(response)

    except Exception as e:
        logging.error(f"Xato (user_id={message.from_user.id}): {str(e)}", exc_info=True)
        await message.answer("❌ Texnik xatolik. Iltimos, keyinroq urinib ko'ring.")
