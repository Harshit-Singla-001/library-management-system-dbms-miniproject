from flask import Blueprint, render_template, request, redirect, url_for, flash
from blueprints.auth import admin_required
from db import query_db, execute_db, get_db_transaction
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# -----------------------------------------------------------------------------
# 1. ADMIN DASHBOARD
# -----------------------------------------------------------------------------
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Execute database queries for real-time KPI metrics
    stats = query_db("""
        SELECT
            (SELECT COUNT(*) FROM students) AS total_students,
            (SELECT COUNT(*) FROM books) AS total_titles,
            (SELECT COALESCE(SUM(total_copies), 0) FROM books) AS total_inventory,
            (SELECT COALESCE(SUM(available_copies), 0) FROM books) AS available_inventory,
            (SELECT COUNT(*) FROM issued_books WHERE status IN ('ISSUED', 'OVERDUE')) AS active_loans,
            (SELECT COUNT(*) FROM issued_books WHERE status = 'OVERDUE' OR (status = 'ISSUED' AND due_date < CURDATE())) AS overdue_loans,
            (SELECT COUNT(*) FROM students WHERE borrowing_permission = 'GRANTED') AS granted_students,
            (SELECT COUNT(*) FROM students WHERE borrowing_permission = 'REVOKED') AS revoked_students,
            (SELECT COUNT(DISTINCT student_id) FROM fines WHERE payment_status = 'UNPAID') AS students_with_fines,
            (SELECT COALESCE(SUM(fine_amount), 0.00) FROM fines WHERE payment_status = 'UNPAID') AS total_unpaid_fines
    """, one=True)

    # Students currently holding 3 books (maximum limit)
    max_borrowers = query_db("""
        SELECT COUNT(*) AS count FROM (
            SELECT student_id FROM issued_books 
            WHERE status IN ('ISSUED', 'OVERDUE') 
            GROUP BY student_id HAVING COUNT(*) >= 3
        ) AS sub
    """, one=True)['count']

    # Recent loan transactions
    recent_issues = query_db("""
        SELECT ib.issue_id, s.roll_number, s.full_name, b.title, ib.issue_date, ib.due_date, ib.status
        FROM issued_books ib
        JOIN students s ON ib.student_id = s.student_id
        JOIN books b ON ib.book_id = b.book_id
        ORDER BY ib.issue_id DESC
        LIMIT 6
    """)

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        max_borrowers=max_borrowers,
        recent_issues=recent_issues
    )

# -----------------------------------------------------------------------------
# 2. STUDENT MANAGEMENT (CRUD)
# -----------------------------------------------------------------------------
@admin_bp.route('/students')
@admin_required
def students():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()

    sql = """
        SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone, s.department, s.borrowing_permission,
               (SELECT COUNT(*) FROM issued_books ib WHERE ib.student_id = s.student_id AND ib.status IN ('ISSUED', 'OVERDUE')) AS active_books,
               (SELECT COALESCE(SUM(f.fine_amount), 0.00) FROM fines f WHERE f.student_id = s.student_id AND f.payment_status = 'UNPAID') AS unpaid_fine
        FROM students s
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (s.roll_number LIKE %s OR s.full_name LIKE %s OR s.email LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if dept:
        sql += " AND s.department = %s"
        params.append(dept)

    sql += " ORDER BY s.roll_number ASC"
    student_list = query_db(sql, params)
    departments = query_db("SELECT DISTINCT department FROM students ORDER BY department ASC")

    return render_template('admin/students.html', students=student_list, departments=departments, search=search, selected_dept=dept)

@admin_bp.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    if request.method == 'POST':
        roll = request.form.get('roll_number', '').strip()
        name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()

        if not all([roll, name, email, phone, department]):
            flash('All fields are required.', 'warning')
            return redirect(url_for('admin.add_student'))

        # Check existing roll or email
        existing = query_db("SELECT student_id FROM students WHERE roll_number = %s OR email = %s", (roll, email), one=True)
        if existing:
            flash('A student with this Roll Number or Email already exists.', 'danger')
            return redirect(url_for('admin.add_student'))

        # Standard password: std + last 3 digits of roll number (e.g., std119)
        pwd_suffix = roll[-3:] if len(roll) >= 3 else roll
        default_pwd = f"std{pwd_suffix}"
        pwd_hash = generate_password_hash(default_pwd)

        try:
            with get_db_transaction() as cursor:
                # 1. Create auth user
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'STUDENT')",
                    (roll, pwd_hash)
                )
                user_id = cursor.lastrowid

                # 2. Create student profile
                cursor.execute(
                    """INSERT INTO students (user_id, roll_number, full_name, email, phone, department, borrowing_permission) 
                       VALUES (%s, %s, %s, %s, %s, %s, 'GRANTED')""",
                    (user_id, roll, name, email, phone, department)
                )

            flash(f'Student {name} ({roll}) created successfully! Default password is: {default_pwd}', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            flash(f'Failed to add student: {str(e)}', 'danger')

    departments = ['CSE', 'IT', 'ECE', 'ME', 'CE', 'Business', 'Applied Sciences']
    return render_template('admin/student_form.html', student=None, departments=departments)

@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    student = query_db("SELECT * FROM students WHERE student_id = %s", (student_id,), one=True)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('admin.students'))

    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()

        try:
            execute_db(
                """UPDATE students 
                   SET full_name = %s, email = %s, phone = %s, department = %s 
                   WHERE student_id = %s""",
                (name, email, phone, department, student_id)
            )
            flash('Student information updated successfully.', 'success')
            return redirect(url_for('admin.students'))
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'danger')

    departments = ['CSE', 'IT', 'ECE', 'ME', 'CE', 'Business', 'Applied Sciences']
    return render_template('admin/student_form.html', student=student, departments=departments)

@admin_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    # Verify no active loans exist
    active_loans = query_db(
        "SELECT COUNT(*) AS count FROM issued_books WHERE student_id = %s AND status IN ('ISSUED', 'OVERDUE')",
        (student_id,),
        one=True
    )['count']

    if active_loans > 0:
        flash('Cannot delete student: The student currently holds active book loans. Please return books first.', 'danger')
        return redirect(url_for('admin.students'))

    # Verify no unpaid fines exist
    unpaid_fines = query_db(
        "SELECT COUNT(*) AS count FROM fines WHERE student_id = %s AND payment_status = 'UNPAID'",
        (student_id,),
        one=True
    )['count']

    if unpaid_fines > 0:
        flash('Cannot delete student: The student has outstanding unpaid fines.', 'danger')
        return redirect(url_for('admin.students'))

    try:
        student = query_db("SELECT user_id FROM students WHERE student_id = %s", (student_id,), one=True)
        if student:
            # Deleting the user will cascade delete the student record
            execute_db("DELETE FROM users WHERE user_id = %s", (student['user_id'],))
            flash('Student record deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete student: {str(e)}', 'danger')

    return redirect(url_for('admin.students'))

@admin_bp.route('/students/view/<int:student_id>')
@admin_required
def view_student(student_id):
    student = query_db("""
        SELECT s.*, u.username,
               (SELECT COUNT(*) FROM issued_books ib WHERE ib.student_id = s.student_id AND ib.status IN ('ISSUED', 'OVERDUE')) AS active_books_count,
               (SELECT COALESCE(SUM(fine_amount), 0.00) FROM fines f WHERE f.student_id = s.student_id AND f.payment_status = 'UNPAID') AS unpaid_fine_amount
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.student_id = %s
    """, (student_id,), one=True)

    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))

    loans = query_db("""
        SELECT ib.*, b.title, b.isbn 
        FROM issued_books ib 
        JOIN books b ON ib.book_id = b.book_id 
        WHERE ib.student_id = %s 
        ORDER BY ib.issue_id DESC
    """, (student_id,))

    fines = query_db("""
        SELECT f.*, b.title, ib.issue_date, ib.return_date 
        FROM fines f 
        JOIN issued_books ib ON f.issue_id = ib.issue_id 
        JOIN books b ON ib.book_id = b.book_id 
        WHERE f.student_id = %s 
        ORDER BY f.fine_id DESC
    """, (student_id,))

    return render_template('admin/student_detail.html', student=student, loans=loans, fines=fines)

# -----------------------------------------------------------------------------
# 3. BOOK MANAGEMENT (CRUD)
# -----------------------------------------------------------------------------
@admin_bp.route('/books')
@admin_required
def books():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '').strip()

    sql = """
        SELECT b.book_id, b.isbn, b.title, c.category_name, b.total_copies, b.available_copies, 
               b.edition, b.publish_year,
               GROUP_CONCAT(a.author_name SEPARATOR ', ') AS authors
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (b.title LIKE %s OR b.isbn LIKE %s OR a.author_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if category_id:
        sql += " AND b.category_id = %s"
        params.append(category_id)

    sql += " GROUP BY b.book_id ORDER BY b.title ASC"
    book_list = query_db(sql, params)
    categories = query_db("SELECT * FROM categories ORDER BY category_name ASC")

    return render_template('admin/books.html', books=book_list, categories=categories, search=search, selected_cat=category_id)

@admin_bp.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        isbn = request.form.get('isbn', '').strip()
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id')
        total_copies = int(request.form.get('total_copies', 1))
        edition = request.form.get('edition', '').strip()
        publish_year = request.form.get('publish_year') or None
        selected_authors = request.form.getlist('author_ids')

        if not isbn or not title or not category_id:
            flash('ISBN, Title, and Category are required.', 'warning')
            return redirect(url_for('admin.add_book'))

        # Check existing ISBN
        existing = query_db("SELECT book_id FROM books WHERE isbn = %s", (isbn,), one=True)
        if existing:
            flash('A book with this ISBN already exists.', 'danger')
            return redirect(url_for('admin.add_book'))

        try:
            with get_db_transaction() as cursor:
                # Insert book (initially available_copies = total_copies)
                cursor.execute(
                    """INSERT INTO books (isbn, title, category_id, total_copies, available_copies, edition, publish_year) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (isbn, title, category_id, total_copies, total_copies, edition, publish_year)
                )
                book_id = cursor.lastrowid

                # Link authors in junction table
                for author_id in selected_authors:
                    cursor.execute(
                        "INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)",
                        (book_id, int(author_id))
                    )

            flash(f"Book '{title}' added to catalog successfully!", 'success')
            return redirect(url_for('admin.books'))
        except Exception as e:
            flash(f'Failed to add book: {str(e)}', 'danger')

    categories = query_db("SELECT * FROM categories ORDER BY category_name ASC")
    authors = query_db("SELECT * FROM authors ORDER BY author_name ASC")
    return render_template('admin/book_form.html', book=None, categories=categories, authors=authors, book_author_ids=[])

@admin_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book = query_db("SELECT * FROM books WHERE book_id = %s", (book_id,), one=True)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('admin.books'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id')
        total_copies = int(request.form.get('total_copies', 1))
        edition = request.form.get('edition', '').strip()
        publish_year = request.form.get('publish_year') or None
        selected_authors = request.form.getlist('author_ids')

        # Check currently active loans for this book
        active_loans = query_db(
            "SELECT COUNT(*) AS count FROM issued_books WHERE book_id = %s AND status IN ('ISSUED', 'OVERDUE')",
            (book_id,),
            one=True
        )['count']

        if total_copies < active_loans:
            flash(f"Cannot set total copies to {total_copies}: There are currently {active_loans} copies on active loan.", 'danger')
            return redirect(url_for('admin.edit_book', book_id=book_id))

        new_available = total_copies - active_loans

        try:
            with get_db_transaction() as cursor:
                cursor.execute(
                    """UPDATE books 
                       SET title = %s, category_id = %s, total_copies = %s, available_copies = %s, edition = %s, publish_year = %s 
                       WHERE book_id = %s""",
                    (title, category_id, total_copies, new_available, edition, publish_year, book_id)
                )

                # Refresh authors junction
                cursor.execute("DELETE FROM book_authors WHERE book_id = %s", (book_id,))
                for author_id in selected_authors:
                    cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)", (book_id, int(author_id)))

            flash('Book details updated successfully.', 'success')
            return redirect(url_for('admin.books'))
        except Exception as e:
            flash(f'Failed to update book: {str(e)}', 'danger')

    categories = query_db("SELECT * FROM categories ORDER BY category_name ASC")
    authors = query_db("SELECT * FROM authors ORDER BY author_name ASC")
    book_authors = query_db("SELECT author_id FROM book_authors WHERE book_id = %s", (book_id,))
    book_author_ids = [ba['author_id'] for ba in book_authors]

    return render_template('admin/book_form.html', book=book, categories=categories, authors=authors, book_author_ids=book_author_ids)

@admin_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    # Enforce rule: cannot delete if copies are currently issued
    active_loans = query_db(
        "SELECT COUNT(*) AS count FROM issued_books WHERE book_id = %s AND status IN ('ISSUED', 'OVERDUE')",
        (book_id,),
        one=True
    )['count']

    if active_loans > 0:
        flash(f'Cannot delete book: {active_loans} copy/copies are currently issued to students.', 'danger')
        return redirect(url_for('admin.books'))

    try:
        execute_db("DELETE FROM books WHERE book_id = %s", (book_id,))
        flash('Book deleted from catalog successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete book: {str(e)}', 'danger')

    return redirect(url_for('admin.books'))

# -----------------------------------------------------------------------------
# 4. AUTHOR MANAGEMENT
# -----------------------------------------------------------------------------
@admin_bp.route('/authors')
@admin_required
def authors():
    authors_list = query_db("""
        SELECT a.author_id, a.author_name, a.biography,
               COUNT(ba.book_id) AS book_count
        FROM authors a
        LEFT JOIN book_authors ba ON a.author_id = ba.author_id
        GROUP BY a.author_id
        ORDER BY a.author_name ASC
    """)
    return render_template('admin/authors.html', authors=authors_list)

@admin_bp.route('/authors/add', methods=['POST'])
@admin_required
def add_author():
    name = request.form.get('author_name', '').strip()
    bio = request.form.get('biography', '').strip()
    if name:
        execute_db("INSERT INTO authors (author_name, biography) VALUES (%s, %s)", (name, bio))
        flash(f"Author '{name}' added successfully.", 'success')
    return redirect(url_for('admin.authors'))

@admin_bp.route('/authors/delete/<int:author_id>', methods=['POST'])
@admin_required
def delete_author(author_id):
    try:
        execute_db("DELETE FROM authors WHERE author_id = %s", (author_id,))
        flash('Author deleted successfully.', 'success')
    except Exception as e:
        flash(f'Cannot delete author: {str(e)}', 'danger')
    return redirect(url_for('admin.authors'))

# -----------------------------------------------------------------------------
# 5. CATEGORY MANAGEMENT
# -----------------------------------------------------------------------------
@admin_bp.route('/categories')
@admin_required
def categories():
    cats = query_db("""
        SELECT c.category_id, c.category_name, c.description,
               COUNT(b.book_id) AS book_count
        FROM categories c
        LEFT JOIN books b ON c.category_id = b.category_id
        GROUP BY c.category_id
        ORDER BY c.category_name ASC
    """)
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('category_name', '').strip()
    desc = request.form.get('description', '').strip()
    if name:
        try:
            execute_db("INSERT INTO categories (category_name, description) VALUES (%s, %s)", (name, desc))
            flash(f"Category '{name}' added.", 'success')
        except Exception as e:
            flash(f"Error adding category: {str(e)}", 'danger')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    try:
        execute_db("DELETE FROM categories WHERE category_id = %s", (category_id,))
        flash('Category deleted successfully.', 'success')
    except Exception as e:
        flash(f'Cannot delete category: Contains associated books.', 'danger')
    return redirect(url_for('admin.categories'))

# -----------------------------------------------------------------------------
# 6. BORROWING PERMISSION MANAGEMENT (CRITICAL FEATURE)
# -----------------------------------------------------------------------------
@admin_bp.route('/permissions')
@admin_required
def permissions():
    search = request.args.get('search', '').strip()
    perm_filter = request.args.get('permission', '').strip()

    sql = """
        SELECT s.student_id, s.roll_number, s.full_name, s.department, s.borrowing_permission,
               (SELECT COUNT(*) FROM issued_books ib WHERE ib.student_id = s.student_id AND ib.status IN ('ISSUED', 'OVERDUE')) AS active_books,
               (SELECT COALESCE(SUM(f.fine_amount), 0.00) FROM fines f WHERE f.student_id = s.student_id AND f.payment_status = 'UNPAID') AS unpaid_fine
        FROM students s
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (s.roll_number LIKE %s OR s.full_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    if perm_filter in ('GRANTED', 'REVOKED'):
        sql += " AND s.borrowing_permission = %s"
        params.append(perm_filter)

    sql += " ORDER BY s.roll_number ASC"
    student_list = query_db(sql, params)

    return render_template('admin/permissions.html', students=student_list, search=search, perm_filter=perm_filter)

@admin_bp.route('/permissions/update/<int:student_id>', methods=['POST'])
@admin_required
def update_permission(student_id):
    action = request.form.get('action') # 'GRANT' or 'REVOKE'
    target_status = 'GRANTED' if action == 'GRANT' else 'REVOKED'

    # Direct database UPDATE query executing on MySQL
    execute_db(
        "UPDATE students SET borrowing_permission = %s WHERE student_id = %s",
        (target_status, student_id)
    )

    student = query_db("SELECT roll_number, full_name FROM students WHERE student_id = %s", (student_id,), one=True)
    if student:
        flash(f"Borrowing permission for {student['full_name']} ({student['roll_number']}) updated to: {target_status}", 'success')

    return redirect(url_for('admin.permissions'))

# -----------------------------------------------------------------------------
# 7. FINES MANAGEMENT
# -----------------------------------------------------------------------------
@admin_bp.route('/fines')
@admin_required
def fines():
    status_filter = request.args.get('status', 'UNPAID')
    sql = """
        SELECT f.fine_id, f.fine_amount, f.payment_status, f.paid_date,
               s.student_id, s.roll_number, s.full_name, s.department,
               b.title AS book_title, ib.issue_date, ib.return_date, ib.due_date
        FROM fines f
        JOIN students s ON f.student_id = s.student_id
        JOIN issued_books ib ON f.issue_id = ib.issue_id
        JOIN books b ON ib.book_id = b.book_id
    """
    params = []
    if status_filter in ('UNPAID', 'PAID'):
        sql += " WHERE f.payment_status = %s"
        params.append(status_filter)

    sql += " ORDER BY f.fine_id DESC"
    fines_list = query_db(sql, params)

    total_unpaid = query_db("SELECT COALESCE(SUM(fine_amount), 0.00) AS total FROM fines WHERE payment_status = 'UNPAID'", one=True)['total']
    total_collected = query_db("SELECT COALESCE(SUM(fine_amount), 0.00) AS total FROM fines WHERE payment_status = 'PAID'", one=True)['total']

    return render_template('admin/fines.html', fines=fines_list, status_filter=status_filter, total_unpaid=total_unpaid, total_collected=total_collected)

@admin_bp.route('/fines/pay/<int:fine_id>', methods=['POST'])
@admin_required
def pay_fine(fine_id):
    execute_db(
        "UPDATE fines SET payment_status = 'PAID', paid_date = NOW() WHERE fine_id = %s",
        (fine_id,)
    )
    flash(f"Fine #{fine_id} marked as PAID successfully.", 'success')
    return redirect(url_for('admin.fines'))

# -----------------------------------------------------------------------------
# 8. ANALYTICAL REPORTS & ADVANCED SQL DEMOS
# -----------------------------------------------------------------------------
@admin_bp.route('/reports')
@admin_required
def reports():
    # Report 1: Top 5 Most Issued Books
    top_books = query_db("""
        SELECT b.book_id, b.title, c.category_name, COUNT(ib.issue_id) AS borrow_count
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN issued_books ib ON b.book_id = ib.book_id
        GROUP BY b.book_id, b.title, c.category_name
        ORDER BY borrow_count DESC
        LIMIT 5
    """)

    # Report 2: Students holding 3 books (Max limit reached)
    max_limit_students = query_db("""
        SELECT s.roll_number, s.full_name, s.department, COUNT(ib.issue_id) AS active_books
        FROM students s
        JOIN issued_books ib ON s.student_id = ib.student_id
        WHERE ib.status IN ('ISSUED', 'OVERDUE')
        GROUP BY s.student_id, s.roll_number, s.full_name, s.department
        HAVING COUNT(ib.issue_id) >= 3
    """)

    # Report 3: Students who have never borrowed any book (Subquery demonstration)
    non_borrowers = query_db("""
        SELECT s.roll_number, s.full_name, s.department, s.borrowing_permission
        FROM students s
        WHERE s.student_id NOT IN (SELECT DISTINCT student_id FROM issued_books)
        ORDER BY s.roll_number ASC
    """)

    # Report 4: Category Distribution
    category_dist = query_db("""
        SELECT c.category_name, COUNT(b.book_id) AS title_count, COALESCE(SUM(b.total_copies), 0) AS copy_count
        FROM categories c
        LEFT JOIN books b ON c.category_id = b.category_id
        GROUP BY c.category_id, c.category_name
        ORDER BY copy_count DESC
    """)

    # Report 5: Current Overdue Loans
    overdue_loans = query_db("""
        SELECT ib.issue_id, s.roll_number, s.full_name, b.title, ib.issue_date, ib.due_date,
               DATEDIFF(CURDATE(), ib.due_date) AS days_overdue,
               DATEDIFF(CURDATE(), ib.due_date) * 5.00 AS fine_estimate
        FROM issued_books ib
        JOIN students s ON ib.student_id = s.student_id
        JOIN books b ON ib.book_id = b.book_id
        WHERE ib.status IN ('ISSUED', 'OVERDUE') AND ib.due_date < CURDATE()
        ORDER BY days_overdue DESC
    """)

    return render_template(
        'admin/reports.html',
        top_books=top_books,
        max_limit_students=max_limit_students,
        non_borrowers=non_borrowers,
        category_dist=category_dist,
        overdue_loans=overdue_loans
    )
