import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-finance-bot-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "finance_bot.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Standard expense categories required by application
    EXPENSE_CATEGORIES = [
        'Food',
        'Rent',
        'Transport',
        'Education',
        'Healthcare',
        'Shopping',
        'Entertainment',
        'Bills',
        'Other'
    ]

    # Income sources presets
    INCOME_SOURCES = [
        'Salary',
        'Freelance',
        'Investment',
        'Business',
        'Bonus',
        'Gift',
        'Other'
    ]
