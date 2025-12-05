# db/dbhelper.py

import sqlite3
import os

# Get absolute path to this folder (db/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database file path (db/school.db)
DB_NAME = os.path.join(BASE_DIR, "school.db")


def get_db():
    """
    Opens a new SQLite database connection.
    row_factory allows fetching rows like dictionaries.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the admins table if it does not exist.
    Also inserts a default admin account (if not already created).
    """
    conn = get_db()

    # Create admins table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # Insert default admin safely
    conn.execute("""
        INSERT OR IGNORE INTO admins (email, password)
        VALUES (?, ?);
    """, ("admin@gmail.com", "1234"))

    conn.commit()
    conn.close()


# ================================
# ADMIN CRUD OPERATIONS
# ================================

def get_admin_by_email(email: str):
    """
    Returns one admin row by email or None.
    """
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM admins WHERE email = ?",
        (email,)
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_admin(email: str, password: str):
    """
    Inserts a new admin and returns the new admin ID.
    """
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO admins (email, password) VALUES (?, ?)",
        (email, password)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_admins():
    """
    Returns all admins sorted by ID.
    """
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM admins ORDER BY id ASC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_admin(admin_id: int, email: str, password: str):
    """
    Updates an admin's email and password.
    """
    conn = get_db()
    conn.execute(
        "UPDATE admins SET email = ?, password = ? WHERE id = ?",
        (email, password, admin_id)
    )
    conn.commit()
    conn.close()


def delete_admin(admin_id: int):
    """
    Deletes an admin by ID.
    """
    conn = get_db()
    conn.execute(
        "DELETE FROM admins WHERE id = ?",
        (admin_id,)
    )
    conn.commit()
    conn.close()
