import asyncpg
import logging
import asyncio
from typing import Optional
import os
import aiohttp

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pool = None  # Pool bo‘yicha bitta instansiya
            cls._instance._is_connected = False
        return cls._instance

    async def connect(self, user, password, db, host, port):
        """PostgreSQL bilan ulanishni o‘rnatish"""
        self._pool = await asyncpg.create_pool(
            user=user,
            password=password,
            database=db,
            host=host,
            port=port
        )

    async def is_connected(self) -> bool:
        """Bazaga ulanishni tekshirish"""
        if self._pool is None:
            return False
        try:
            async with self._pool.acquire() as connection:
                await connection.fetch("SELECT 1")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    async def fetch(self, query, *args):
        """SQL so'rovini bajarish va ma'lumot olish"""
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def execute(self, query, *args):
        """SQL so'rovini bajarish (ma'lumot o'zgartirish)"""
        async with self._pool.acquire() as connection:
            return await connection.execute(query, *args)


    async def add_user(self, user_id: int, full_name: str, username: Optional[str] = None):
        """Add or update user in database"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, full_name, username)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    username = EXCLUDED.username
            """, user_id, full_name, username)

    async def get_resources(self) -> list:
        """Get all resources from database"""
        async with self._pool.acquire() as conn:  # Changed from pool to _pool
            return await conn.fetch("SELECT * FROM resources")

    async def search_courses(self, search_query: str) -> list:
        """Search courses with better matching"""
        async with self._pool.acquire() as conn:
            query = """
                SELECT id, name as title, lesson_count 
                FROM courses_course 
                WHERE name ILIKE '%' || $1 || '%'
                ORDER BY name
                LIMIT 10
            """
            results = await conn.fetch(query, search_query)
            return [dict(row) for row in results]

    async def get_course_by_name(self, name: str) -> Optional[dict]:
        """Get course by name from your courses_course table"""
        async with self._pool.acquire() as conn:
            result = await conn.fetchrow(
                """SELECT id, name, description, lesson_count 
                   FROM courses_course 
                   WHERE name ILIKE $1 LIMIT 1""",
                f"%{name}%"
            )
            return dict(result) if result else None

    # async def get_active_jobs(self) -> list:
    #     """Get active job postings"""
    #     async with self._pool.acquire() as conn:
    #         results = await conn.fetch(
    #             "SELECT * FROM jobs_job WHERE is_active = TRUE ORDER BY created_at DESC"
    #         )
    #         return [dict(row) for row in results]
    #
    # async def get_freelance_projects(self) -> list:
    #     """Get freelance projects"""
    #     async with self._pool.acquire() as conn:
    #         results = await conn.fetch(
    #             "SELECT * FROM freelance_project WHERE is_active = TRUE ORDER BY created_at DESC"
    #         )
    #         return [dict(row) for row in results]

    async def get_course_videos(self, course_id: int) -> list:
        """Kurs videolarini olish"""
        async with self._pool.acquire() as conn:
            query = """
                SELECT id, module_name, video_file_id 
                FROM course_video 
                WHERE course_id = $1
                ORDER BY uploaded_at
            """
            results = await conn.fetch(query, course_id)
            logging.info(f"Found {len(results)} videos for course {course_id}")  # Debug uchun
            return [dict(row) for row in results]

    async def get_course_videos_count(self, course_id: int) -> int:
        """Kursdagi videolar sonini olish"""
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM course_video WHERE course_id = $1", course_id)

    async def get_user_progress(self, user_id: int, course_id: int) -> int:
        """Foydalanuvchi progressini olish"""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT progress FROM user_course_progress WHERE user_id = $1 AND course_id = $2",
                user_id, course_id
            ) or 0

    async def update_user_progress(self, user_id: int, course_id: int, progress: int):
        """Progressni yangilash"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_course_progress (user_id, course_id, progress)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, course_id) DO UPDATE SET
                    progress = EXCLUDED.progress,
                    updated_at = NOW()
            """, user_id, course_id, progress)

    async def get_video_by_index(self, course_id: int, index: int) -> dict:
        """Kursdagi indeks bo'yicha videoni olish"""
        async with self._pool.acquire() as conn:
            query = """
                SELECT id, module_name, video_file_id 
                FROM course_video 
                WHERE course_id = $1
                ORDER BY uploaded_at
                LIMIT 1 OFFSET $2
            """
            result = await conn.fetchrow(query, course_id, index)
            if not result:
                raise ValueError(f"Video topilmadi (course_id={course_id}, index={index})")
            return dict(result)

    async def update_user_language(self, user_id: int, language: str):
        """Update user's language preference"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, language)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET
                    language = EXCLUDED.language,
                    updated_at = NOW()
            """, user_id, language)

    async def update_user_phone(self, user_id: int, phone_number: str):
        """Update user's phone number"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, phone_number)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET
                    phone_number = EXCLUDED.phone_number,
                    updated_at = NOW()
            """, user_id, phone_number)

    async def get_user_info(self, user_id: int) -> dict:
        async with self._pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT user_id, full_name, username, phone_number,subscription_start, subscription_end, approved, language, is_active
                FROM users
                WHERE user_id = $1
            """, user_id)
            return dict(record) if record else None

    async def get_total_users(self) -> int:
        """Get total number of users"""
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")

    async def activate_user(self, user_id: int):
        async with self._pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET approved = TRUE,
                is_active = TRUE,
                activated_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $1
            """, user_id)


    async def get_new_users_today(self) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE updated_at::date = CURRENT_DATE
            """)

    async def get_active_jobs(self, lang: str = 'uz') -> list:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"http://127.0.0.1:8000/api/v1/jobs/",
                        timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception as e:
            logging.error(f"Error fetching jobs: {e}")
            return []


    async def get_freelance_projects(self, lang: str = 'uz') -> list:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"http://127.0.0.1:8000/api/v1/freelance/",
                        timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception as e:
            logging.error(f"Error fetching freelance projects: {e}")
            return []



    async def get_institute_name_by_id(self, institute_id: str, lang: str = 'uz'):
        try:
            url = f"http://127.0.0.1:8000/api/v1/institute/{institute_id}/"
            logging.info(f"Requesting institute data from: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_text = await response.text()
                    logging.info(f"API response: {response_text}")

                    if response.status == 200:
                        data = await response.json()
                        logging.info(f"Parsed data: {data}")

                        # JSON strukturasini tekshirish
                        if isinstance(data, dict) and data.get('name'):
                            return data['name']
                        elif isinstance(data, str):
                            # Agar response oddiy string bo'lsa
                            return data
                        else:
                            logging.error(f"Unexpected response format: {data}")
                            return None

                    logging.error(f"API request failed with status {response.status}")
                    return None

        except aiohttp.ClientError as e:
            logging.error(f"Network error: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        return None

    async def get_stats(self) -> dict:
        async with self._pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            today = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= CURRENT_DATE
            """)
            month = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= (CURRENT_DATE - INTERVAL '30 days')
            """)
            return {
                "total": total or 0,
                "today": today or 0,
                "month": month or 0
            }


    async def get_top_user(self) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT username, progress
                FROM users
                WHERE username IS NOT NULL
                ORDER BY progress DESC
                LIMIT 1
            """)
            return {
                "username": result["username"],
                "progress": result["progress"]
            } if result else None


    async def update_user_subscription(
            self,
            user_id: int,
            is_active: bool = None,
            subscription_start: str = None,
            subscription_end: str = None
    ):
        """Obuna ma'lumotlarini yangilash"""
        updates = []
        params = []

        if is_active is not None:
            updates.append("is_active = $%d" % (len(params) + 1))
            params.append(is_active)

        if subscription_start is not None:
            updates.append("subscription_start = $%d" % (len(params) + 1))
            params.append(subscription_start)

        if subscription_end is not None:
            updates.append("subscription_end = $%d" % (len(params) + 1))
            params.append(subscription_end)

        if not updates:
            return False

        query = "UPDATE users SET " + ", ".join(updates) + ", updated_at = NOW() WHERE user_id = $%d" % (
                    len(params) + 1)
        params.append(user_id)

        async with self._pool.acquire() as conn:
            try:
                await conn.execute(query, *params)
                return True
            except Exception as e:
                logging.error(f"Obunani yangilashda xato (user_id={user_id}): {str(e)}")
                return False


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1@localhost:5432/it_ai_company")
db = Database()