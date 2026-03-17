from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "budget_secret"


# Disable browser cache
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- LOGIN PAGE ----------------
@app.route("/")
def login():
    return render_template("login.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login_user():

    username = request.form["username"]
    password = request.form["password"]

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()

    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect("/dashboard")

    return "Invalid username or password"


# ---------------- REGISTER PAGE ----------------
@app.route("/register")
def register():
    return render_template("register.html")


# ---------------- REGISTER USER ----------------
@app.route("/register_user", methods=["POST"])
def register_user():

    username = request.form["username"]
    password = request.form["password"]

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if user:
        return "Username already exists"

    db.execute(
        "INSERT INTO users(username,password) VALUES (?,?)",
        (username, password)
    )

    db.commit()

    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user_id = session["user_id"]

    income = db.execute(
        "SELECT SUM(amount) as total FROM income WHERE user_id=?",
        (user_id,)
    ).fetchone()["total"] or 0

    expense = db.execute(
        "SELECT SUM(amount) as total FROM expenses WHERE user_id=?",
        (user_id,)
    ).fetchone()["total"] or 0

    balance = income - expense

    categories = db.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id=?
        GROUP BY category
    """, (user_id,)).fetchall()

    category_labels = [row["category"] for row in categories]
    category_values = [row["total"] for row in categories]

    return render_template(
        "dashboard.html",
        income=income,
        expense=expense,
        balance=balance,
        category_labels=category_labels,
        category_values=category_values
    )


# ---------------- ADD INCOME ----------------
@app.route("/add_income", methods=["GET", "POST"])
def add_income():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":

        date = request.form["date"]
        source = request.form["source"]
        amount = request.form["amount"]

        db.execute(
            "INSERT INTO income(user_id,date,source,amount) VALUES (?,?,?,?)",
            (user_id, date, source, amount)
        )

        db.commit()

        return redirect("/add_income")

    income = db.execute(
        "SELECT * FROM income WHERE user_id=?",
        (user_id,)
    ).fetchall()

    return render_template("add_income.html", income=income)


# ---------------- DELETE INCOME ----------------
@app.route("/delete_income/<int:id>")
def delete_income(id):

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user_id = session["user_id"]

    db.execute(
        "DELETE FROM income WHERE id=? AND user_id=?",
        (id, user_id)
    )

    db.commit()

    return redirect("/add_income")

# ---------------- ADD EXPENSE ----------------
@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":

        date = request.form["date"]
        category = request.form["category"]
        amount = request.form["amount"]

        db.execute(
            "INSERT INTO expenses(user_id,date,category,amount) VALUES (?,?,?,?)",
            (user_id, date, category, amount)
        )

        db.commit()

        return redirect("/add_expense")

    expenses = db.execute(
        "SELECT * FROM expenses WHERE user_id=?",
        (user_id,)
    ).fetchall()

    return render_template("add_expense.html", expenses=expenses)


# ---------------- DELETE EXPENSE ----------------
@app.route("/delete_expense/<int:id>")
def delete_expense(id):

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user_id = session["user_id"]

    db.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id, user_id)
    )

    db.commit()

    return redirect("/add_expense")


# ---------------- REPORT ----------------
@app.route("/report")
def report():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    user_id = session["user_id"]

    filter_type = request.args.get("filter", "monthly")

    if filter_type == "daily":

        income = db.execute("""
        SELECT SUM(amount) FROM income
        WHERE user_id=? AND date=date('now')
        """,(user_id,)).fetchone()[0] or 0

        expense = db.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE user_id=? AND date=date('now')
        """,(user_id,)).fetchone()[0] or 0

    elif filter_type == "weekly":

        income = db.execute("""
        SELECT SUM(amount) FROM income
        WHERE user_id=? AND date >= date('now','-7 day')
        """,(user_id,)).fetchone()[0] or 0

        expense = db.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE user_id=? AND date >= date('now','-7 day')
        """,(user_id,)).fetchone()[0] or 0

    else:

        income = db.execute("""
        SELECT SUM(amount) FROM income
        WHERE user_id=? AND strftime('%m',date)=strftime('%m','now')
        """,(user_id,)).fetchone()[0] or 0

        expense = db.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE user_id=? AND strftime('%m',date)=strftime('%m','now')
        """,(user_id,)).fetchone()[0] or 0

    return render_template(
        "report.html",
        income=income,
        expense=expense,
        filter_type=filter_type
    )
  
  #--------------excel---------------
    
@app.route("/export_excel")
def export_excel():

    if "user_id" not in session:
        return redirect("/")

    import pandas as pd
    from flask import send_file

    db = get_db()
    user_id = session["user_id"]

    income_data = db.execute(
        "SELECT date, source, amount FROM income WHERE user_id=?",
        (user_id,)
    ).fetchall()

    expense_data = db.execute(
        "SELECT date, category, amount FROM expenses WHERE user_id=?",
        (user_id,)
    ).fetchall()

    income_df = pd.DataFrame(income_data, columns=["Date", "Source", "Amount"])
    expense_df = pd.DataFrame(expense_data, columns=["Date", "Category", "Amount"])

    file_name = "budget_report.xlsx"

    with pd.ExcelWriter(file_name) as writer:
        income_df.to_excel(writer, sheet_name="Income", index=False)
        expense_df.to_excel(writer, sheet_name="Expenses", index=False)

    return send_file(file_name, as_attachment=True)

#-----------------------pdf----------------------

@app.route("/export_pdf")
def export_pdf():

    if "user_id" not in session:
        return redirect("/")

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from flask import send_file

    db = get_db()
    user_id = session["user_id"]

    income = db.execute(
        "SELECT SUM(amount) FROM income WHERE user_id=?",
        (user_id,)
    ).fetchone()[0] or 0

    expense = db.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (user_id,)
    ).fetchone()[0] or 0

    file_name = "budget_report.pdf"

    c = canvas.Canvas(file_name, pagesize=letter)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, 750, "Budget Report")

    c.setFont("Helvetica", 14)
    c.drawString(100, 650, f"Total Income : ₹ {income}")
    c.drawString(100, 620, f"Total Expense : ₹ {expense}")
    c.drawString(100, 590, f"Balance : ₹ {income-expense}")

    c.save()

    return send_file(file_name, as_attachment=True)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- DATABASE SETUP ----------------
if __name__ == "__main__":

    db = get_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS income(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        source TEXT,
        amount REAL
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        category TEXT,
        amount REAL
    )
    """)

    db.commit()

    app.run(debug=True)