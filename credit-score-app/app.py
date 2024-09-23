from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

# Initialize Flask app
app = Flask(__name__)

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Setup secret key and database URI
app.config['SECRET_KEY'] = 'my_key'
db_path = os.path.join(os.getcwd(), 'instance', 'users.db')
print(f"Database path: {db_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
# Initialize the database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    credit_score = db.Column(db.Integer, default=600)  # Start with a base score
    payment_history = db.Column(db.Integer, default=90)  # Percentage of on-time payments
    credit_utilization = db.Column(db.Float, default=0.3)  # 30% credit utilization
    credit_age = db.Column(db.Integer, default=2)  # Years of credit history
    inquiries = db.Column(db.Integer, default=1)  # Number of recent inquiries


# Function to calculate credit score
def calculate_credit_score(user):
    score = 600
    score += int(user.payment_history * 0.4)
    score += int((1 - user.credit_utilization) * 100 * 0.3)
    score += int(user.credit_age * 10 * 0.2)
    score -= user.inquiries * 10
    return min(850, max(300, score))  # Credit score range: 300 to 850


# Function to generate credit advice
def generate_credit_advice(user):
    advice = []
    if user.payment_history < 95:
        advice.append("Your payment history is below 95%. Try to make on-time payments to improve your score.")
    if user.credit_utilization > 0.3:
        advice.append("Your credit utilization is above 30%. Keeping your utilization below 30% can improve your score.")
    if user.credit_age < 5:
        advice.append("Your credit history is relatively short. Keep your accounts open to increase your credit age over time.")
    if user.inquiries > 2:
        advice.append("You have more than two recent inquiries. Avoid applying for new credit to prevent further impact.")
    if not advice:
        advice.append("You're doing great! Keep maintaining good credit habits.")
    return advice


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return 'Welcome to Credit Score App!'


# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.')
            return redirect(url_for('register'))

        # Randomized credit data for the new user
        payment_history = random.randint(80, 100)  # Between 80% and 100%
        credit_utilization = random.uniform(0.1, 0.5)  # Between 10% and 50%
        credit_age = random.randint(1, 10)  # Between 1 and 10 years
        inquiries = random.randint(0, 5)  # Between 0 and 5 inquiries

        new_user = User(username=username,
                        password=generate_password_hash(password, method='pbkdf2:sha256'),
                        payment_history=payment_history,
                        credit_utilization=credit_utilization,
                        credit_age=credit_age,
                        inquiries=inquiries)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Incorrect username or password.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('login.html')


# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
  # Mock data for account balances and late payments (can be stored in your database too)
    total_balance = round(random.uniform(1000, 5000), 2)  # Random balance between $1000 and $5000
    available_credit = round(random.uniform(500, 2000), 2)  # Random available credit
    late_payments = random.randint(0, 5)  # Random number of late payments

    # Other fields that are part of the current user (already set)
    user_credit_score = calculate_credit_score(current_user)
    credit_advice = generate_credit_advice(current_user)

    return render_template('dashboard.html',
                           credit_score=user_credit_score,
                           payment_history=current_user.payment_history,
                           credit_utilization=current_user.credit_utilization,
                           credit_age=current_user.credit_age,
                           inquiries=current_user.inquiries,
                           total_balance=total_balance,
                           available_credit=available_credit,
                           late_payments=late_payments,
                           advice=credit_advice)

if __name__ == '__main__':
    app.run(debug=True)
