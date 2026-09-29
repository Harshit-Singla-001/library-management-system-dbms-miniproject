from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from blueprints.auth import student_required
from db import query_db, get_db_transaction
from config import Config
from datetime import date

student_bp = Blueprint('student', __name__, url_prefix='/student')

def get_current_student():
    """Retrieve freshly updated student record from database with effective permission calculation."""
    roll_number = session.get('roll_number')
    student_id = session.get('student_id')
    
    if roll_number:
        student = query_db(
            """SELECT s.*, 
                      (SELECT COUNT(*) FROM issued_books ib WHERE ib.student_id = s.student_id AND ib.status IN ('ISSUED', 'OVERDUE')) AS active_books,
                      (SELECT SUM(f.fine_amount) FROM fines f WHERE f.student_id = s.student_id AND f.payment_status = 'UNPAID') AS unpaid_fine
               FROM students s WHERE s.roll_number = %s""",
            (roll_number,),
            one=True
        )
    else:
        student = query_db(
            """SELECT s.*, 
                      (SELECT COUNT(*) FROM issued_books ib WHERE ib.student_id = s.student_id AND ib.status IN ('ISSUED', 'OVERDUE')) AS active_books,
                      (SELECT SUM(f.fine_amount) FROM fines f WHERE f.student_id = s.student_id AND f.payment_status = 'UNPAID') AS unpaid_fine
               FROM students s WHERE s.student_id = %s""",
            (student_id,),
            one=True
        )

    if student:
        student['unpaid_fine'] = float(student.get('unpaid_fine') or 0.0)
        # Determine dynamic effective permission state and user-friendly explanation
        if student['borrowing_permission'] == 'REVOKED':
            student['effective_permission'] = 'REVOKED'
            student['permission_reason'] = 'Borrowing privileges suspended by library administration.'
        elif student['active_books'] >= Config.MAX_ISSUED_BOOKS:
            student['effective_permission'] = 'REVOKED'
            student['permission_reason'] = f'Maximum borrowing limit reached ({Config.MAX_ISSUED_BOOKS}/{Config.MAX_ISSUED_BOOKS} books). Return an active book to restore borrowing.'
        elif student['unpaid_fine'] > 0:
            student['effective_permission'] = 'REVOKED'
            student['permission_reason'] = f'Borrowing suspended due to outstanding unpaid fine of ₹{student["unpaid_fine"]:.2f}. Please settle fines at library desk.'
        else:
            student['effective_permission'] = 'GRANTED'
            student['permission_reason'] = f'Borrowing permission granted. You can borrow up to {Config.MAX_ISSUED_BOOKS - student["active_books"]} more book(s).'

    return student

# -----------------------------------------------------------------------------
# 1. STUDENT DASHBOARD
# -----------------------------------------------------------------------------
@student_bp.route('/dashboard')
@student_required
def dashboard():
    student = get_current_student()
    roll_number = student.get('roll_number') or session.get('roll_number')

    # Retrieve currently issued books with live days remaining / overdue calculation
    active_loans = query_db("""
        SELECT ib.issue_id, b.book_id, b.title, b.isbn, ib.issue_date, ib.due_date, ib.status,
               DATEDIFF(ib.due_date, CURDATE()) AS days_left,
               DATEDIFF(CURDATE(), ib.due_date) AS days_overdue
        FROM issued_books ib
        JOIN books b ON ib.book_id = b.book_id
        JOIN students s ON ib.student_id = s.student_id
        WHERE s.roll_number = %s AND ib.status IN ('ISSUED', 'OVERDUE')
        ORDER BY ib.due_date ASC
    """, (roll_number,))

    return render_template(
        'student/dashboard.html',
        student=student,
        active_loans=active_loans,
        max_books=Config.MAX_ISSUED_BOOKS
    )

# -----------------------------------------------------------------------------
# 2. BROWSE & SEARCH CATALOG
# -----------------------------------------------------------------------------
@student_bp.route('/books')
@student_required
def books():
    student = get_current_student()
    roll_number = student.get('roll_number') or session.get('roll_number')
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '').strip()

    sql = """
        SELECT b.book_id, b.isbn, b.title, c.category_name, b.total_copies, b.available_copies, 
               b.edition, b.publish_year,
               GROUP_CONCAT(a.author_name SEPARATOR ', ') AS authors,
               (SELECT COUNT(*) FROM issued_books ib 
                JOIN students s ON ib.student_id = s.student_id
                WHERE ib.book_id = b.book_id AND s.roll_number = %s AND ib.status IN ('ISSUED', 'OVERDUE')) AS already_issued
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        WHERE 1=1
    """
    params = [roll_number]
    if search:
        sql += " AND (b.title LIKE %s OR b.isbn LIKE %s OR a.author_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if category_id:
        sql += " AND b.category_id = %s"
        params.append(category_id)

    sql += " GROUP BY b.book_id ORDER BY b.title ASC"
    book_list = query_db(sql, params)
    categories = query_db("SELECT * FROM categories ORDER BY category_name ASC")

    return render_template('student/books.html', books=book_list, categories=categories, search=search, selected_cat=category_id, student=student)

# -----------------------------------------------------------------------------
# 3. BOOK ISSUE TRANSACTION (6-POINT ATOMIC VALIDATION)
# -----------------------------------------------------------------------------
@student_bp.route('/issue/<int:book_id>', methods=['POST'])
@student_required
def issue_book(book_id):
    roll_number = session.get('roll_number')

    try:
        with get_db_transaction() as cursor:
            # -----------------------------------------------------------------
            # RULE CHECK 2: FRESH DB CHECK OF BORROWING PERMISSION
            # -----------------------------------------------------------------
            cursor.execute("SELECT student_id, borrowing_permission, full_name FROM students WHERE roll_number = %s", (roll_number,))
            student = cursor.fetchone()
            if not student or student['borrowing_permission'] != 'GRANTED':
                flash("Issue Rejected: Your library borrowing permission is currently REVOKED by the administration. Please contact the librarian desk.", "danger")
                return redirect(url_for('student.books'))

            student_id = student['student_id']

            # -----------------------------------------------------------------
            # RULE CHECK 1: MAXIMUM 3 BOOKS LIMIT
            # -----------------------------------------------------------------
            cursor.execute(
                """SELECT COUNT(*) AS active_count 
                   FROM issued_books ib
                   JOIN students s ON ib.student_id = s.student_id
                   WHERE s.roll_number = %s AND ib.status IN ('ISSUED', 'OVERDUE')""",
                (roll_number,)
            )
            active_count = cursor.fetchone()['active_count']
            if active_count >= Config.MAX_ISSUED_BOOKS:
                flash(f"Issue Rejected: You have reached the maximum borrowing limit of {Config.MAX_ISSUED_BOOKS} books. You must return an active book before borrowing another.", "danger")
                return redirect(url_for('student.books'))

            # -----------------------------------------------------------------
            # RULE CHECK 3: UNPAID FINES BLOCK
            # -----------------------------------------------------------------
            cursor.execute(
                """SELECT SUM(fine_amount) AS total_unpaid 
                   FROM fines f
                   JOIN students s ON f.student_id = s.student_id
                   WHERE s.roll_number = %s AND f.payment_status = 'UNPAID'""",
                (roll_number,)
            )
            unpaid = float(cursor.fetchone()['total_unpaid'] or 0.0)
            if unpaid > 0:
                flash(f"Issue Rejected: You have outstanding unpaid fines of ₹{unpaid:.2f}. Please clear your fine dues before borrowing new books.", "danger")
                return redirect(url_for('student.books'))

            # -----------------------------------------------------------------
            # RULE CHECK 5: NO DUPLICATE ACTIVE LOANS OF THE SAME BOOK
            # -----------------------------------------------------------------
            cursor.execute(
                """SELECT COUNT(*) AS count 
                   FROM issued_books ib
                   JOIN students s ON ib.student_id = s.student_id
                   WHERE s.roll_number = %s AND ib.book_id = %s AND ib.status IN ('ISSUED', 'OVERDUE')""",
                (roll_number, book_id)
            )
            already_holding = cursor.fetchone()['count']
            if already_holding > 0:
                flash("Issue Rejected: You already hold an active copy of this book.", "warning")
                return redirect(url_for('student.books'))

            # -----------------------------------------------------------------
            # RULE CHECK 4: BOOK AVAILABILITY ROW LOCK (SELECT ... FOR UPDATE)
            # -----------------------------------------------------------------
            cursor.execute("SELECT book_id, title, available_copies FROM books WHERE book_id = %s FOR UPDATE", (book_id,))
            book = cursor.fetchone()
            if not book or book['available_copies'] <= 0:
                flash("Issue Rejected: Sorry, all copies of this book are currently issued to other students.", "danger")
                return redirect(url_for('student.books'))

            # -----------------------------------------------------------------
            # ALL RULES PASSED: ATOMIC INVENTORY DECREMENT & ISSUE INSERT
            # -----------------------------------------------------------------
            cursor.execute(
                """INSERT INTO issued_books (student_id, book_id, issue_date, due_date, status, remarks) 
                   VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL %s DAY), 'ISSUED', 'Student self-service issue')""",
                (student_id, book_id, Config.LOAN_PERIOD_DAYS)
            )

            cursor.execute(
                "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s",
                (book_id,)
            )

        flash(f"Success! '{book['title']}' has been issued to you. Please return it within {Config.LOAN_PERIOD_DAYS} days to avoid fines.", "success")
        return redirect(url_for('student.dashboard'))

    except Exception as e:
        flash(f"System error during checkout: {str(e)}", "danger")
        return redirect(url_for('student.books'))

# -----------------------------------------------------------------------------
# 4. BOOK RETURN PROCESS & FINE CALCULATION
# -----------------------------------------------------------------------------
@student_bp.route('/return')
@student_required
def return_page():
    student = get_current_student()
    roll_number = student.get('roll_number') or session.get('roll_number')
    active_loans = query_db("""
        SELECT ib.issue_id, b.book_id, b.title, b.isbn, ib.issue_date, ib.due_date, ib.status,
               DATEDIFF(CURDATE(), ib.due_date) AS overdue_days
        FROM issued_books ib
        JOIN books b ON ib.book_id = b.book_id
        JOIN students s ON ib.student_id = s.student_id
        WHERE s.roll_number = %s AND ib.status IN ('ISSUED', 'OVERDUE')
        ORDER BY ib.due_date ASC
    """, (roll_number,))

    return render_template('student/return.html', student=student, active_loans=active_loans, daily_rate=Config.DAILY_FINE_RATE)

@student_bp.route('/return/<int:issue_id>', methods=['POST'])
@student_required
def process_return(issue_id):
    roll_number = session.get('roll_number')

    try:
        with get_db_transaction() as cursor:
            # Verify issue belongs to student and is active
            cursor.execute(
                """SELECT ib.*, b.title, b.book_id, s.student_id 
                   FROM issued_books ib
                   JOIN books b ON ib.book_id = b.book_id
                   JOIN students s ON ib.student_id = s.student_id
                   WHERE ib.issue_id = %s AND s.roll_number = %s AND ib.status IN ('ISSUED', 'OVERDUE')""",
                (issue_id, roll_number)
            )
            issue = cursor.fetchone()

            if not issue:
                flash("Active loan record not found or already returned.", "danger")
                return redirect(url_for('student.return_page'))

            student_id = issue['student_id']

            # 1. Update loan status to RETURNED and set return_date
            cursor.execute(
                "UPDATE issued_books SET return_date = CURDATE(), status = 'RETURNED' WHERE issue_id = %s",
                (issue_id,)
            )

            # 2. Increment physical available copies
            cursor.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s",
                (issue['book_id'],)
            )

            # 3. Fine calculation
            today = date.today()
            due_date = issue['due_date']
            fine_message = ""

            if today > due_date:
                overdue_days = (today - due_date).days
                fine_amount = overdue_days * Config.DAILY_FINE_RATE

                cursor.execute(
                    """INSERT INTO fines (issue_id, student_id, fine_amount, payment_status) 
                       VALUES (%s, %s, %s, 'UNPAID')""",
                    (issue_id, student_id, fine_amount)
                )
                fine_message = f" Note: Returned {overdue_days} day(s) late. A fine of ₹{fine_amount:.2f} has been added to your account."
            else:
                fine_message = " Returned on time with ₹0.00 fine!"

        flash(f"Book '{issue['title']}' returned successfully.{fine_message}", "success" if not fine_message.startswith(" Note: Returned") else "warning")
        return redirect(url_for('student.dashboard'))

    except Exception as e:
        flash(f"Error returning book: {str(e)}", "danger")
        return redirect(url_for('student.return_page'))

# -----------------------------------------------------------------------------
# 5. BORROWING HISTORY
# -----------------------------------------------------------------------------
@student_bp.route('/history')
@student_required
def history():
    student = get_current_student()
    roll_number = student.get('roll_number') or session.get('roll_number')
    past_loans = query_db("""
        SELECT ib.issue_id, b.title, b.isbn, ib.issue_date, ib.due_date, ib.return_date, ib.status,
               f.fine_amount, f.payment_status
        FROM issued_books ib
        JOIN books b ON ib.book_id = b.book_id
        JOIN students s ON ib.student_id = s.student_id
        LEFT JOIN fines f ON ib.issue_id = f.issue_id
        WHERE s.roll_number = %s AND ib.status = 'RETURNED'
        ORDER BY ib.return_date DESC
    """, (roll_number,))

    return render_template('student/history.html', student=student, past_loans=past_loans)

# -----------------------------------------------------------------------------
# 6. MY FINES
# -----------------------------------------------------------------------------
@student_bp.route('/fines')
@student_required
def fines():
    student = get_current_student()
    roll_number = student.get('roll_number') or session.get('roll_number')
    fines_list = query_db("""
        SELECT f.fine_id, f.fine_amount, f.payment_status, f.paid_date,
               b.title, ib.issue_date, ib.due_date, ib.return_date
        FROM fines f
        JOIN issued_books ib ON f.issue_id = ib.issue_id
        JOIN books b ON ib.book_id = b.book_id
        JOIN students s ON f.student_id = s.student_id
        WHERE s.roll_number = %s
        ORDER BY f.fine_id DESC
    """, (roll_number,))

    return render_template('student/fines.html', student=student, fines=fines_list)

# -----------------------------------------------------------------------------
# 7. STUDENT PROFILE
# -----------------------------------------------------------------------------
@student_bp.route('/profile')
@student_required
def profile():
    student = get_current_student()
    return render_template('student/profile.html', student=student)
