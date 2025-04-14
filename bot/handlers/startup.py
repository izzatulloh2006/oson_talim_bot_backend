from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
import aiohttp

router = Router(name="startup")
API_URL = "http://127.0.0.1:8000/api/v1/startups/"

class StartupStates(StatesGroup):
    waiting_for_startup = State()

async def get_startups_keyboard(current_index: int, total_startups: int):
    keyboard = []

    row = []
    if current_index > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"startup_previous_{current_index}"))
    if current_index < total_startups - 1:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"startup_next_{current_index}"))

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.text.in_(["🚀 Startaplar"]))
async def startups_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Startap yuborish", callback_data="submit_startup")],
        [InlineKeyboardButton(text="🔍 Startaplarni ko'rish", callback_data="view_startups")]
    ])
    await message.answer("Startaplar bo'limiga xush kelibsiz!", reply_markup=keyboard)

@router.callback_query(F.data == "view_startups")
async def view_startups(call: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status != 200:
                await call.message.answer("Startaplarni olishda xato yuz berdi.")
                return

            startups = await response.json()
            startups = startups[::-1]  # Reverse the startups list

            if not startups:
                await call.message.answer("Hozirda startaplar mavjud emas.")
                return

            current_index = 0
            total_startups = len(startups)

            startup = startups[current_index]
            text = f"""<b>Startap:</b> {startup['name']}\n\n<b>📋 Tavsif:</b> {startup['description']}\n\n<b>👤 Muallif:</b> {startup['creator']}"""
            keyboard = await get_startups_keyboard(current_index, total_startups)
            await call.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

            await call.answer()

@router.callback_query(lambda c: c.data.startswith('startup_previous_') or c.data.startswith('startup_next_'))
async def handle_startups_navigation(callback_query: CallbackQuery):
    action, current_index = callback_query.data.replace("startup_", "").split('_')
    current_index = int(current_index)

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status != 200:
                await callback_query.answer("Startaplarni olishda xato yuz berdi.")
                return

            startups = await response.json()
            startups = startups[::-1]  # Reverse the startups list
            total_startups = len(startups)

            if action == 'previous' and current_index > 0:
                new_index = current_index - 1
            elif action == 'next' and current_index < total_startups - 1:
                new_index = current_index + 1
            else:
                await callback_query.answer("Endi startaplar mavjud emas.")
                return

            startup = startups[new_index]
            response_text = f"""<b>Startap:</b> {startup['name']}\n\n<b>📋 Tavsif:</b> {startup['description']}\n\n<b>👤 Muallif:</b> {startup['creator']}"""
            keyboard = await get_startups_keyboard(new_index, total_startups)
            await callback_query.message.edit_text(response_text, parse_mode="HTML")
            await callback_query.message.edit_reply_markup(reply_markup=keyboard)

    await callback_query.answer()

@router.callback_query(F.data == "submit_startup")
async def submit_startup(call: CallbackQuery):
    await call.message.answer(f"Startap yuborish uchun admin bilan bog'laning. @adm_tbizness")
    await call.answer()

@router.callback_query(F.data == "back")
async def handle_back(callback_query: CallbackQuery):
    await callback_query.message.edit_text("🏠 Asaosiy menuga qaytdingiz", parse_mode="HTML")
    await callback_query.answer()
