from aiogram import Router, types
from aiogram.filters import Command
from bot.database import Database

router = Router(name="statistica")
db = Database()

@router.message(Command("statistika"))
async def send_statistics(message: types.Message):
    stats = await db.get_stats()
    top_user = await db.get_top_user()

    text = f"""📊 <b>Bot Statistikasi</b>

👨🏻‍💻 <b>Aktiv obunachilar soni</b> — {stats['total']} ta
📈 <b>So‘nggi 24 soatda</b> — +{stats['today']} ta
📅 <b>So‘nggi 1 oyda</b> — +{stats['month']} ta

💡 <b>Eng faol foydalanuvchi</b>: @{top_user['username']}
"""

    await message.answer(text)
