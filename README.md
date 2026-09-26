# 💰 Personal Finance Advisor Bot

A beginner-friendly full-stack web application built with **Python**, **Flask**, **Flask-SQLAlchemy**, **SQLite**, and **Google Gemini AI**.

---

## ✨ Features

1. **User Authentication**: Secure user registration, login, and logout with hashed passwords (using Werkzeug).
2. **Interactive Financial Dashboard**:
   - Monthly summary cards: Total Income, Total Expenses, Net Savings, and Savings Rate (%).
   - Budget status progress bars.
   - Real-time overspending alerts.
   - Interactive charts for category spending breakdown (Doughnut) and cash flow comparison (Bar).
   - Recent transactions preview.
3. **Monthly Income Management**: Record monthly income streams (Salary, Freelance, Investment, Business, etc.).
4. **Expense Tracking**: Add, edit, and delete expenses across 9 standard categories:
   - 🍔 Food
   - 🏠 Rent
   - 🚗 Transport
   - 📚 Education
   - 🏥 Healthcare
   - 🛍️ Shopping
   - 🎬 Entertainment
   - 💡 Bills
   - 📦 Other
5. **Monthly Budget Management**:
   - Set overall monthly spending limits.
   - Set category-specific limits.
   - Color-coded progress indicators (Safe / Warning / Overspent).
6. **AI Financial Advisor (Powered by Gemini AI)**:
   - Real-time conversational AI bot loaded with your actual financial numbers.
   - Quick prompt pills for instant budgeting checks, the 50/30/20 rule, and cutback suggestions.
   - Works offline with smart built-in rule-based insights if an API key is not yet configured.
7. **AI Spending Analysis & Saving Suggestions**: One-click in-depth audit of spending leaks and customized 3-month savings plan.
8. **Monthly Financial Report**:
   - Itemized income and expense statements.
   - Category percentage distribution.
   - One-click **Print / Save as PDF** report view.
9. **Financial Goals Tracker**: Set savings targets for Emergency Funds, Vacations, etc., and record contributions toward completion.

---

## 📁 Project Structure

```text
Personal-Finance-Advisor-Bot/
│
├── app.py                  # Main Flask routes, calculations & Gemini AI logic
├── config.py               # Configuration & categories
├── models.py               # SQLAlchemy models (User, Income, Expense, Budget, FinancialGoal)
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment template
├── .env                    # Local environment variables (API keys)
├── .gitignore              # Ignored files
├── README.md               # Setup and usage guide
│
├── templates/              # Jinja HTML templates
│   ├── base.html           # Base layout with navbar, alerts & footer
│   ├── index.html          # Public landing page
│   ├── login.html          # User login page
│   ├── register.html       # User registration page
│   ├── dashboard.html      # Main dashboard with metrics and charts
│   ├── income.html         # Income entry and history
│   ├── expenses.html       # Expense management (add, edit, filter, delete)
│   ├── budget.html         # Overall and category budget tracking
│   ├── advisor.html        # Gemini AI advisor chat interface
│   ├── report.html         # Monthly financial statement & PDF print view
│   └── goals.html          # Financial goals tracker
│
├── static/
│   ├── css/
│   │   └── style.css       # Clean fintech theme and print styles
│   └── js/
│       └── script.js       # Chart.js and AI chat scripts
│
└── instance/
    └── finance_bot.db      # SQLite database (auto-created on first run)
```

---

## 🚀 How to Install and Run on Windows

Follow these simple step-by-step instructions in **Windows PowerShell** or **Command Prompt (CMD)**:

### 1. Open Terminal in the Project Directory
Make sure your terminal is opened inside the `Personal-Finance-Advisor-Bot` directory.

### 2. Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies:
```powershell
python -m venv venv
```

### 3. Activate the Virtual Environment
- **On PowerShell:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If you get a script execution policy warning on PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the command again).*

- **On Command Prompt (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```

Once activated, you will see `(venv)` at the beginning of your command line.

### 4. Install the Required Dependencies
Run:
```powershell
pip install -r requirements.txt
```

### 5. Configure Your Gemini AI API Key (Optional but Recommended)
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Open the `.env` file in the project root:
   ```env
   SECRET_KEY=dev-secret-finance-bot-key-2026
   GEMINI_API_KEY=AIzaSy...your_actual_api_key_here
   ```
> **Note:** If you run the app without an API key, the AI Advisor will automatically operate in **Smart Offline Mode**, providing personalized calculations and advice using built-in financial intelligence.

### 6. Run the Application
Start the Flask development server:
```powershell
python app.py
```

### 7. Access in Your Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

1. Click **"Get Started Free"** or **"Register"** to create a test user.
2. Log in and start adding your income, setting a monthly budget, logging expenses, and chatting with Penny the AI Advisor!

---

## 🔒 Security Best Practices
- Passwords are encrypted using Werkzeug's `generate_password_hash` with secure salt hashing.
- User financial records are strictly isolated by `user_id` session verification.
- Protected routes require authentication via the `@login_required` decorator.
