import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloudstorage.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        aws_access_key TEXT,
        aws_secret_key TEXT,
        aws_region TEXT DEFAULT 'us-east-1',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # Seed default demo account if it doesn't exist
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@cloudstorage.com",))
    if not cursor.fetchone():
        hashed = generate_password_hash("demo1234")
        cursor.execute("""
            INSERT INTO users (email, full_name, password_hash, aws_region)
            VALUES (?, ?, ?, ?)
        """, ("demo@cloudstorage.com", "Demo Cloud Architect", hashed, "us-east-1"))
        conn.commit()

    conn.close()

def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(email, full_name, password):
    email = email.strip().lower()
    full_name = full_name.strip()
    password_hash = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (email, full_name, password_hash)
            VALUES (?, ?, ?)
        """, (email, full_name, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return get_user_by_id(user_id), None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "An account with this email already exists."
    except Exception as e:
        conn.close()
        return None, str(e)

def update_user_aws_creds(user_id, access_key, secret_key, region):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET aws_access_key = ?, aws_secret_key = ?, aws_region = ?
        WHERE id = ?
    """, (access_key, secret_key, region, user_id))
    conn.commit()
    conn.close()

def check_user_password(user, password):
    if not user or not user.get("password_hash"):
        return False
    return check_password_hash(user["password_hash"], password)
