from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import base64
from datetime import date  # NEW
from db import dbhelper  # import from db package
from datetime import date, datetime


app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # required for flash/session

# Initialize DB (creates tables if they don't exist)
dbhelper.init_db()


@app.route("/")
def index():
    email = session.get("email")  # optional
    return render_template("index.html", email=email)


# ==========================
# AUTH: LOGIN / REGISTER / LOGOUT
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --- LOGIN FORM ---
        if form_type == "login":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            admin = dbhelper.get_admin_by_email(email)

            if admin and admin["password"] == password:
                session["email"] = email
                flash("Login successful!", "success")
                return redirect(url_for("admin"))
            else:
                flash("Invalid email or password.", "error")

        # --- REGISTER FORM ---
        elif form_type == "register":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            if not email or not password:
                flash("Please fill in all required fields.", "error")
            elif password != confirm:
                flash("Passwords do not match.", "error")
            else:
                try:
                    dbhelper.create_admin(email, password)
                    flash("Registration successful. You can now log in.", "success")
                    return redirect(url_for("login"))
                except sqlite3.IntegrityError:
                    flash("Email is already registered.", "error")

    # GET or failed POST → show login page again
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("email", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ==========================
# ADMIN: USER MANAGEMENT
# ==========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # simple protection: must be logged in
    if "email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user_id = request.form.get("user_id")  # hidden field, will be filled when editing

        if not email or not password:
            flash("Email and password are required.", "error")
        else:
            try:
                if user_id:  # EDIT existing user
                    dbhelper.update_admin(int(user_id), email, password)
                    flash("Admin updated.", "success")
                else:        # CREATE new user
                    dbhelper.create_admin(email, password)
                    flash("Admin user created.", "success")

                return redirect(url_for("admin"))
            except sqlite3.IntegrityError:
                flash("That email is already in use.", "error")

    # GET: show list of admins
    users = dbhelper.get_all_admins()
    return render_template("admin.html", users=users)


@app.route("/admin/delete/<int:user_id>")
def delete_user(user_id):
    if "email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    dbhelper.delete_admin(user_id)
    flash("Admin deleted.", "info")
    return redirect(url_for("admin"))


# ==========================
# STUDENT MANAGEMENT
# ==========================
@app.route("/students")
def students():
    """Student management main page (studentmngt.html)."""
    if "email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    all_students = dbhelper.get_all_students()
    return render_template("studentmngt.html", students=all_students)


@app.route("/student", methods=["GET", "POST"])
@app.route("/student/<int:student_id>", methods=["GET", "POST"])
def student_form(student_id=None):
    """
    Add / Edit student.
    - GET without id  -> empty form (ADD)
    - GET with id     -> load existing student (EDIT)
    - POST            -> save to DB (including avatar + qr_value)
    """
    if "email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    student = None
    if student_id is not None:
        student = dbhelper.get_student_by_id(student_id)

    if request.method == "POST":
        sid = request.form.get("student_id", "").strip()
        last_name = request.form.get("last_name", "").strip()
        first_name = request.form.get("first_name", "").strip()
        course = request.form.get("course", "").strip()
        level = request.form.get("level", "").strip()
        photo_data = request.form.get("photo_data", "")  # base64 data URI from hidden input

        if not sid or not last_name or not first_name:
            flash("Student ID, last name, and first name are required.", "error")
            return redirect(request.url)

        # QR value: for now same as ID
        qr_value = sid

        # ------------------------------
        # Handle avatar image saving
        # ------------------------------
        photo_path = None

        # If editing, start with existing photo_path so we don't lose it
        if student is not None:
            existing_path = student["photo_path"]
            if existing_path:
                photo_path = existing_path

        # If a new photo was captured, overwrite / create file
        if photo_data and photo_data.startswith("data:image"):
            try:
                header, encoded = photo_data.split(",", 1)
                image_bytes = base64.b64decode(encoded)

                avatars_dir = os.path.join(app.root_path, "static", "images", "avatars")
                os.makedirs(avatars_dir, exist_ok=True)

                # Use student_id as filename so it is stable
                filename = f"{sid}.jpg"
                file_path = os.path.join(avatars_dir, filename)

                with open(file_path, "wb") as f:
                    f.write(image_bytes)

                # Path to store in DB (relative to /static)
                photo_path = f"images/avatars/{filename}"

            except Exception as e:
                print("Error saving avatar:", e)
                flash("Photo could not be saved, but other data was updated.", "error")

        # ------------------------------
        # Create or update DB record
        # ------------------------------
        try:
            if student_id is not None:
                # UPDATE
                dbhelper.update_student(
                    student_id,
                    sid,
                    last_name,
                    first_name,
                    course,
                    level,
                    photo_path,
                    qr_value
                )
                flash("Student updated.", "success")
            else:
                # CREATE
                dbhelper.create_student(
                    sid,
                    last_name,
                    first_name,
                    course,
                    level,
                    photo_path,
                    qr_value
                )
                flash("Student created.", "success")
        except sqlite3.IntegrityError:
            flash("Student ID or QR value already exists.", "error")
            return redirect(request.url)

        return redirect(url_for("students"))

    # GET: show form
    return render_template("student.html", student=student)


@app.route("/student/delete/<int:student_id>")
def delete_student(student_id):
    """Delete a student record."""
    if "email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    dbhelper.delete_student(student_id)
    flash("Student deleted.", "info")
    return redirect(url_for("students"))


# ==========================
# ATTENDANCE
# ==========================
@app.route("/attendance")
def attendance():
    """Attendance list page (filterable by date)."""
    if "email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    # date from query string (?date=YYYY-MM-DD)
    selected_date = request.args.get("date")
    if not selected_date:
        selected_date = date.today().strftime("%Y-%m-%d")

    # fetch rows for that date from DB
    rows = dbhelper.get_attendance_by_date(selected_date)

    records = []
    for r in rows:
        full_name = f"{r['last_name']}, {r['first_name']}"
        course_level = f"{r['course']} - {r['level']}"
        records.append(
            {
                "id": r["id"],           # attendance record id
                "time_in": r["time_in"],
                "name": full_name,
                "course_level": course_level,
            }
        )

    return render_template(
        "attendance.html",
        selected_date=selected_date,
        records=records
    )
    
    
    # ==========================
# QR SCAN → ATTENDANCE API
# ==========================
@app.route("/scan", methods=["POST"])
def scan_qr():
    """
    Called by JS on the index page when a QR is scanned.
    - expects JSON: { "qr_text": "20240001" }
    - looks up student by student_id
    - records attendance for today (if not yet recorded)
    - returns student info + time_in for the popup card
    """
    data = request.get_json() or {}
    qr_text = (data.get("qr_text") or "").strip()

    if not qr_text:
        return {"status": "error", "message": "Empty QR data."}, 400

    # Look up student using IDNO (student_id)
    student = dbhelper.get_student_by_student_id(qr_text)
    if not student:
        # QR not registered
        return {"status": "not_found", "message": "Student not found for this QR."}, 200

    today_str = date.today().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%I:%M %p")  # e.g. 08:05 AM

    # Check if this student already has attendance for today
    existing = dbhelper.get_attendance_for_student_on_date(student["id"], today_str)

    if existing:
        created = False
        time_in = existing["time_in"]
    else:
        created = True
        time_in = now_str
        dbhelper.record_attendance(student["id"], today_str, time_in)

    # Build photo URL (if any)
    photo_url = None
    if student["photo_path"]:
        photo_url = url_for("static", filename=student["photo_path"])

    return {
        "status": "ok",
        "created": created,      # True if new attendance just recorded
        "time_in": time_in,
        "student": {
            "id": student["id"],
            "student_id": student["student_id"],
            "last_name": student["last_name"],
            "first_name": student["first_name"],
            "course": student["course"],
            "level": student["level"],
            "photo_url": photo_url,
        },
    }



if __name__ == "__main__":
    app.run(debug=True)
