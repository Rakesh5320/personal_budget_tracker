from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import io

app = Flask(__name__)
app.secret_key = "budget_secret"


# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CACHE FIX ----------------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# ---------------- LOGIN ----------------
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():
    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (request.form["username"], request.form["password"])
    ).fetchone()

    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect("/dashboard")

    return "Invalid username or password"


# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():
    db = get_db()

    try:
        db.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (request.form["username"], request.form["password"])
        )
        db.commit()
    except:
        return "Username already exists"

    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

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

    balance = income - expense

    categories = db.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id=?
        GROUP BY category
    """, (user_id,)).fetchall()

    category_labels = [row["category"] for row in categories]
    category_values = [row["total"] for row in categories]

    return render_template("dashboard.html",
                           income=income,
                           expense=expense,
                           balance=balance,
                           category_labels=category_labels,
                           category_values=category_values)


# ---------------- ADD INCOME ----------------
@app.route("/add_income", methods=["GET", "POST"])
def add_income():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        db.execute(
            "INSERT INTO income(user_id,date,source,amount,description) VALUES (?,?,?,?,?)",
            (session["user_id"],
             request.form["date"],
             request.form["source"],
             request.form["amount"],
             request.form["description"])
            
        )
        db.commit()
        return redirect("/add_income")

    data = db.execute(
        "SELECT * FROM income WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    return render_template("add_income.html", income=data)


# 🔥 DELETE INCOME (ADDED FIX)
@app.route("/delete_income/<int:id>")
def delete_income(id):

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    db.execute("DELETE FROM income WHERE id=? AND user_id=?",
               (id, session["user_id"]))
    db.commit()

    return redirect("/add_income")


# ---------------- ADD EXPENSE ----------------
@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        db.execute(
            "INSERT INTO expenses(user_id,date,category,amount,description) VALUES (?,?,?,?,?)",
            (session["user_id"],
             request.form["date"],
             request.form["category"],
             request.form["amount"],
             request.form["description"])
        )
        db.commit()
        return redirect("/add_expense")

    data = db.execute(
        "SELECT * FROM expenses WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    return render_template("add_expense.html", expenses=data)


# 🔥 DELETE EXPENSE (ADDED FIX)
@app.route("/delete_expense/<int:id>")
def delete_expense(id):

    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    db.execute("DELETE FROM expenses WHERE id=? AND user_id=?",
               (id, session["user_id"]))
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
        condition = "date = date('now')"
    elif filter_type == "weekly":
        condition = "date >= date('now','-7 day')"
    elif filter_type == "yearly":  
        condition = "strftime('%Y', date)=strftime('%Y','now')"
    else:
        condition = "strftime('%Y-%m', date)=strftime('%Y-%m','now')"

    data = db.execute(f"""
        SELECT date, 'Expense' as type, category, amount, description
        FROM expenses WHERE user_id=? AND {condition}

        UNION ALL

        SELECT date, 'Income', source, amount, description 
        FROM income WHERE user_id=? AND {condition}

        ORDER BY date DESC
    """, (user_id, user_id)).fetchall()

    income = sum(row["amount"] for row in data if row["type"] == "Income")
    expense = sum(row["amount"] for row in data if row["type"] == "Expense")

    chart_labels = ["Income", "Expense"]
    chart_values = [income, expense]

    return render_template("report.html",
                           data=data,
                           filter_type=filter_type,
                           income=income,
                           expense=expense,
                           chart_labels=chart_labels,
                           chart_values=chart_values)
    
#----------------pdf----------------
@app.route("/export_pdf/<filter_type>")
def export_pdf(filter_type):

    if "user_id" not in session:
        return redirect("/")

    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet

    db = get_db()
    user_id = session["user_id"]
    username = session["username"]

    # FILTER
    if filter_type == "daily":
        condition = "date = date('now')"
    elif filter_type == "weekly":
        condition = "date >= date('now','-7 day')"
    elif filter_type == "yearly":
        condition = "strftime('%Y', date)=strftime('%Y','now')"
    else:
        condition = "strftime('%Y-%m', date)=strftime('%Y-%m','now')"

    
    data = db.execute(f"""
        SELECT date, 'Expense' as type, category, amount, description
        FROM expenses WHERE user_id=? AND {condition}

        UNION ALL

        SELECT date, 'Income' as type, source as category, amount, description
        FROM income WHERE user_id=? AND {condition}

        ORDER BY date DESC
    """, (user_id, user_id)).fetchall()

    # PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Personal Budget Tracker Report", styles['Title']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"User: {username}", styles['Normal']))
    elements.append(Paragraph(f"Report Type: {filter_type}", styles['Normal']))
    elements.append(Spacer(1, 20))

    table_data = [["Date", "Type", "Category", "Amount", "Description"]]

    for row in data:
        table_data.append([
            str(row["date"]),
            row["type"],
            row["category"],
            str(row["amount"]),
            row["description"]
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name=f"{filter_type}_report.pdf",
                     mimetype='application/pdf')


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
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
        amount REAL,
        description TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        category TEXT,
        amount REAL,
        description TEXT
    )
    """)

    db.commit()

if __name__ == "__main__":
    app.run()