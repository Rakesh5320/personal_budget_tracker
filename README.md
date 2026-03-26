# Personal Budget Tracker

A **Personal Budget Tracker** is a web-based application that helps users manage their finances by tracking income and expenses in an organized way. The system allows users to record financial transactions, analyze spending patterns, and generate visual reports to better understand their financial habits.

This application is designed to provide a simple and user-friendly interface for managing personal budgets with graphical insights and report generation.

---

## Features

- User Authentication (Login / Logout)
- Add Income Transactions
- Add Expense Transactions
- Categorize income and expenses
- View Daily, Weekly, and Monthly Reports
- Data Visualization using Bar Charts and Pie Charts
- Export Financial Reports to PDF
- Simple and Responsive Web Interface

---

## Technologies Used

### Frontend
- HTML
- CSS

### Backend
- Python (Flask)

### Database
- SQLite / MySQL

### Visualization
- Chart.js / Matplotlib

### Report Generation
- ReportLab (PDF Export)

---

## Project Structure
personal_budget_tracker/
│
├── app.py
├── database.db
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── add_income.html
│   ├── add_expense.html
│   ├── report.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── charts.js
│
└── README.md

---

## Installation

### 1 Clone the repository
git cloneb https://github.com/Rakesh5320/personal_budget_tracker.git

### 2 Navigate to the project directory
cd personal-budget-tracker


### 3 Install required libraries
pip install flask
pip install reportlab

### 4 Run the application
python app.py


### 5 Open in browser
http://127.0.0.1:5000

---

## Usage

1. Login to the system.
2. Add your income sources.
3. Record your daily expenses.
4. View financial reports.
5. Analyze spending through charts.
6. Export reports as PDF.

---

## Screenshots
login page
<img width="1366" height="688" alt="image" src="https://github.com/user-attachments/assets/4d66a6aa-694e-4c88-8d69-e7c5d6ea5e06" />
Dashboard page
<img width="1361" height="688" alt="image" src="https://github.com/user-attachments/assets/a2ec6597-4361-4110-b3e6-6b04828f10ce" />
Income page
<img width="1366" height="686" alt="image" src="https://github.com/user-attachments/assets/f3e3ba1e-9441-405d-9882-fb9e9d7c6398" />
Expense page
<img width="1366" height="690" alt="image" src="https://github.com/user-attachments/assets/c7e7e941-76e0-4bd3-9e90-0271720ae34f" />
Report page
<img width="1365" height="685" alt="image" src="https://github.com/user-attachments/assets/5b12791f-442f-4d8d-b749-259044209f0b" />



---

## Future Improvements

- User registration system
- Multi-user support
- Export reports to Excel
- Budget limit alerts
- Mobile responsive UI
- Cloud database integration

---

## Contribution

Contributions are welcome. If you would like to improve this project:

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Submit a pull request

---

## License

This project is licensed under the MIT License.

---

## Author

Developed by **Rakesh**

