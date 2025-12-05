from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from db import dbhelper  # import from db package

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # required for flash/session

# Initialize DB (creates admins table and default admin)
dbhelper.init_db()


@app.route("/")
def index():
    email = session.get("email")  # optional
    return render_template("index.html", email=email)


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


if __name__ == "__main__":
    app.run(debug=True)
