import os
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify
)
from config import Config
from models import db, User, Income, Expense, Budget, FinancialGoal


def create_app():
    """Application factory for Personal Finance Advisor Bot."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance directory exists for SQLite database
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register template filters and context processors
    @app.context_processor
    def inject_global_data():
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
        return {
            'current_user': current_user,
            'expense_categories': Config.EXPENSE_CATEGORIES,
            'income_sources': Config.INCOME_SOURCES,
            'current_month_str': datetime.now().strftime('%Y-%m'),
            'current_year': datetime.now().year
        }

    @app.template_filter('currency')
    def currency_filter(val):
        """Format number as currency: $1,234.56"""
        try:
            val = float(val or 0)
            return f"${val:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    # --- Authentication Decorator ---
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def get_current_user():
        if 'user_id' in session:
            return db.session.get(User, session['user_id'])
        return None

    # --- Financial Calculation Helpers ---
    def get_financial_summary(user_id, month_str=None):
        """
        Calculate total income, total expenses, savings,
        savings percentage, and budget status for a given month.
        """
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')

        try:
            year, month = map(int, month_str.split('-'))
        except (ValueError, AttributeError):
            today = datetime.now()
            year, month = today.year, today.month
            month_str = f"{year:04d}-{month:02d}"

        # Incomes for the month
        incomes = Income.query.filter(
            Income.user_id == user_id,
            db.extract('year', Income.date) == year,
            db.extract('month', Income.date) == month
        ).all()

        # Expenses for the month
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == month
        ).all()

        total_income = sum(item.amount for item in incomes)
        total_expenses = sum(item.amount for item in expenses)
        savings = total_income - total_expenses
        savings_pct = (savings / total_income * 100) if total_income > 0 else 0.0

        # Category-wise expenses
        category_totals = {cat: 0.0 for cat in Config.EXPENSE_CATEGORIES}
        for exp in expenses:
            category_totals[exp.category] = category_totals.get(exp.category, 0.0) + exp.amount

        # Overall monthly budget
        overall_budget = Budget.query.filter_by(
            user_id=user_id,
            month=month_str,
            category='Overall'
        ).first()

        budget_amount = overall_budget.amount if overall_budget else 0.0
        budget_remaining = budget_amount - total_expenses if budget_amount > 0 else 0.0
        budget_used_pct = (total_expenses / budget_amount * 100) if budget_amount > 0 else 0.0

        # Category budgets
        cat_budgets = Budget.query.filter(
            Budget.user_id == user_id,
            Budget.month == month_str,
            Budget.category != 'Overall'
        ).all()
        category_budget_dict = {b.category: b.amount for b in cat_budgets}

        # Check overspending alerts
        alerts = []
        if budget_amount > 0:
            if total_expenses > budget_amount:
                over = total_expenses - budget_amount
                alerts.append({
                    'type': 'danger',
                    'title': 'Overspending Alert!',
                    'message': f"You have exceeded your overall monthly budget by ${over:,.2f}!"
                })
            elif budget_used_pct >= 90:
                alerts.append({
                    'type': 'warning',
                    'title': 'Budget Warning!',
                    'message': f"You have used {budget_used_pct:.1f}% of your monthly budget (${total_expenses:,.2f} of ${budget_amount:,.2f})."
                })

        # Category budget alerts
        for cat, limit in category_budget_dict.items():
            spent = category_totals.get(cat, 0.0)
            if spent > limit:
                alerts.append({
                    'type': 'danger',
                    'title': f'{cat} Over Budget!',
                    'message': f"Spent ${spent:,.2f} on {cat}, exceeding the limit of ${limit:,.2f} by ${(spent - limit):,.2f}."
                })

        return {
            'month_str': month_str,
            'year': year,
            'month': month,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'savings': savings,
            'savings_pct': round(savings_pct, 1),
            'budget_amount': budget_amount,
            'budget_remaining': budget_remaining,
            'budget_used_pct': round(budget_used_pct, 1),
            'category_totals': category_totals,
            'category_budget_dict': category_budget_dict,
            'alerts': alerts,
            'incomes_count': len(incomes),
            'expenses_count': len(expenses)
        }

    # --- Financial Advisor Summary (Rule-based for now; AI to be added in next step) ---
    def generate_financial_advice(user, user_prompt, summary_data):
        """
        Generate financial advice and analysis based on actual numbers.
        """
        income = summary_data['total_income']
        expenses = summary_data['total_expenses']
        savings = summary_data['savings']
        savings_pct = summary_data['savings_pct']
        budget = summary_data['budget_amount']

        top_cats = sorted(
            summary_data['category_totals'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        non_zero_cats = [f"{cat}: ${amt:,.2f}" for cat, amt in top_cats if amt > 0]

        response_lines = [
            f"### 💡 Financial Insights for {summary_data['month_str']}",
            "",
            f"- **Income:** ${income:,.2f} | **Expenses:** ${expenses:,.2f} | **Net Savings:** ${savings:,.2f} ({savings_pct}%)",
            ""
        ]

        # Check savings status
        if income == 0 and expenses == 0:
            response_lines.append("You haven't logged any income or expenses yet for this month. Start by adding your income and recent purchases so I can give you personalized financial advice!")
        elif income == 0 and expenses > 0:
            response_lines.append(f"⚠️ You recorded ${expenses:,.2f} in expenses without logging any income for this month. Please add your monthly income to calculate your savings rate.")
        elif savings < 0:
            response_lines.append(f"⚠️ **Deficit Alert:** You are currently spending ${abs(savings):,.2f} more than you earn this month. Let's look at your largest expense categories to find quick cutbacks.")
        elif savings_pct < 20:
            response_lines.append(f"📌 **Savings Rate ({savings_pct}%):** The standard recommendation (50/30/20 rule) is to save at least **20%** of your income (${(income * 0.2):,.2f}). You are currently saving ${savings:,.2f}.")
        else:
            response_lines.append(f"🎉 **Great job!** You have a strong savings rate of **{savings_pct}%** (${savings:,.2f}). Consider channeling these savings toward an emergency fund or investments.")

        # Top category advice
        if non_zero_cats:
            top_cat_name, top_cat_amt = top_cats[0]
            cat_pct = (top_cat_amt / expenses * 100) if expenses > 0 else 0
            response_lines.append(f"\n- **Biggest Spending Category:** **{top_cat_name}** at ${top_cat_amt:,.2f} ({cat_pct:.1f}% of total spending).")
            if top_cat_name == 'Food':
                response_lines.append("  *Tip:* Meal planning, batch cooking, and limiting food delivery to once a week can quickly save $100-$300/month.")
            elif top_cat_name == 'Shopping':
                response_lines.append("  *Tip:* Try applying a 48-hour cooling-off rule before any non-essential purchase over $30.")
            elif top_cat_name == 'Entertainment':
                response_lines.append("  *Tip:* Audit recurring streaming services and gym memberships to eliminate subscriptions you rarely use.")
            elif top_cat_name == 'Bills':
                response_lines.append("  *Tip:* Check if you can renegotiate your internet plan, switch phone carriers, or reduce energy usage.")
            elif top_cat_name == 'Rent':
                response_lines.append("  *Tip:* Rent is typically fixed; focus on optimizing variable categories like Food, Shopping, and Entertainment.")

        if budget > 0:
            if expenses > budget:
                response_lines.append(f"\n- **Budget Status:** You have exceeded your monthly budget of ${budget:,.2f} by ${(expenses - budget):,.2f}.")
            else:
                response_lines.append(f"\n- **Budget Status:** You have ${summary_data['budget_remaining']:,.2f} left in your ${budget:,.2f} budget.")
        else:
            response_lines.append("\n- **Budget Tip:** You haven't set a monthly budget yet! Head to the Budget page to establish your monthly spending target.")

        return "\n".join(response_lines)

    # ==========================================
    # ROUTES
    # ==========================================

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    # --- Authentication Routes ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            # Validations
            if not username or not email or not password:
                flash('Please fill out all required fields.', 'danger')
                return render_template('register.html', username=username, email=email)

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('register.html', username=username, email=email)

            if password != confirm_password:
                flash('Passwords do not match. Please re-enter.', 'danger')
                return render_template('register.html', username=username, email=email)

            if User.query.filter_by(username=username).first():
                flash('That username is already taken. Please choose another.', 'danger')
                return render_template('register.html', email=email)

            if User.query.filter_by(email=email).first():
                flash('That email address is already registered. Please log in.', 'danger')
                return redirect(url_for('login'))

            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            # Automatically log in the user
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            flash(f'Welcome aboard, {new_user.username}! Your account has been created.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username_or_email = request.form.get('username_or_email', '').strip()
            password = request.form.get('password', '')

            if not username_or_email or not password:
                flash('Please enter both your username/email and password.', 'warning')
                return render_template('login.html', username_or_email=username_or_email)

            # Check by username or email
            user = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email.lower())
            ).first()

            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username/email or password. Please try again.', 'danger')
                return render_template('login.html', username_or_email=username_or_email)

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out safely.', 'info')
        return redirect(url_for('login'))

    # --- Dashboard Route ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        # Recent 5 expenses
        recent_expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date.desc(), Expense.id.desc()).limit(5).all()

        # Recent 5 incomes
        recent_incomes = Income.query.filter_by(user_id=user.id).order_by(Income.date.desc(), Income.id.desc()).limit(5).all()

        # User's financial goals
        goals = FinancialGoal.query.filter_by(user_id=user.id).order_by(FinancialGoal.id.desc()).all()

        return render_template(
            'dashboard.html',
            summary=summary,
            recent_expenses=recent_expenses,
            recent_incomes=recent_incomes,
            goals=goals,
            selected_month=month_str
        )

    # --- Income Routes ---
    @app.route('/income', methods=['GET'])
    @login_required
    def income():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        try:
            year, month = map(int, month_str.split('-'))
            incomes = Income.query.filter(
                Income.user_id == user.id,
                db.extract('year', Income.date) == year,
                db.extract('month', Income.date) == month
            ).order_by(Income.date.desc()).all()
        except ValueError:
            incomes = Income.query.filter_by(user_id=user.id).order_by(Income.date.desc()).all()

        return render_template(
            'income.html',
            incomes=incomes,
            summary=summary,
            selected_month=month_str,
            today_str=date.today().strftime('%Y-%m-%d')
        )

    @app.route('/income/add', methods=['POST'])
    @login_required
    def add_income():
        user = get_current_user()
        source = request.form.get('source', '').strip()
        amount_val = request.form.get('amount', '0')
        date_str = request.form.get('date', '')
        notes = request.form.get('notes', '').strip()

        try:
            amount = float(amount_val)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            flash('Please enter a valid positive number for income amount.', 'danger')
            return redirect(url_for('income'))

        try:
            income_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            income_date = date.today()

        new_income = Income(
            user_id=user.id,
            source=source or 'Other',
            amount=amount,
            date=income_date,
            notes=notes
        )
        db.session.add(new_income)
        db.session.commit()

        flash(f'Income of ${amount:,.2f} from "{source}" added successfully!', 'success')
        return redirect(url_for('income', month=income_date.strftime('%Y-%m')))

    @app.route('/income/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_income(id):
        user = get_current_user()
        income_item = Income.query.filter_by(id=id, user_id=user.id).first_or_404()
        month_str = income_item.date.strftime('%Y-%m')
        db.session.delete(income_item)
        db.session.commit()
        flash('Income record deleted successfully.', 'info')
        return redirect(url_for('income', month=month_str))

    # --- Expenses Routes ---
    @app.route('/expenses', methods=['GET'])
    @login_required
    def expenses():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        cat_filter = request.args.get('category', '').strip()

        query = Expense.query.filter_by(user_id=user.id)

        if month_str:
            try:
                year, month = map(int, month_str.split('-'))
                query = query.filter(
                    db.extract('year', Expense.date) == year,
                    db.extract('month', Expense.date) == month
                )
            except ValueError:
                pass

        if cat_filter and cat_filter in Config.EXPENSE_CATEGORIES:
            query = query.filter(Expense.category == cat_filter)

        expense_list = query.order_by(Expense.date.desc(), Expense.id.desc()).all()
        summary = get_financial_summary(user.id, month_str)

        return render_template(
            'expenses.html',
            expenses=expense_list,
            summary=summary,
            selected_month=month_str,
            selected_category=cat_filter,
            today_str=date.today().strftime('%Y-%m-%d')
        )

    @app.route('/expenses/add', methods=['POST'])
    @login_required
    def add_expense():
        user = get_current_user()
        title = request.form.get('title', '').strip()
        amount_val = request.form.get('amount', '0')
        category = request.form.get('category', 'Other')
        date_str = request.form.get('date', '')
        notes = request.form.get('notes', '').strip()

        if not title:
            flash('Please enter a description/title for the expense.', 'danger')
            return redirect(url_for('expenses'))

        try:
            amount = float(amount_val)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            flash('Please enter a valid positive number for expense amount.', 'danger')
            return redirect(url_for('expenses'))

        try:
            expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            expense_date = date.today()

        new_expense = Expense(
            user_id=user.id,
            title=title,
            amount=amount,
            category=category,
            date=expense_date,
            notes=notes
        )
        db.session.add(new_expense)
        db.session.commit()

        flash(f'Expense "{title}" (${amount:,.2f}) added successfully!', 'success')
        return redirect(url_for('expenses', month=expense_date.strftime('%Y-%m')))

    @app.route('/expenses/edit/<int:id>', methods=['POST'])
    @login_required
    def edit_expense(id):
        user = get_current_user()
        expense_item = Expense.query.filter_by(id=id, user_id=user.id).first_or_404()

        title = request.form.get('title', '').strip()
        amount_val = request.form.get('amount', '0')
        category = request.form.get('category', 'Other')
        date_str = request.form.get('date', '')
        notes = request.form.get('notes', '').strip()

        if not title:
            flash('Expense title cannot be empty.', 'danger')
            return redirect(url_for('expenses'))

        try:
            amount = float(amount_val)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            flash('Please enter a valid positive amount.', 'danger')
            return redirect(url_for('expenses'))

        try:
            expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            expense_date = expense_item.date

        expense_item.title = title
        expense_item.amount = amount
        expense_item.category = category
        expense_item.date = expense_date
        expense_item.notes = notes

        db.session.commit()
        flash(f'Expense "{title}" updated successfully.', 'success')
        return redirect(url_for('expenses', month=expense_date.strftime('%Y-%m')))

    @app.route('/expenses/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_expense(id):
        user = get_current_user()
        expense_item = Expense.query.filter_by(id=id, user_id=user.id).first_or_404()
        month_str = expense_item.date.strftime('%Y-%m')
        db.session.delete(expense_item)
        db.session.commit()
        flash('Expense deleted successfully.', 'info')
        return redirect(url_for('expenses', month=month_str))

    # --- Budget Routes ---
    @app.route('/budget', methods=['GET'])
    @login_required
    def budget():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        all_budgets = Budget.query.filter_by(
            user_id=user.id,
            month=month_str
        ).order_by(Budget.category.asc()).all()

        return render_template(
            'budget.html',
            summary=summary,
            budgets=all_budgets,
            selected_month=month_str
        )

    @app.route('/budget/set', methods=['POST'])
    @login_required
    def set_budget():
        user = get_current_user()
        month_str = request.form.get('month', datetime.now().strftime('%Y-%m'))
        category = request.form.get('category', 'Overall')
        amount_val = request.form.get('amount', '0')

        try:
            amount = float(amount_val)
            if amount < 0:
                raise ValueError()
        except ValueError:
            flash('Please enter a valid positive budget amount.', 'danger')
            return redirect(url_for('budget', month=month_str))

        # Check if budget already exists for this month and category
        existing = Budget.query.filter_by(
            user_id=user.id,
            month=month_str,
            category=category
        ).first()

        if existing:
            existing.amount = amount
            flash(f'Budget for {category} ({month_str}) updated to ${amount:,.2f}.', 'success')
        else:
            new_budget = Budget(
                user_id=user.id,
                month=month_str,
                category=category,
                amount=amount
            )
            db.session.add(new_budget)
            flash(f'Budget for {category} ({month_str}) set to ${amount:,.2f}.', 'success')

        db.session.commit()
        return redirect(url_for('budget', month=month_str))

    @app.route('/budget/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_budget(id):
        user = get_current_user()
        budget_item = Budget.query.filter_by(id=id, user_id=user.id).first_or_404()
        month_str = budget_item.month
        db.session.delete(budget_item)
        db.session.commit()
        flash('Budget limit removed.', 'info')
        return redirect(url_for('budget', month=month_str))

    # --- Financial Goals Routes ---
    @app.route('/goals', methods=['GET'])
    @login_required
    def goals():
        user = get_current_user()
        all_goals = FinancialGoal.query.filter_by(user_id=user.id).order_by(FinancialGoal.id.desc()).all()
        return render_template('goals.html', goals=all_goals, today_str=date.today().strftime('%Y-%m-%d'))

    @app.route('/goals/add', methods=['POST'])
    @login_required
    def add_goal():
        user = get_current_user()
        title = request.form.get('title', '').strip()
        target_val = request.form.get('target_amount', '0')
        current_val = request.form.get('current_amount', '0')
        target_date_str = request.form.get('target_date', '')

        if not title:
            flash('Please give your goal a title.', 'danger')
            return redirect(url_for('goals'))

        try:
            target_amount = float(target_val)
            current_amount = float(current_val) if current_val else 0.0
            if target_amount <= 0:
                raise ValueError()
        except ValueError:
            flash('Please enter valid dollar amounts.', 'danger')
            return redirect(url_for('goals'))

        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = None

        new_goal = FinancialGoal(
            user_id=user.id,
            title=title,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            status='Completed' if current_amount >= target_amount else 'In Progress'
        )
        db.session.add(new_goal)
        db.session.commit()

        flash(f'Goal "{title}" created!', 'success')
        return redirect(url_for('goals'))

    @app.route('/goals/update/<int:id>', methods=['POST'])
    @login_required
    def update_goal(id):
        user = get_current_user()
        goal = FinancialGoal.query.filter_by(id=id, user_id=user.id).first_or_404()

        add_amount = request.form.get('add_amount', '0')
        try:
            amt = float(add_amount)
            goal.current_amount += amt
            if goal.current_amount >= goal.target_amount:
                goal.status = 'Completed'
            db.session.commit()
            flash(f'Added ${amt:,.2f} towards "{goal.title}"!', 'success')
        except ValueError:
            flash('Invalid contribution amount.', 'danger')

        return redirect(url_for('goals'))

    @app.route('/goals/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_goal(id):
        user = get_current_user()
        goal = FinancialGoal.query.filter_by(id=id, user_id=user.id).first_or_404()
        db.session.delete(goal)
        db.session.commit()
        flash('Financial goal removed.', 'info')
        return redirect(url_for('goals'))

    # --- Financial Advisor Routes ---
    @app.route('/advisor')
    @login_required
    def advisor():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        return render_template(
            'advisor.html',
            summary=summary,
            has_api_key=False,
            selected_month=month_str
        )

    @app.route('/api/advisor/chat', methods=['POST'])
    @login_required
    def advisor_chat():
        user = get_current_user()
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        month_str = data.get('month', datetime.now().strftime('%Y-%m'))

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        summary = get_financial_summary(user.id, month_str)
        response_text = generate_financial_advice(user, user_message, summary)

        return jsonify({
            'reply': response_text,
            'summary': {
                'income': summary['total_income'],
                'expenses': summary['total_expenses'],
                'savings': summary['savings'],
                'savings_pct': summary['savings_pct']
            }
        })

    @app.route('/api/advisor/analyze', methods=['POST'])
    @login_required
    def advisor_analyze():
        user = get_current_user()
        data = request.get_json() or {}
        month_str = data.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        prompt = (
            "Please provide a comprehensive spending analysis and saving suggestions for my monthly finances: "
            "1. Spending Breakdown & Patterns\n"
            "2. 3 Actionable Cost-Cutting Ideas for my highest spending categories\n"
            "3. 50/30/20 Rule comparison based on my actual income\n"
            "4. A realistic 3-month savings plan."
        )

        analysis = generate_financial_advice(user, prompt, summary)
        return jsonify({'analysis': analysis})

    # --- Monthly Financial Report Route ---
    @app.route('/report')
    @login_required
    def report():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        try:
            year, month = map(int, month_str.split('-'))
            incomes = Income.query.filter(
                Income.user_id == user.id,
                db.extract('year', Income.date) == year,
                db.extract('month', Income.date) == month
            ).order_by(Income.date.asc()).all()

            expenses = Expense.query.filter(
                Expense.user_id == user.id,
                db.extract('year', Expense.date) == year,
                db.extract('month', Expense.date) == month
            ).order_by(Expense.date.asc()).all()
        except ValueError:
            incomes, expenses = [], []

        # Category breakdown list with percentages
        category_breakdown = []
        tot_exp = summary['total_expenses']
        for cat in Config.EXPENSE_CATEGORIES:
            amt = summary['category_totals'].get(cat, 0.0)
            pct = (amt / tot_exp * 100) if tot_exp > 0 else 0.0
            budget_limit = summary['category_budget_dict'].get(cat, 0.0)
            category_breakdown.append({
                'category': cat,
                'amount': amt,
                'percentage': round(pct, 1),
                'budget': budget_limit,
                'over_budget': amt > budget_limit if budget_limit > 0 else False
            })

        # Sort category breakdown descending by amount
        category_breakdown.sort(key=lambda x: x['amount'], reverse=True)

        # Quick summary for report
        summary_prompt = "Executive monthly report summary"
        report_summary = generate_financial_advice(user, summary_prompt, summary)

        return render_template(
            'report.html',
            summary=summary,
            incomes=incomes,
            expenses=expenses,
            category_breakdown=category_breakdown,
            ai_summary=report_summary,
            selected_month=month_str
        )

    # --- Chart Data API Route ---
    @app.route('/api/chart-data')
    @login_required
    def chart_data():
        user = get_current_user()
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        summary = get_financial_summary(user.id, month_str)

        # Categories with spending > 0
        cat_labels = []
        cat_values = []
        for cat, amt in summary['category_totals'].items():
            if amt > 0:
                cat_labels.append(cat)
                cat_values.append(amt)

        if not cat_labels:
            cat_labels = ['No Expenses']
            cat_values = [0]

        return jsonify({
            'month': month_str,
            'income': summary['total_income'],
            'expenses': summary['total_expenses'],
            'savings': max(summary['savings'], 0),
            'budget': summary['budget_amount'],
            'categories': {
                'labels': cat_labels,
                'values': cat_values
            }
        })

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Personal Finance Advisor Bot starting on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
