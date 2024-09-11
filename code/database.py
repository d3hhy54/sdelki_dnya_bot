import aiosqlite as sq
import datetime

def format_date(date_str):
  day, month = map(int, date_str.split('.'))
  return f"{datetime.date.today().year}-{month:02}-{day:02}"
  
class Database:
    def __init__(self, file):
        self.file = file

    async def create_table_users(self) -> None:
        async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                posts INTEGER,
                menu_id INTEGER,
                count INTEGER)""")
            await conn.commit()
           
    async def create_table_posts(self) -> None:
    	async with sq.connect(self.file) as conn:
    		cursor = await conn.cursor()
    		await cursor.execute("""CREATE TABLE IF NOT EXISTS posts(
    		id INTEGER PRIMARY KEY AUTOINCREMENT,
    		user_id INTEGER,
    		file TEXT,
    		type TEXT,
    		description TEXT,
    		date DATE,
    		time TIME,
    		status TEXT)""")
    		await conn.commit()
    		
    async def add_post(self, user_id: int, file: str, type: str, description: str, date: str, time: str, status="check") -> None:
    	async with sq.connect(self.file) as conn:
    		cursor = await conn.cursor()
    		await cursor.execute("""INSERT INTO posts(user_id, file, type, description, date, time, status) VALUES(?, ?, ?, ?, ?, ?, ?)""", (user_id, file, type, description, date, time, status))
    		await conn.commit()
    		
    async def all_posts_sending(self) -> list:
    	async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            msk_timezone = datetime.timezone(datetime.timedelta(hours=3))
            msk_time = datetime.datetime.now().astimezone(msk_timezone)
            date_msk, time_msk = msk_time.strftime("%d.%m"), msk_time.strftime("%H:%M")
            await cursor.execute("""SELECT * FROM posts WHERE status = ? AND date = ? AND time =?""", ("send", date_msk, time_msk))
            return await cursor.fetchall()

    async def all_posts_check(self) -> list:
    	async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""SELECT * FROM posts WHERE status = ?""", ("check", ))
            return await cursor.fetchall()
    		
    async def all_posts_user(self, user_id: int) -> list:
    	async with sq.connect(self.file) as conn:
    		cursor = await conn.cursor()
    		await cursor.execute("""SELECT * FROM posts WHERE user_id = ?""", (user_id, ))
    		return await cursor.fetchall()
    		
    async def change_status_post(self, id: int, status="cancelled") -> None:
    	async with sq.connect(self.file) as conn:
    		cursor = await conn.cursor()
    		await cursor.execute("""UPDATE posts SET status = ? WHERE id = ?""", (status, id))
    		await conn.commit()
    		
    async def change_value_posts_user(self, user_id: int, posts: int) -> None:
    	async with sq.connect(self.file) as conn:
    		cursor = await conn.cursor()
    		await cursor.execute("""UPDATE users SET posts = posts + ? WHERE user_id = ?""", (posts, user_id))
    		await conn.commit()
    		
    async def change_value_count_user(self, user_id: int, count: int) -> None:
    	async with sq.connect(self.file) as conn:
    		cursor = await conn.cursor()
    		await cursor.execute("""UPDATE users SET count = count + ? WHERE user_id = ?""", (count, user_id))
    		await conn.commit()
    		
    async def add_user(self, user_id: int, menu_id: int, posts=0) -> None:
        async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""INSERT INTO users (user_id, posts, menu_id) VALUES (?, ?, ?)""", (user_id, posts, menu_id))
            await conn.commit()
    
    async def have_user(self, user_id: int) -> bool:
        async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,))
            rows = await cursor.fetchall()
            return len(rows) > 0 
    
    async def change_value_menu_id_user(self, user_id: int, menu_id: int) -> None:
        async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""UPDATE users SET menu_id = ? WHERE user_id = ?""", (menu_id, user_id))
            await conn.commit()
    
    async def info_user(self, user_id: int) -> tuple:
        async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,))
            answer = await cursor.fetchone()
            return answer

    async def id_all_users(self) -> tuple:
        async with sq.connect(self.file) as conn:
            cursor = await conn.cursor()
            await cursor.execute("""SELECT user_id FROM users""")
            answer = await cursor.fetchall()
            for id in answer:
                yield id[0]