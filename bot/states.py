from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_course_search = State()
    waiting_for_job_type = State()
    waiting_for_job_details = State()
    waiting_for_freelancer_category = State()
    waiting_for_freelancer_details = State()
    waiting_for_startup_type = State()
    waiting_for_startup_details = State()
    waiting_for_content_type = State()
    waiting_for_content_details = State()
    waiting_for_question = State()
    waiting_for_admin_reply = State()