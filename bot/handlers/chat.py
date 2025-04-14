import os
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import logging


router = Router(name="chat")
load_dotenv()
ADMIN_ID = os.getenv("ADMIN_CHAT_ID")


class ChatStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()


@router.message(F.text.in_(["💬 Chat"]))
async def chat_menu(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ChatStates.waiting_for_message)
    await message.answer("Xabaringizni yuboring, admin javob beradi:")


@router.message(ChatStates.waiting_for_message)
async def handle_user_message(message: Message, bot: Bot, state: FSMContext):

    if message.text == "ℹ️ Obuna vaqti":
        await state.clear()
        return

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✍️ Javob yozish",
            callback_data=f"reply_{user_id}"
        )]
    ])

    try:
        if message.text:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✉️ Yangi xabar\nFoydalanuvchi: @{username}\n\n{message.text}",
                reply_markup=reply_markup
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=ADMIN_ID,
                photo=message.photo[-1].file_id,
                caption=f"📸 Yangi rasm\nFoydalanuvchi: @{username}",
                reply_markup=reply_markup
            )

        await message.answer("✅ Xabaringiz adminga yuborildi!")
    except Exception as e:
        logging.error(f"Xatolik adminga yuborishda: {e}")
        await message.answer("❌ Xabarni yuborishda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")


@router.callback_query(F.data.startswith("reply_"))
async def process_admin_reply(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])

    await state.set_state(ChatStates.waiting_for_admin_reply)
    await state.update_data(reply_to_user_id=user_id)

    await callback.message.answer(f"✍️ Javob yozish uchun xabarni yuboring (UserID: {user_id}):")
    await callback.answer()


@router.message(
    lambda message: str(message.chat.id) == ADMIN_ID,
    ChatStates.waiting_for_admin_reply,
    F.content_type.in_({"text", "photo"})
)
async def send_admin_reply(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('reply_to_user_id')

    try:
        if message.text:
            await bot.send_message(
                chat_id=user_id,
                text=f"📨 Admin javobi:\n\n{message.text}"
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption=f"📨 Admin javobi:\n\n{message.caption or ''}"
            )

        await message.answer(f"✅ Javob foydalanuvchiga yuborildi (ID: {user_id})")
        await state.clear()
    except Exception as e:
        logging.error(f"Admin javob yuborishda xato: {e}")
        await message.answer("❌ Javob yuborishda xatolik yuz berdi")
