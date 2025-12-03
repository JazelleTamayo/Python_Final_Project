from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # required for flash/session

# Temporary in-memory user storage (for demo)
# In a real project, use a database.
users = {}  # { "username": "password" }

@app.route("/")
def index():
    username = session.get("username")  # optional, if you want to greet them
    return render_template("index.html", username=username)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --- LOGIN FORM ---
        if form_type == "login":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if username in users and users[username] == password:
                session["username"] = username
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid username or password.", "error")

        # --- REGISTER FORM ---
        elif form_type == "register":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            if not username or not password:
                flash("Please fill in all required fields.", "error")
            elif password != confirm:
                flash("Passwords do not match.", "error")
            elif username in users:
                flash("Username already taken.", "error")
            else:
                users[username] = password
                flash("Registration successful. You can now log in.", "success")
                return redirect(url_for("login"))

    # GET or failed POST → show login page again
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
