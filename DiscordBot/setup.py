import sqlite3
import os

DATABASE_FILE = 'discord_bot.db'

if os.path.exists(DATABASE_FILE):
    os.remove(DATABASE_FILE)
    
con = sqlite3.connect(DATABASE_FILE)
cursor = con.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_logs (
        user_id TEXT NOT NULL,
        timestamp REAL NOT NULL DEFAULT current_timestamp
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_messages (
        user_id TEXT NOT NULL,
        message_date REAL NOT NULL,
        message_text TEXT NOT NULL,
        is_complete INTEGER NOT NULL
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        user_id TEXT NOT NULL,
        saved_timestamp REAL NOT NULL DEFAULT current_timestamp,
        resource_url TEXT NOT NULL
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT,
        username TEXT
    );
""")