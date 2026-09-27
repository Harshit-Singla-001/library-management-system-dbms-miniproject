from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from functools import wraps
from db import query_db

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'ADMIN':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'STUDENT':
            flash('Access denied. Student portal privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please provide both username/roll number and password.', 'warning')
            return render_template('auth/login.html', username=username)

        # Secure parameterized query to authenticate user
        user = query_db(
            "SELECT user_id, username, password_hash, role FROM users WHERE username = %s",
            (username,),
            one=True
        )

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password. Please check your credentials.', 'danger')
            return render_template('auth/login.html', username=username)

        # Establish secure session context
        session.clear()
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role'] = user['role']

        if user['role'] == 'STUDENT':
            # Retrieve linked student profile
            student = query_db(
                """SELECT student_id, roll_number, full_name, borrowing_permission, department 
                   FROM students WHERE user_id = %s""",
                (user['user_id'],),
                one=True
            )
            if student:
                session['student_id'] = student['student_id']
                session['roll_number'] = student['roll_number']
                session['full_name'] = student['full_name']
                session['borrowing_permission'] = student['borrowing_permission']
                flash(f'Welcome back, {student["full_name"]}!', 'success')
                return redirect(url_for('student.dashboard'))
            else:
                flash('Student profile not found. Please contact administration.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            session['full_name'] = 'Admin'
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))
