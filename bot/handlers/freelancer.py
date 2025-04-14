import aiohttp
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router(name="freelancer")
API_URL = "https://osontalimbott.pythonanywhere.com/api/v1/freelance/"

async def get_freelance_keyboard(current_index: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status != 200:
                return InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="❌ Xatolik", callback_data="back")]])

            projects = await response.json()
            projects = projects[::-1]  # Reverse the projects list
            if not projects:
                return InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")]])

            keyboard = []

            row = []
            if current_index > 0:
                row.append(InlineKeyboardButton(text="⬅️", callback_data=f"freelance_previous_{current_index}"))
            if current_index < len(projects) - 1:
                row.append(InlineKeyboardButton(text="➡️", callback_data=f"freelance_next_{current_index}"))

            if row:
                keyboard.append(row)

            keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")])

            return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.text.in_(["💻 Frilanser"]))
async def show_freelancer_menu(message: Message):
    keyboard = await get_freelance_keyboard(0)

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                projects = await response.json()
                projects = projects[::-1]  # Reverse the projects list

                if projects:
                    project = projects[0]
                    response_text = (
                        f"💼 <b>{project['title']}</b>\n\n"
                        f"💰 <b>Byudjet:</b> {project.get('budget', 'Kelishilgan')}\n"
                        f"⏳ <b>Muddat:</b> {project.get('deadline', 'Aniqlanmagan')}\n\n"
                        f"{project.get('description', 'Loyiha haqida ma’lumot mavjud emas')}\n\n"
                        f"📩 <b>Aloqa:</b> {project.get('contact_email', 'Admin @username')}"
                    )

                    await message.answer(response_text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await message.answer("No freelance projects available at the moment.", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith('freelance_previous_') or c.data.startswith('freelance_next_'))
async def handle_freelancer_navigation(callback_query: CallbackQuery):
    action, current_index = callback_query.data.replace("freelance_", "").split('_')
    current_index = int(current_index)
    new_index = current_index - 1 if action == 'previous' else current_index + 1

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                projects = await response.json()
                projects = projects[::-1]  # Reverse the projects list
                if 0 <= new_index < len(projects):
                    project = projects[new_index]

                    response_text = (
                        f"💼 <b>{project['title']}</b>\n\n"
                        f"💰 <b>Byudjet:</b> {project.get('budget', 'Kelishilgan')}\n"
                        f"⏳ <b>Muddat:</b> {project.get('deadline', 'Aniqlanmagan')}\n\n"
                        f"{project.get('description', 'Loyiha haqida ma’lumot mavjud emas')}\n\n"
                        f"📩 <b>Aloqa:</b> {project.get('contact_email', 'Admin @username')}"
                    )

                    await callback_query.message.edit_text(response_text, parse_mode="HTML")
                    keyboard = await get_freelance_keyboard(new_index)
                    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
            else:
                await callback_query.answer("Freelance loyihalarini olishda xato yuz berdi.")

    await callback_query.answer()

@router.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: CallbackQuery):
    await callback_query.message.edit_text("🏠 Asaosiy menuga qaytdingiz", parse_mode="HTML")
    await callback_query.answer()
