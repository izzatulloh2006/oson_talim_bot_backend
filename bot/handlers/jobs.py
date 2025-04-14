import aiohttp
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router(name="jobs")
API_URL = "http://127.0.0.1:8000/api/v1/jobs/"


async def get_jobs_keyboard(current_index: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status != 200:
                return InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="❌ Xatolik", callback_data="back")]])

            jobs = await response.json()
            if not jobs:
                return InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")]])

            keyboard = []

            # job_title = jobs[current_index]["title"]
            # keyboard.append([InlineKeyboardButton(text="🔹 Ish o'rni", callback_data="none")])  # Just a static text

            row = []
            if current_index > 0:
                row.append(InlineKeyboardButton(text="⬅️", callback_data=f"job_previous_{current_index}"))
            if current_index < len(jobs) - 1:
                row.append(InlineKeyboardButton(text="➡️", callback_data=f"job_next_{current_index}"))

            if row:
                keyboard.append(row)

            keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")])

            return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text.in_(["👔 Tayyor Xodim"]))
async def show_jobs_menu(message: Message):
    keyboard = await get_jobs_keyboard(0)

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                jobs = await response.json()

                if jobs:
                    job = jobs[0]
                    response_text = (
                        f"🏢 <b>{job['title']}</b>\n\n"
                        f"💵 <b>Ish haqi:</b> {job.get('salary', 'Kelishilgan')}\n"
                        f"☎️ <b>Bog‘lanish:</b> {job.get('contact_info', 'Admin @username')}\n\n"
                        f"{job.get('description', 'Tavsif mavjud emas')}\n"
                    )

                    await message.answer(response_text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await message.answer("No jobs available at the moment.", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith('job_previous_') or c.data.startswith('job_next_'))
async def handle_jobs_navigation(callback_query: CallbackQuery):
    action, current_index = callback_query.data.replace("job_", "").split('_')
    current_index = int(current_index)
    new_index = current_index - 1 if action == 'previous' else current_index + 1

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                jobs = await response.json()
                if 0 <= new_index < len(jobs):
                    job = jobs[new_index]

                    response_text = (
                        f"🏢 <b>{job['title']}</b>\n\n"
                        f"💵 <b>Ish haqi:</b> {job.get('salary', 'Kelishilgan')}\n"
                        f"☎️ <b>Bog‘lanish:</b> {job.get('contact_info', 'Admin @username')}\n\n"
                        f"{job.get('description', 'Tavsif mavjud emas')}\n"
                    )

                    await callback_query.message.edit_text(response_text, parse_mode="HTML")
                    keyboard = await get_jobs_keyboard(new_index)
                    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
            else:
                await callback_query.answer("Tayyor hodimlar olishda xato yuz berdi.")

    await callback_query.answer()

@router.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: CallbackQuery):
    await callback_query.message.edit_text("🏠 Asaosiy menuga qaytdingiz", parse_mode="HTML")
