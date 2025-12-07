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
    Creates the admins, students, and attendance tables if they do not exist.
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

    # =====================
    # ATTENDANCE TABLE
    # =====================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,   -- FK -> students.id
            date TEXT NOT NULL,            -- 'YYYY-MM-DD'
            time_in TEXT NOT NULL,         -- e.g. '08:05 AM'
            FOREIGN KEY (student_id) REFERENCES students(id)
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


def get_admin_by_id(admin_id: int):
    """
    Return a single admin row by numeric id, or None if it doesn't exist.
    """
    conn = get_db()
    cur = conn.execute("SELECT * FROM admins WHERE id = ?", (admin_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_admin(email: str, password: str):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO admins (email, password) VALUES (?, ?)",
            (email, password)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_all_admins():
    conn = get_db()
    cur = conn.execute("SELECT * FROM admins ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def update_admin(admin_id: int, email: str, password: str):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE admins SET email = ?, password = ? WHERE id = ?",
            (email, password, admin_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_admin(admin_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
        conn.commit()
    finally:
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


def get_student_by_student_id(student_id_str: str):
    """
    Returns student row by their public IDNO (student_id column).
    Useful when your QR scan gives you the IDNO string.
    """
    conn = get_db()
    cur = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id_str,))
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
    try:
        cur = conn.execute("""
            INSERT INTO students
                (student_id, last_name, first_name, course, level, photo_path, qr_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, last_name, first_name, course, level, photo_path, qr_value))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


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
    try:
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
    finally:
        conn.close()


def delete_student(row_id: int):
    """
    Deletes a student by numeric 'id'.
    """
    conn = get_db()
    try:
        conn.execute("DELETE FROM students WHERE id = ?", (row_id,))
        conn.commit()
    finally:
        conn.close()


# ================================
# ATTENDANCE OPERATIONS
# ================================

def record_attendance(student_row_id: int, date_str: str, time_in_str: str):
    """
    Inserts a new attendance row.
    Called when a QR is successfully scanned.
    """
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO attendance (student_id, date, time_in)
            VALUES (?, ?, ?)
        """, (student_row_id, date_str, time_in_str))
        conn.commit()
    finally:
        conn.close()


def get_attendance_by_date(date_str: str):
    """
    Returns attendance + joined student data for a given date.
    Now sorted by time_in (earliest first).
    """
    conn = get_db()
    cur = conn.execute("""
        SELECT
            a.id,
            a.time_in,
            s.student_id,
            s.first_name,
            s.last_name,
            s.course,
            s.level
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time_in ASC, a.id ASC
    """, (date_str,))
    rows = cur.fetchall()
    conn.close()
    return rows



def get_attendance_for_student_on_date(student_row_id: int, date_str: str):
    """
    Returns a single attendance row for a given student + date
    (or None if no attendance yet).
    Used to avoid duplicate attendance for the same day.
    """
    conn = get_db()
    cur = conn.execute("""
        SELECT * FROM attendance
        WHERE student_id = ? AND date = ?
        LIMIT 1
    """, (student_row_id, date_str))
    row = cur.fetchone()
    conn.close()
    return row
