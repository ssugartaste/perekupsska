import sqlite3
from typing import List

class Database:
    def __init__(self, db_file="bot_database.sqlite"):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            active INTEGER DEFAULT 1
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            UNIQUE(user_id, url),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ad_id TEXT,
            UNIQUE(user_id, ad_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)
        conn.commit()
        conn.close()

    def add_user(self, user_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users(user_id, active) VALUES (?, 1)", (user_id,))
        cursor.execute("UPDATE users SET active=1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

    def deactivate_user(self, user_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET active=0 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

    def get_active_users(self) -> List[int]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE active=1")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def add_url_for_user(self, user_id: int, url: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO user_urls(user_id, url) VALUES (?, ?)", (user_id, url))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_urls_for_user(self, user_id: int) -> List[str]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM user_urls WHERE user_id=?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def get_unique_urls_of_active_users(self) -> List[str]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT url FROM user_urls
            WHERE user_id IN (SELECT user_id FROM users WHERE active=1)
        """)
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def get_active_users_by_url(self, url: str) -> List[int]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id FROM user_urls
            WHERE url=? AND user_id IN (SELECT user_id FROM users WHERE active=1)
        """, (url,))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def is_ad_seen(self, user_id: int, ad_id: str) -> bool:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM seen_ads WHERE user_id=? AND ad_id=?", (user_id, ad_id))
        res = cursor.fetchone()
        conn.close()
        return res is not None

    def mark_ad_as_seen(self, user_id: int, ad_id: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO seen_ads(user_id, ad_id) VALUES (?, ?)", (user_id, ad_id))
        conn.commit()
        conn.close()
