from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def get_utc_now():
    """Helper to return current UTC time."""
    return datetime.now(timezone.utc)

class User(db.Model):
    """User account model for authentication and data association."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    # Relationships
    incomes = db.relationship('Income', backref='user', cascade='all, delete-orphan', lazy=True)
    expenses = db.relationship('Expense', backref='user', cascade='all, delete-orphan', lazy=True)
    budgets = db.relationship('Budget', backref='user', cascade='all, delete-orphan', lazy=True)
    financial_goals = db.relationship('FinancialGoal', backref='user', cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Income(db.Model):
    """Monthly income entry."""
    __tablename__ = 'income'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def __repr__(self):
        return f'<Income {self.source} - ${self.amount}>'


class Expense(db.Model):
    """Expense entry categorized under pre-defined categories."""
    __tablename__ = 'expense'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def __repr__(self):
        return f'<Expense {self.title} - ${self.amount} ({self.category})>'


class Budget(db.Model):
    """Monthly budget limit for overall or specific category."""
    __tablename__ = 'budget'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    category = db.Column(db.String(50), default='Overall', nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def __repr__(self):
        return f'<Budget {self.month} - {self.category}: ${self.amount}>'


class FinancialGoal(db.Model):
    """Financial goal (e.g., Emergency Fund, Vacation, Down Payment)."""
    __tablename__ = 'financial_goal'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0, nullable=False)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='In Progress', nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    @property
    def progress_percentage(self):
        if not self.target_amount or self.target_amount <= 0:
            return 0
        pct = (self.current_amount / self.target_amount) * 100
        return min(round(pct, 1), 100.0)

    def __repr__(self):
        return f'<FinancialGoal {self.title} - ${self.current_amount}/${self.target_amount}>'
