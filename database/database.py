import dbm
import os
import aiosqlite
import asyncio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR,'bot.db')

async def init_db():
    """Инициализируем базу данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:

        #Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            ''')

        #Таблица истории сообщений
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL, -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')

        await db.commit()


#Функция для добавления пользователей в БД

async def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):

    async with aiosqlite.connect(DATABASE_PATH) as db:

        await db.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?,?,?,?)
        ''', (user_id, username, first_name, last_name))
        await db.commit()


#Функция для возвращения информации о пользователе из БД

async def get_user(user_id: int):

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


#Фукнция сохранения сообщения от пользователя или ассистента

async def save_message(user_id: int, role: str, content: str):

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
        INSERT INTO  messages (user_id, role, content)
        VALUES (?,?,?)
        ''', (user_id, role, content))

        await db.commit()



#Функция возвращения последних сообщений

async def get_message(user_id: int, limit: int = 10):

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute('''
        SELECT role, content FROM messages
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (user_id, limit)) as cursor:
            rows = await cursor.fetchall()

        return [dict(row) for row  in reversed(rows)]




