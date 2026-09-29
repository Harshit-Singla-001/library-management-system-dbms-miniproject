import time
import mysql.connector
from mysql.connector import pooling, Error
from config import Config
from contextlib import contextmanager
from flask import has_request_context, g

# Initialize MySQL Connection Pool
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="lms_pool",
        pool_size=5,
        pool_reset_session=True,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )
except Error as e:
    db_pool = None
    print(f"Warning: Failed to create connection pool: {e}")

def get_db_connection():
    """Retrieve a connection from pool or fallback to direct connection."""
    global db_pool
    if db_pool:
        try:
            return db_pool.get_connection()
        except Error:
            pass
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )

def analyze_sql_query(sql_text):
    """
    Returns (classification, description, date_note) for an executed SQL query.
    Classifications: DQL, DML, DCL, TCL.
    """
    upper_sql = sql_text.upper() if sql_text else ""

    # 1. Classification (DQL, DML, DCL, TCL)
    if upper_sql.startswith("START TRANSACTION") or upper_sql.startswith("COMMIT") or upper_sql.startswith("ROLLBACK"):
        classification = "TCL (Transaction Control Language)"
    elif upper_sql.startswith("GRANT") or upper_sql.startswith("REVOKE"):
        classification = "DCL (Data Control Language)"
    elif upper_sql.startswith("UPDATE") and "BORROWING_PERMISSION" in upper_sql:
        classification = "DML / DCL (Privilege & Access Control)"
    elif upper_sql.startswith("SELECT"):
        classification = "DQL (Data Query Language)"
    elif upper_sql.startswith("INSERT") or upper_sql.startswith("UPDATE") or upper_sql.startswith("DELETE"):
        classification = "DML (Data Manipulation Language)"
    elif upper_sql.startswith("CREATE") or upper_sql.startswith("ALTER") or upper_sql.startswith("DROP"):
        classification = "DDL (Data Definition Language)"
    else:
        classification = "SQL Command"

    # 2. Personalized Description
    if "START TRANSACTION" in upper_sql:
        desc = "TCL: Initiates an atomic multi-statement database transaction to guarantee ACID consistency."
    elif "COMMIT" in upper_sql:
        desc = "TCL: Commits transaction changes permanently to disk, completing ACID durability."
    elif "ROLLBACK" in upper_sql:
        desc = "TCL: Rolls back all uncommitted transaction changes to restore previous valid state."
    elif "FOR UPDATE" in upper_sql:
        desc = "Concurrency Control: Applies exclusive row-level lock (FOR UPDATE) to prevent concurrent checkout race conditions."
    elif "(SELECT COUNT(*) FROM STUDENTS) AS TOTAL_STUDENTS" in upper_sql or "TOTAL_INVENTORY" in upper_sql:
        desc = "KPI Aggregation: Computes high-level system metrics including registered students, titles, copy counts, active loans, and overdue counts."
    elif "FROM STUDENTS S" in upper_sql and ("ACTIVE_BOOKS" in upper_sql or "ACTIVE_BOOKS_COUNT" in upper_sql) and ("UNPAID_FINE" in upper_sql or "UNPAID_FINE_AMOUNT" in upper_sql):
        desc = "Student Profile Query: Retrieves student details while computing real-time active loans count and pending fine dues."
    elif "HAVING COUNT(*) >= 3" in upper_sql or "HAVING COUNT(IB.ISSUE_ID) >= 3" in upper_sql:
        desc = "Limitation Check: Identifies students who have reached the maximum threshold of 3 active loans using HAVING aggregation."
    elif "NOT IN (SELECT DISTINCT STUDENT_ID FROM ISSUED_BOOKS)" in upper_sql:
        desc = "Nested Subquery Analysis: Finds students who have never borrowed any library resources."
    elif "BORROW_COUNT" in upper_sql and "ORDER BY BORROW_COUNT DESC" in upper_sql:
        desc = "Popularity Index: Ranks books by total historical borrow count using LEFT JOIN and GROUP BY."
    elif "GROUP BY C.CATEGORY_ID" in upper_sql and "COUNT(B.BOOK_ID)" in upper_sql:
        desc = "Category Aggregation: Groups book inventory by genre/category to display distribution and physical copy totals."
    elif "FROM ISSUED_BOOKS IB" in upper_sql and "ORDER BY IB.ISSUE_ID DESC" in upper_sql:
        desc = "Recent Circulation Feed: Retrieves latest loan checkouts joined across students and books."
    elif "FROM ISSUED_BOOKS IB" in upper_sql and "STATUS IN ('ISSUED', 'OVERDUE')" in upper_sql and "ORDER BY DAYS_OVERDUE" in upper_sql:
        desc = "Overdue Audit: Retrieves loans that have exceeded the 14-day due date along with dynamic fine calculations."
    elif "FROM ISSUED_BOOKS IB" in upper_sql and "STATUS IN ('ISSUED', 'OVERDUE')" in upper_sql and ("STUDENTS S" in upper_sql or "WHERE S.ROLL_NUMBER" in upper_sql or "IB.STUDENT_ID" in upper_sql):
        desc = "Active Loans Query: Retrieves currently borrowed books for this student with real-time due dates and days remaining."
    elif "FROM ISSUED_BOOKS IB" in upper_sql and "STATUS = 'RETURNED'" in upper_sql:
        desc = "Loan History Query: Retrieves past returned books joined with check-in timestamps and settled fines."
    elif "FROM STUDENTS S" in upper_sql and "WHERE 1=1" in upper_sql:
        desc = "Student Directory Query: Fetches student records with dynamic roll number, name, and department search filters."
    elif "FROM BOOKS B" in upper_sql and "GROUP_CONCAT" in upper_sql:
        desc = "Catalog Query: Searches book collection joined with categories, authors, and real-time shelf copy availability."
    elif "FROM BOOKS B" in upper_sql and "WHERE 1=1" in upper_sql:
        desc = "Book Inventory Query: Searches books with category joins and copy tracking."
    elif "FROM AUTHORS A" in upper_sql and "BOOK_COUNT" in upper_sql:
        desc = "Author Directory Query: Fetches author profiles joined with book_authors junction table to aggregate published titles count."
    elif "FROM CATEGORIES C" in upper_sql and "BOOK_COUNT" in upper_sql:
        desc = "Category Taxonomy Query: Fetches academic categories joined with book catalog to compute subject distribution."
    elif "SELECT DISTINCT DEPARTMENT FROM STUDENTS" in upper_sql:
        desc = "Department Filter Query: Retrieves unique institutional departments for directory filtering."
    elif "FROM CATEGORIES" in upper_sql and "ORDER BY CATEGORY_NAME" in upper_sql:
        desc = "Category Options Query: Fetches alphabetical category taxonomy to populate catalog dropdown filters."
    elif "FROM FINES" in upper_sql and "SUM(FINE_AMOUNT)" in upper_sql and "PAYMENT_STATUS = 'UNPAID'" in upper_sql:
        desc = "Institutional Unpaid Dues: Computes cumulative pending fine revenue across all student accounts."
    elif "FROM FINES" in upper_sql and "SUM(FINE_AMOUNT)" in upper_sql and "PAYMENT_STATUS = 'PAID'" in upper_sql:
        desc = "Institutional Settled Dues: Computes cumulative penalty revenue successfully settled and collected."
    elif "FROM ISSUED_BOOKS IB" in upper_sql and "OVERDUE_DAYS" in upper_sql:
        desc = "Return Eligibility Query: Retrieves active loans for check-in with dynamic overdue days and fine assessments."
    elif "FROM FINES F" in upper_sql and "JOIN ISSUED_BOOKS" in upper_sql and ("STUDENTS S" in upper_sql or "S.ROLL_NUMBER" in upper_sql):
        desc = "Personal Fine Ledger: Retrieves itemized penalty records and settlement status for this student."
    elif "FROM BOOKS B" in upper_sql and "ALREADY_ISSUED" in upper_sql:
        desc = "Catalog & Eligibility Query: Searches catalog joined with student active loans to detect already-held copies."
    elif "FROM FINES F" in upper_sql and "WHERE 1=1" in upper_sql:
        desc = "Fine Ledger Query: Fetches fine records joined with student and book loan details."
    elif "FROM FINES F" in upper_sql and "PAYMENT_STATUS = 'UNPAID'" in upper_sql:
        desc = "Unpaid Dues Query: Calculates outstanding fine amounts requiring student settlement."
    elif "INSERT INTO ISSUED_BOOKS" in upper_sql:
        desc = "Checkout Transaction: Creates an active loan record assigning a 14-day due date."
    elif "UPDATE BOOKS SET AVAILABLE_COPIES = AVAILABLE_COPIES - 1" in upper_sql:
        desc = "Inventory Decrement: Decrements physical book copies available on the shelf."
    elif "UPDATE BOOKS SET AVAILABLE_COPIES = AVAILABLE_COPIES + 1" in upper_sql:
        desc = "Inventory Increment: Restores physical book copies upon return."
    elif "UPDATE ISSUED_BOOKS SET RETURN_DATE" in upper_sql:
        desc = "Check-in Transaction: Updates loan status to RETURNED and records current return date."
    elif "UPDATE STUDENTS SET BORROWING_PERMISSION" in upper_sql:
        desc = "Privilege Update: Modifies student borrowing status between GRANTED and REVOKED."
    elif "UPDATE FINES SET PAYMENT_STATUS = 'PAID'" in upper_sql:
        desc = "Fine Settlement: Clears fine dues and records timestamp."
    elif "INSERT INTO FINES" in upper_sql:
        desc = "Fine Assessment: Calculates and inserts an overdue fine based on late return days."
    elif upper_sql.startswith("SELECT"):
        desc = "Data Query: Retrieves records from database tables based on specified query criteria."
    elif upper_sql.startswith("UPDATE"):
        desc = "Data Update: Updates existing table rows with new values."
    elif upper_sql.startswith("INSERT"):
        desc = "Data Insertion: Inserts new record into the database table."
    elif upper_sql.startswith("DELETE"):
        desc = "Data Deletion: Removes specified record from the database table."
    else:
        desc = "Executes database operation."

    # 3. Date utility check
    has_date_utils = any(k in upper_sql for k in ["CURDATE", "DATEDIFF", "DATE_ADD", "NOW", "INTERVAL"])
    date_note = "Date Utility: Built-in date functions (CURDATE, DATEDIFF, NOW) compute real-time loan deadlines and overdue fines dynamically." if has_date_utils else None

    return classification, desc, date_note

def record_query(cursor, query=None, params=None, duration=None, error=None):
    """Log executed SQL query with real bound parameters to current Flask request context."""
    if not has_request_context():
        return
    if not hasattr(g, 'sql_queries'):
        g.sql_queries = []

    sql_text = None
    try:
        if cursor and hasattr(cursor, 'statement') and cursor.statement:
            sql_text = cursor.statement
            if isinstance(sql_text, bytes):
                sql_text = sql_text.decode('utf-8', errors='replace')
        elif cursor and hasattr(cursor, '_executed') and cursor._executed:
            sql_text = cursor._executed
            if isinstance(sql_text, bytes):
                sql_text = sql_text.decode('utf-8', errors='replace')
    except Exception:
        pass

    if not sql_text and query:
        sql_text = str(query).strip()
        if params is not None and params != () and params != []:
            sql_text += f"\n-- Bound Parameters: {repr(params)}"

    sql_text = sql_text.strip() if sql_text else str(query or "").strip()

    stmt_type = "SQL"
    first_word = sql_text.split()[0].upper() if sql_text else "SQL"
    if first_word in ("SELECT", "INSERT", "UPDATE", "DELETE", "START", "COMMIT", "ROLLBACK", "SET", "SHOW", "DESCRIBE"):
        stmt_type = first_word

    classification, description, date_note = analyze_sql_query(sql_text)

    g.sql_queries.append({
        'query': sql_text,
        'type': stmt_type,
        'classification': classification,
        'description': description,
        'date_note': date_note,
        'duration_ms': round(duration * 1000, 2) if duration is not None else 0.0,
        'error': error
    })

class MonitoredCursor:
    """Cursor wrapper that transparently captures executed SQL statements with bound parameters."""
    def __init__(self, cursor):
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __iter__(self):
        return iter(self._cursor)

    def execute(self, operation, params=None, *args, **kwargs):
        start = time.perf_counter()
        try:
            res = self._cursor.execute(operation, params, *args, **kwargs)
            duration = time.perf_counter() - start
            record_query(self._cursor, operation, params, duration)
            return res
        except Exception as e:
            duration = time.perf_counter() - start
            record_query(self._cursor, operation, params, duration, error=str(e))
            raise e

    def executemany(self, operation, seq_params, *args, **kwargs):
        start = time.perf_counter()
        try:
            res = self._cursor.executemany(operation, seq_params, *args, **kwargs)
            duration = time.perf_counter() - start
            record_query(self._cursor, operation, seq_params, duration)
            return res
        except Exception as e:
            duration = time.perf_counter() - start
            record_query(self._cursor, operation, seq_params, duration, error=str(e))
            raise e

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return dictionary results."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        start = time.perf_counter()
        try:
            cursor.execute(query, args)
            duration = time.perf_counter() - start
            record_query(cursor, query, args, duration)
        except Exception as e:
            duration = time.perf_counter() - start
            record_query(cursor, query, args, duration, error=str(e))
            raise e
        rv = cursor.fetchall()
        cursor.close()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), commit=True):
    """Execute an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        start = time.perf_counter()
        try:
            cursor.execute(query, args)
            duration = time.perf_counter() - start
            record_query(cursor, query, args, duration)
        except Exception as e:
            duration = time.perf_counter() - start
            record_query(cursor, query, args, duration, error=str(e))
            raise e
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        cursor.close()
        if commit:
            conn.commit()
        return {'lastrowid': last_id, 'rowcount': row_count}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@contextmanager
def get_db_transaction():
    """
    Context manager for atomic multi-statement database transactions (TCL).
    Automatically commits on success or rolls back on exception.
    """
    conn = get_db_connection()
    conn.start_transaction()
    record_query(None, "START TRANSACTION", None, 0.0)
    raw_cursor = conn.cursor(dictionary=True)
    cursor = MonitoredCursor(raw_cursor)
    try:
        yield cursor
        conn.commit()
        record_query(None, "COMMIT", None, 0.0)
    except Exception as e:
        conn.rollback()
        record_query(None, "ROLLBACK", None, 0.0, error=str(e))
        raise e
    finally:
        raw_cursor.close()
        conn.close()
