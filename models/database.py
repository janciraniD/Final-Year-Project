"""models/database.py – SQLite Database Manager"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'healthcare.db'


class DatabaseManager:

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                tx_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS emrs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                patient_name TEXT,
                ipfs_hash TEXT,
                tx_hash TEXT,
                file_hash TEXT,
                encryption_key TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tx_hash TEXT,
                tx_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        conn.close()
        print("[DB] Database initialized.")

    def _conn(self):
        return sqlite3.connect(DB_PATH)

    def save_user_tx(self, username: str, tx_hash: str):
        conn = self._conn()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username, tx_hash) VALUES (?,?)",
                  (username, tx_hash))
        conn.commit(); conn.close()

    def save_emr(self, user_id, patient_name, ipfs_hash,
                 tx_hash, file_hash, encryption_key):
        conn = self._conn()
        c = conn.cursor()
        c.execute('''INSERT INTO emrs
                     (user_id, patient_name, ipfs_hash, tx_hash, file_hash, encryption_key)
                     VALUES (?,?,?,?,?,?)''',
                  (user_id, patient_name, ipfs_hash, tx_hash, file_hash, encryption_key))
        conn.commit(); conn.close()

    def get_user_emrs(self, user_id: int) -> list:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM emrs WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        cols = ['id','user_id','patient_name','ipfs_hash','tx_hash',
                'file_hash','encryption_key','created_at']
        return [dict(zip(cols, r)) for r in rows]

    def get_all_emrs(self) -> list:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM emrs ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        cols = ['id','user_id','patient_name','ipfs_hash','tx_hash',
                'file_hash','encryption_key','created_at']
        return [dict(zip(cols, r)) for r in rows]

    def get_emr_by_id(self, emr_id: int) -> dict:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM emrs WHERE id=?", (emr_id,))
        row = c.fetchone()
        conn.close()
        if row:
            cols = ['id','user_id','patient_name','ipfs_hash','tx_hash',
                    'file_hash','encryption_key','created_at']
            return dict(zip(cols, row))
        return None

    def get_all_transactions(self) -> list:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        cols = ['id','user_id','tx_hash','tx_type','created_at']
        return [dict(zip(cols, r)) for r in rows]
