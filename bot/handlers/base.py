from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.types import ContentType
from  bot.database import db
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime, timedelta
from bot.handlers.statistica import send_statistics
from typing import List, Dict
import os
import logging
import aiohttp


router = Router(name='base')
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


class LanguageStates(StatesGroup):
    waiting_for_contact = State()

class CourseStates(StatesGroup):
    watching = State()

class SubscriptionStates(StatesGroup):
    waiting_for_subscription = State()
    waiting_for_admin_confirm = State()
    waiting_for_institute_id = State()


WELCOME_TEXTS = {
"uz": """🎉 OsonTa'lim botiga xush kelibsiz! 🎉 Bu yerda sizning bilim va karyera yo'lingizni yuksaltirish uchun eng qulay va zamonaviy imkoniyatlar mavjud!
📌 Sizga taqdim etadigan xususiyatlar:
🌍 Har xil sohalarda foydali ma'lumotlar: O'zingiz uchun kerakli bilimlarni osongina oling va hayotingizni yaxshilang.
📘 Ta'lim va kasb-hunar kurslari: Siz uchun eng sifatli va ishonchli kurslarni tavsiya qilamiz.
🌍 Networking va tarmoq yaratish:
Yangi tanishlar va hamkorlarni topish. Investorlar bilan bog'lanish imkoniyati.
💼 Katta kompaniyalarga ishga joylashish imkoniyati: O'z orzuingizdagi ishga kirish uchun yo'riq va ko'mak olasiz!
🛠 Frilanser sifatida katta proyektlarda qatnashish: O'z mahoratingizni namoyish eting va muvaffaqiyatga erishing.
ℹ️ 4 oylik obuna narxi: 300,000 so'm 📚 Biz kurslarni sotmaymiz, faqat eng sifatli va ishonchli kurslarni tavsiya qilamiz. Sizga bilim va karyera rivoji uchun yo'l-yo'riq ko'rsatamiz!
📥 Obuna bo'lish va imkoniyatlardan foydalanish uchun: 👤 Admin bilan bog'laning: @adm_tbizness

🚀 O'zingizning kelajagingiz sari ilk qadamni hoziroq tashlang! Bizning bot - sizning rivojlanishingiz uchun eng yaxshi yordamchi! 😊"""

}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    lang = "uz"
    await state.update_data(language=lang)
    await db.update_user_language(message.from_user.id, lang)

    user_info = await db.get_user_info(message.from_user.id)

    if user_info and user_info.get("is_active") and user_info.get("phone_number"):
        await message.answer("👋 Salom! Siz allaqachon ro'yxatdan o'tgansiz.")
        await send_main_menu(message.bot, message.from_user.id, lang)
        return

    await message.answer(WELCOME_TEXTS[lang], parse_mode=ParseMode.HTML)

    contact_button = KeyboardButton(
        text="📱 Telefon raqamni ulashish",
        request_contact=True
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[contact_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "📞 Iltimos, telefon raqamingizni yuboring:",
        reply_markup=keyboard
    )
    await state.set_state(LanguageStates.waiting_for_contact)


@router.message(LanguageStates.waiting_for_contact, F.contact)
async def process_contact_via_button(message: Message, state: FSMContext, bot: Bot):
    phone_number = message.contact.phone_number
    await process_contact(message, phone_number, state)


async def process_contact(message: Message, phone_number: str, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("language", "uz")

    await db.update_user_phone(message.from_user.id, phone_number)

    await message.answer(
        "📌 Iltimos, sizni taklif qilgan shaxsning ID raqamini kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SubscriptionStates.waiting_for_institute_id)


@router.message(SubscriptionStates.waiting_for_institute_id, F.text)
async def process_institute_id(message: Message, state: FSMContext):
    institute_id = message.text.strip()
    institute_name = await db.get_institute_name_by_id(institute_id)

    if not institute_name:
        await message.answer("❌ Bunday ID topilmadi. Qaytadan urinib ko'ring.")
        return

    await state.update_data(institute_id=institute_id, institute_name=institute_name)
    lang = (await state.get_data()).get("language", "uz")

    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Obuna bo'lish",
        callback_data="subscribe"
    )

    await message.answer(
        "Obuna bo'lish uchun quyidagi tugmani bosing:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(SubscriptionStates.waiting_for_subscription)


@router.callback_query(F.data == "subscribe", SubscriptionStates.waiting_for_subscription)
async def process_subscription(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        user_data = await state.get_data()
        lang = user_data.get("language", "uz")
        institute_id = user_data.get("institute_id", "Noma'lum")

        user_info = await db.get_user_info(callback.from_user.id)
        if not user_info:
            raise ValueError("User not found in database")
        if institute_id:
            institute_name = await db.get_institute_name_by_id(institute_id)

        admin_text = (
            f"Yangi obuna so'rovi:\n"
            f"👤 Foydalanuvchi: @{callback.from_user.username or 'N/A'}\n"
            f"📱 Telefon: {user_info['phone_number']}\n"
            f"🌐 Til: {user_info['language']}\n"
            f"🎓 Institut: {institute_name or 'Nomalum'}"
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Tasdiqlash", callback_data=f"confirm_{callback.from_user.id}")
        builder.button(text="❌ Rad etish", callback_data=f"reject_{callback.from_user.id}")

        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, reply_markup=builder.as_markup())

        await callback.answer(
            "✅ So'rovingiz adminga yuborildi. Tasdiqlashni kuting yoki admin bilan bog'laning!",
            show_alert=True
        )

        await state.set_state(SubscriptionStates.waiting_for_admin_confirm)

    except Exception as e:
        logging.error(f"Subscription error: {e}")
        await callback.answer(
            "❌ Xatolik yuz berdi. Iltimos keyinroq urinib ko'ring.",
            show_alert=True
        )


@router.callback_query(F.data.startswith("confirm_"))
async def admin_confirm(callback: CallbackQuery, bot: Bot):
    try:
        user_id = int(callback.data.split("_")[1])

        # Obuna muddatini belgilash (30 kun)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)

        # Foydalanuvchini tasdiqlash
        await db.activate_user(user_id)

        # Obuna ma'lumotlarini yangilash
        await db.update_user_subscription(
            user_id=user_id,
            is_active=True,
            subscription_start=start_date.isoformat(),
            subscription_end=end_date.isoformat()
        )

        # Foydalanuvchiga xabar
        await bot.send_message(
            chat_id=user_id,
            text=f"""✅ Obunangiz tasdiqlandi!

📅 Boshlanish: {start_date.strftime('%d-%m-%Y %H:%M')}
📅 Tugash: {end_date.strftime('%d-%m-%Y %H:%M')}
⏳ Davomiylik: 30 kun"""
        )
        await callback.answer("Obuna tasdiqlandi", show_alert=True)

    except Exception as e:
        logging.error(f"Admin tasdiqlashda xato: {str(e)}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def admin_reject(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = int(callback.data.split("_")[1])

    # Get user language
    user_info = await db.get_user_info(user_id)
    lang = user_info.get("language", "uz")

    reject_text = {
        "uz": "❌ Sizning obuna so'rovingiz rad etildi. Batafsil: @adm_tbizness"
    }

    await bot.send_message(
        chat_id=user_id,
        text=reject_text[lang]
    )
    await callback.answer("Foydalanuvchi rad etildi", show_alert=True)


async def get_courses_from_api() -> List[Dict]:
    """API'dan kurslar ro'yxatini olish"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://127.0.0.1:8000/api/v1/courses/"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    # logging.info(f"API'dan olingan kurslar: {data}")
                    return data if isinstance(data, list) else []
                else:
                    logging.warning(f"API status: {response.status}")
                    return []
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching courses: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching courses: {e}")
    return []


async def get_course_videos(course_name: str) -> List[Dict]:
    """Berilgan kurs uchun videolar ro'yxatini olish"""
    try:
        # Avval kurslar ro'yxatini olish
        courses = await get_courses_from_api()
        course_id = None
        for course in courses:
            if course['name'] == course_name:
                course_id = course['id']
                break

        if not course_id:
            logging.warning(f"{course_name} kursi topilmadi")
            return []

        async with aiohttp.ClientSession() as session:
            url = f"http://127.0.0.1:8000/api/v1/videos/?course_name={course_name}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logging.info(f"API'dan olingan videolar ({course_name}): {data}")
                    # Faqat tanlangan kursga tegishli videolarni filtrlang
                    filtered_videos = [video for video in data if video['course'] == course_id]
                    logging.info(f"Filtrlangan videolar ({course_name}, course_id={course_id}): {filtered_videos}")
                    return filtered_videos if isinstance(filtered_videos, list) else []
                else:
                    logging.warning(f"API returned status code: {response.status}")
                    return []
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching videos: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching videos: {e}")
    return []


async def create_courses_keyboard() -> ReplyKeyboardMarkup:
    """Kurslar uchun dinamik klaviatura yaratish"""
    courses = await get_courses_from_api()
    logging.info(f"Kurslar ro'yxati: {courses}")
    builder = ReplyKeyboardBuilder()

    if not courses:
        # logging.warning("Kurslar ro'yxati bo'sh")
        builder.add(KeyboardButton(text="⚠️ Kurslar topilmadi"))
    else:
        for course in courses:
            if isinstance(course, dict) and 'name' in course:
                # logging.info(f"Kurs qo'shildi: {course['name']}")
                builder.add(KeyboardButton(text=course['name']))

    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


@router.message(F.text.in_(["⬅️ Orqaga"]))
async def handle_back(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('language', 'uz')

    current_state = await state.get_state()

    if current_state == "SubscriptionStates:waiting_for_subscription":
        await state.set_state(None)
        await send_main_menu(message.bot, message.from_user.id, lang)
    else:
        await send_main_menu(message.bot, message.from_user.id, lang)


async def send_main_menu(bot: Bot, user_id: int, lang: str):
    builder = ReplyKeyboardBuilder()

    user_info = await db.get_user_info(user_id)
    is_active = user_info.get('is_active', False) if user_info else False
    subscription_end = user_info.get('subscription_end') if user_info else None

    buttons = ["📚 O'quv kurslar", "👔 Tayyor Xodim", "💻 Frilanser", "🚀 Startaplar", "💬 Chat"]

    buttons.append("ℹ️ Obuna vaqti")


    if str(user_id) == ADMIN_CHAT_ID:
        buttons.append("📊 Statistika")

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))
    builder.adjust(2)

    menu_text = "Quyidagi menyudan kerakli bo'limni tanlang:"

    await bot.send_message(
        chat_id=user_id,
        text=menu_text,
        reply_markup=builder.as_markup(resize_keyboard=True))



@router.callback_query(F.data == "send_startup")
async def send_startup(call: CallbackQuery, state: FSMContext):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    text = "Yangi startap yuborish uchun adminni tasdiqlash zarur. Admin sizga javob beradi."

    await call.bot.send_message(ADMIN_CHAT_ID, f"Yangi startap yuborish: @{call.from_user.username}")

    await call.message.answer(text)
    await call.answer()


@router.message(F.text.in_(["📊 Statistika"]))
async def show_stats(message: Message):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    if str(message.from_user.id) == ADMIN_CHAT_ID:
        await send_statistics(message)
    else:
        await message.answer("Sizga ruxsat yo'q")


@router.message(F.content_type == ContentType.VIDEO)
async def video_handler(message: Message):
    if str(message.from_user.id) == ADMIN_CHAT_ID:
        await message.answer("✅ Video qabul qilindi!")
        await message.answer(f"📁 Video file_id: {message.video.file_id}")
    else:
        await message.answer("❌ Sizga video yuborish taqiqlangan!")
