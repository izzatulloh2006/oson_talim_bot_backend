from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.handlers.base import get_courses_from_api
from typing import List, Dict
from bot.handlers.base import send_main_menu
import logging
import requests

router = Router(name='courses')


class CourseStates(StatesGroup):
    selecting_course = State()
    selecting_author = State()
    watching = State()


BASE_API_URL = "http://127.0.0.1:8000/api/v1/"


async def get_course_authors(course_id: int) -> List[Dict]:
    try:
        response = requests.get(f"{BASE_API_URL}courses/{course_id}/authors/")
        response.raise_for_status()
        authors_data = response.json()

        if isinstance(authors_data, list):
            return authors_data
        elif isinstance(authors_data, dict):
            return authors_data.get('authors', [])
        else:
            logging.error(f"Noto'g'ri javob formati (course_id: {course_id}): {authors_data}")
            return []
    except Exception as e:
        logging.error(f"Mualliflarni olishda xato (course_id: {course_id}): {e}")
        return []


async def get_author_videos(author_id: int, course_id: int = None) -> List[Dict]:
    try:
        url = f"{BASE_API_URL}authors/{author_id}/videos/"
        if course_id:
            url += f"?course_id={course_id}"

        response = requests.get(url)
        response.raise_for_status()
        videos_data = response.json()

        if isinstance(videos_data, list):
            return videos_data
        elif isinstance(videos_data, dict):
            return videos_data.get('videos', [])
        else:
            logging.error(f"Noto'g'ri javob formati (author_id: {author_id}, course_id: {course_id}): {videos_data}")
            return []
    except Exception as e:
        logging.error(f"Videolarni olishda xato (author_id: {author_id}, course_id: {course_id}): {e}")
        return []


@router.message(F.text == "📚 O'quv kurslar")
async def show_courses(message: Message, state: FSMContext):
    courses = await get_courses_from_api()

    buttons = [[KeyboardButton(text=course['name'])] for course in courses]
    buttons.append([KeyboardButton(text="⬅️ Bosh menyu")])

    await message.answer(
        "O'quv kurslar ro'yxati:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True
        )
    )
    await state.set_state(CourseStates.selecting_course)


def build_keyboard(items: list[str], back_text: str, include_main_menu: bool = False) -> ReplyKeyboardMarkup:
    buttons = [items[i:i + 2] for i in range(0, len(items), 2)]
    buttons = [[KeyboardButton(text=txt) for txt in row] for row in buttons]

    if include_main_menu:
        buttons.append([KeyboardButton(text=back_text), KeyboardButton(text="⬅️ Bosh menyu")])
    else:
        buttons.append([KeyboardButton(text=back_text)])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(CourseStates.selecting_course, F.text == "⬅️ Bosh menyu")
async def back_to_main(message: Message, state: FSMContext):
    await message.answer("Bosh menyuga qaytdingiz")
    await state.clear()
    await send_main_menu(message.bot, message.from_user.id, "uz")


@router.message(CourseStates.selecting_course)
async def select_course(message: Message, state: FSMContext):
    courses = await get_courses_from_api()
    course_names = [c['name'] for c in courses]
    if message.text not in course_names:
        await message.answer(
            "❌ Iltimos, faqat ro'yxatdagi kurslardan birini tanlang:",
            reply_markup=build_keyboard(course_names, "⬅️ Bosh menyu")
        )
        return

    selected_course = next(c for c in courses if c['name'] == message.text)
    authors = await get_course_authors(selected_course['id'])

    if not authors:
        await message.answer("❌ Bu kursda hozircha mualliflar mavjud emas")
        return

    author_names = [a['full_name'] for a in authors]
    await message.answer(
        f"📚 {selected_course['name']} kursi mualliflari:",
        reply_markup=build_keyboard(author_names, "⬅️ Kurslar", include_main_menu=True)
    )
    await state.set_state(CourseStates.selecting_author)
    await state.update_data(course_id=selected_course['id'], course_name=selected_course['name'])


@router.message(CourseStates.selecting_author, F.text == "⬅️ Kurslar")
async def back_to_courses_list(message: Message, state: FSMContext):
    await show_courses(message, state)


@router.message(CourseStates.selecting_author, F.text == "⬅️ Bosh menyu")
async def back_to_main_from_authors(message: Message, state: FSMContext):
    await message.answer("Bosh menyuga qaytdingiz")
    await state.clear()
    await send_main_menu(message.bot, message.from_user.id, "uz")


@router.message(CourseStates.selecting_author)
async def handle_author_selection(message: Message, state: FSMContext):
    data = await state.get_data()
    authors = await get_course_authors(data['course_id'])
    author_names = [a['full_name'] for a in authors]

    if message.text not in author_names:
        await message.answer(
            "❌ Iltimos, faqat ro'yxatdagi mualliflardan birini tanlang:",
            reply_markup=build_keyboard(author_names, "⬅️ Kurslar", include_main_menu=True)
        )
        return

    selected_author = next(a for a in authors if a['full_name'] == message.text)
    videos = await get_author_videos(selected_author['id'], data['course_id'])

    if not videos:
        await message.answer(f"❌ {message.text} muallifida hozircha videolar mavjud emas")
        return

    caption = f"📹 {videos[0]['module_name']}\n\nMuallif: {message.text}"
    sent_message = await message.answer_video(
        video=videos[0]['video_file_id'],
        caption=caption,
        protect_content=True,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⏭️ Keyingi video"), KeyboardButton(text="⬅️ Mualliflar")]],
            resize_keyboard=True
        )
    )
    await state.set_state(CourseStates.watching)
    await state.update_data(
        author_id=selected_author['id'],
        author_name=message.text,
        videos=videos,
        current_index=0,
        video_message_id=sent_message.message_id
    )


@router.message(CourseStates.watching, F.text == "⬅️ Mualliflar")
async def back_to_authors_list(message: Message, state: FSMContext):
    data = await state.get_data()
    authors = await get_course_authors(data['course_id'])
    author_names = [a['full_name'] for a in authors]
    await message.answer(
        f"📚 {data['course_name']} kursi mualliflari:",
        reply_markup=build_keyboard(author_names, "⬅️ Kurslar", include_main_menu=True)
    )
    await state.set_state(CourseStates.selecting_author)


@router.message(CourseStates.watching, F.text == "⏭️ Keyingi video")
async def show_next_video(message: Message, state: FSMContext):
    data = await state.get_data()
    videos = data['videos']
    i = data['current_index'] + 1

    if i >= len(videos):
        await message.answer(f"🎉 {data['author_name']} muallifining barcha videolarini ko'rdingiz!")
        return await back_to_authors_list(message, state)

    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=data['video_message_id'])
        new_msg = await message.answer_video(
            video=videos[i]['video_file_id'],
            caption=f"📹 {videos[i]['module_name']}\n\nMuallif: {data['author_name']}",
            protect_content=True,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⏭️ Keyingi video"), KeyboardButton(text="⬅️ Mualliflar")]],
                resize_keyboard=True
            )
        )
        await state.update_data(current_index=i, video_message_id=new_msg.message_id)
    except Exception as e:
        logging.error(f"Video yangilashda xato: {e}")
        await message.answer("❌ Videoni yangilashda xatolik yuz berdi")
