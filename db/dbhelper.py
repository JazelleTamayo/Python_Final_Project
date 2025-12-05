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
    Creates the admins and students tables if they do not exist.
    Also inserts a default admin account (if not already created).
    """
    conn = get_db()

    # =====================
    # ADMIN TABLE
    # =====================
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

    # =====================
    # STUDENTS TABLE
    # (matches your PRAGMA/screenshot)
    # =====================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            course TEXT,
            level TEXT,
            photo_path TEXT,
            qr_value TEXT UNIQUE NOT NULL
        );
    """)

    conn.commit()
    conn.close()


# ================================
# ADMIN CRUD OPERATIONS
# ================================

def get_admin_by_email(email: str):
    conn = get_db()
    cur = conn.execute("SELECT * FROM admins WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row


def create_admin(email: str, password: str):
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
    conn = get_db()
    cur = conn.execute("SELECT * FROM admins ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def update_admin(admin_id: int, email: str, password: str):
    conn = get_db()
    conn.execute(
        "UPDATE admins SET email = ?, password = ? WHERE id = ?",
        (email, password, admin_id)
    )
    conn.commit()
    conn.close()


def delete_admin(admin_id: int):
    conn = get_db()
    conn.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
    conn.commit()
    conn.close()


# ================================
# STUDENT CRUD OPERATIONS
# ================================

def get_all_students():
    """
    Returns all students sorted by last name and first name.
    """
    conn = get_db()
    cur = conn.execute("""
        SELECT * FROM students
        ORDER BY last_name, first_name
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_student_by_id(student_id: int):
    """
    Returns a single student record by internal numeric ID.
    """
    conn = get_db()
    cur = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_student(student_id: str,
                   last_name: str,
                   first_name: str,
                   course: str,
                   level: str,
                   photo_path: str,
                   qr_value: str):
    """
    Inserts a new student row and returns the new ID.
    """
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO students
            (student_id, last_name, first_name, course, level, photo_path, qr_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_id, last_name, first_name, course, level, photo_path, qr_value))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_student(row_id: int,
                   student_id: str,
                   last_name: str,
                   first_name: str,
                   course: str,
                   level: str,
                   photo_path: str,
                   qr_value: str):
    """
    Updates an existing student row by numeric 'id'.
    """
    conn = get_db()
    conn.execute("""
        UPDATE students
        SET student_id = ?,
            last_name  = ?,
            first_name = ?,
            course     = ?,
            level      = ?,
            photo_path = ?,
            qr_value   = ?
        WHERE id = ?
    """, (student_id, last_name, first_name, course, level, photo_path, qr_value, row_id))
    conn.commit()
    conn.close()


def delete_student(row_id: int):
    """
    Deletes a student by numeric 'id'.
    """
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()
