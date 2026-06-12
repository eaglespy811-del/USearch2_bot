import sqlite3
from datetime import datetime, timedelta
from config import FREE_LIMIT, PREMIUM_LIMIT

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("users.db", check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                premium_until TEXT,
                premium_type TEXT,
                searches_today INTEGER DEFAULT 0,
                last_date TEXT,
                total_searches INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def register(self, user_id, username):
        self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        self.conn.commit()
    
    def is_premium(self, user_id):
        cur = self.conn.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row[0]:
            return datetime.fromisoformat(row[0]) > datetime.now()
        return False
    
    def activate_premium(self, user_id, days, premium_type):
        until = (datetime.now() + timedelta(days=days)).isoformat()
        self.conn.execute(
            "UPDATE users SET premium_until = ?, premium_type = ? WHERE user_id = ?",
            (until, premium_type, user_id)
        )
        self.conn.commit()
    
    def get_user(self, user_id):
        cur = self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()
    
    def can_search(self, user_id):
        today = datetime.now().date().isoformat()
        cur = self.conn.execute("SELECT searches_today, last_date FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        limit = PREMIUM_LIMIT if self.is_premium(user_id) else FREE_LIMIT
        
        if row and row[1] == today:
            return row[0] < limit, limit - row[0]
        return True, limit
    
    def use_search(self, user_id):
        today = datetime.now().date().isoformat()
        cur = self.conn.execute("SELECT searches_today, last_date FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        searches = (row[0] if row and row[1] == today else 0) + 1
        self.conn.execute("""
            UPDATE users 
            SET searches_today = ?, last_date = ?, total_searches = total_searches + 1
            WHERE user_id = ?
        """, (searches, today, user_id))
        self.conn.commit()

db = Database()