import os
import re
import time
import datetime
from decimal import Decimal
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import mysql.connector
from mysql.connector import pooling, Error
from flask import has_request_context, g
from config import Config

# Global database system state
DB_MODE = 'SQLITE'  # 'DUAL' (MySQL + SQLite synced) or 'SQLITE' (SQLite primary)
db_pool = None
_db_initialized = False

# -----------------------------------------------------------------------------
# 1. SQLITE ROW FACTORY & DATE TYPE ADAPTERS
# -----------------------------------------------------------------------------
def sqlite_dict_factory(cursor, row):
    """
    Row factory that returns standard mutable Python dicts with column names.
    Automatically parses ISO date/datetime strings into Python date/datetime objects
    to ensure full compatibility with application logic across both engines.
    """
    fields = [col[0] for col in cursor.description]
    res = {}
    for col, val in zip(fields, row):
        lower_col = col.lower()
        if isinstance(val, str):
            if lower_col.endswith('_date') or lower_col in ('due_date', 'issue_date', 'return_date', 'date'):
                try:
                    val = datetime.date.fromisoformat(val.split()[0])
                except Exception:
                    pass
            elif lower_col.endswith('_at') or lower_col in ('paid_date', 'created_at', 'timestamp'):
                try:
                    val = datetime.datetime.fromisoformat(val)
                except Exception:
                    try:
                        val = datetime.date.fromisoformat(val.split()[0])
                    except Exception:
                        pass
        res[col] = val
    return res

def adapt_query_for_sqlite(sql):
    """
    Adapts MySQL-specific SQL statements to SQLite-compatible syntax:
    - Removes 'FOR UPDATE' row-locking syntax (unsupported/unneeded in SQLite).
    - Converts GROUP_CONCAT(col SEPARATOR ', ') to GROUP_CONCAT(col, ', ').
    - Converts DATE_ADD(date, INTERVAL n DAY) to date(date, '+' || n || ' day').
    - Translates '%s' parameterized placeholders to '?'.
    """
    if not sql:
        return sql
    # 1. Strip FOR UPDATE
    s = re.sub(r'\s+FOR\s+UPDATE\b', '', sql, flags=re.IGNORECASE)
    # 2. GROUP_CONCAT(col SEPARATOR ', ') -> GROUP_CONCAT(col, ', ')
    s = re.sub(r'GROUP_CONCAT\s*\(\s*([^)]+?)\s+SEPARATOR\s+([^\)]+?)\s*\)', r'GROUP_CONCAT(\1, \2)', s, flags=re.IGNORECASE)
    # 3. DATE_ADD(date, INTERVAL n DAY) -> date(date, '+' || n || ' day')
    s = re.sub(r'DATE_ADD\s*\(\s*(CURDATE\(\)|NOW\(\)|[^\s,]+)\s*,\s*INTERVAL\s+(%s|\?)\s+DAY\s*\)', r"date(\1, '+' || \2 || ' day')", s, flags=re.IGNORECASE)
    # 4. Replace %s placeholder with ?
    s = re.sub(r'%s', '?', s)
    return s

def adapt_params_for_sqlite(params):
    """Converts parameter types (date, datetime, Decimal) to SQLite-native formats."""
    if params is None:
        return ()
    if isinstance(params, (list, tuple)):
        new_params = []
        for p in params:
            if isinstance(p, (datetime.date, datetime.datetime)):
                new_params.append(p.isoformat())
            elif isinstance(p, Decimal):
                new_params.append(float(p))
            else:
                new_params.append(p)
        return tuple(new_params)
    return params

def get_sqlite_connection():
    """Create and return a configured SQLite connection with custom functions."""
    sqlite_path = Config.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)), exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite_dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")

    # Register MySQL-compatible SQL functions in SQLite
    conn.create_function('CURDATE', 0, lambda: datetime.date.today().isoformat())
    conn.create_function('NOW', 0, lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def sqlite_datediff(d1, d2):
        if not d1 or not d2:
            return 0
        if isinstance(d1, str):
            d1 = datetime.date.fromisoformat(d1.split()[0])
        elif isinstance(d1, datetime.datetime):
            d1 = d1.date()
        if isinstance(d2, str):
            d2 = datetime.date.fromisoformat(d2.split()[0])
        elif isinstance(d2, datetime.datetime):
            d2 = d2.date()
        return (d1 - d2).days

    conn.create_function('DATEDIFF', 2, sqlite_datediff)
    return conn

# -----------------------------------------------------------------------------
# 2. SCHEMA AND SYNCHRONIZATION ENGINES
# -----------------------------------------------------------------------------
SQLITE_TABLE_SCHEMAS = [
    """CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE,
        description TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS authors (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT NOT NULL,
        biography TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        roll_number TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        department TEXT NOT NULL,
        borrowing_permission TEXT NOT NULL DEFAULT 'GRANTED',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        total_copies INTEGER NOT NULL DEFAULT 1,
        available_copies INTEGER NOT NULL DEFAULT 1,
        edition TEXT,
        publish_year INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    )""",
    """CREATE TABLE IF NOT EXISTS book_authors (
        book_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        PRIMARY KEY (book_id, author_id),
        FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors (author_id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS issued_books (
        issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'ISSUED',
        remarks TEXT,
        FOREIGN KEY (student_id) REFERENCES students (student_id),
        FOREIGN KEY (book_id) REFERENCES books (book_id)
    )""",
    """CREATE TABLE IF NOT EXISTS fines (
        fine_id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL UNIQUE,
        student_id INTEGER NOT NULL,
        fine_amount REAL NOT NULL DEFAULT 0.00,
        payment_status TEXT NOT NULL DEFAULT 'UNPAID',
        paid_date TEXT,
        FOREIGN KEY (issue_id) REFERENCES issued_books (issue_id),
        FOREIGN KEY (student_id) REFERENCES students (student_id)
    )"""
]

TABLE_SYNC_ORDER = ['users', 'categories', 'authors', 'students', 'books', 'book_authors', 'issued_books', 'fines']

def init_sqlite_tables_if_needed(sconn):
    """Ensure SQLite schema exists."""
    scur = sconn.cursor()
    for stmt in SQLITE_TABLE_SCHEMAS:
        scur.execute(stmt)
    sconn.commit()

def fetch_database_from_sqlite_to_mysql(mconn, sconn):
    """
    Case 3 & Case 1 sync: Creates schema on MySQL if needed and populates
    all tables and records directly from SQLite.
    """
    mcur = mconn.cursor(buffered=True)
    schema_path = Path(__file__).resolve().parent / 'database' / 'schema.sql'
    if schema_path.exists():
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Clean comments and run DDL statements
        clean_lines = [line for line in schema_sql.splitlines() if not line.strip().startswith('--')]
        clean_sql = '\n'.join(clean_lines)
        for raw_stmt in clean_sql.split(';'):
            stmt = raw_stmt.strip()
            if not stmt:
                continue
            first_word = stmt.split()[0].upper()
            if first_word in ('CREATE', 'DROP', 'SET', 'ALTER'):
                if 'DATABASE' in stmt.split()[:3] or 'USE' in stmt.split()[:2]:
                    continue
                try:
                    mcur.execute(stmt)
                except Exception:
                    pass

    # Copy data from SQLite to MySQL
    scur = sconn.cursor()
    mcur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in TABLE_SYNC_ORDER:
        scur.execute(f"SELECT * FROM {table}")
        rows = scur.fetchall()
        if rows:
            cols = list(rows[0].keys())
            col_names = ', '.join([f"`{c}`" for c in cols])
            placeholders = ', '.join(['%s'] * len(cols))
            insert_sql = f"REPLACE INTO `{table}` ({col_names}) VALUES ({placeholders})"
            data = []
            for r in rows:
                vals = []
                for c in cols:
                    v = r[c]
                    if isinstance(v, (datetime.date, datetime.datetime)):
                        v = v.isoformat()
                    vals.append(v)
                data.append(tuple(vals))
            mcur.executemany(insert_sql, data)
    mcur.execute("SET FOREIGN_KEY_CHECKS = 1")
    mconn.commit()
    mcur.close()

def sync_mysql_to_sqlite(mconn, sconn):
    """Seed or update SQLite from MySQL if SQLite is empty or missing data."""
    init_sqlite_tables_if_needed(sconn)
    scur = sconn.cursor()
    mcur = mconn.cursor(dictionary=True, buffered=True)
    scur.execute("PRAGMA foreign_keys = OFF")
    for table in TABLE_SYNC_ORDER:
        mcur.execute(f"SELECT * FROM {table}")
        rows = mcur.fetchall()
        if rows:
            cols = list(rows[0].keys())
            placeholders = ', '.join(['?'] * len(cols))
            col_names = ', '.join(cols)
            insert_sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
            data = []
            for row in rows:
                vals = []
                for c in cols:
                    v = row[c]
                    if hasattr(v, 'isoformat'):
                        v = v.isoformat()
                    if isinstance(v, Decimal):
                        v = float(v)
                    vals.append(v)
                data.append(tuple(vals))
            scur.executemany(insert_sql, data)
    scur.execute("PRAGMA foreign_keys = ON")
    sconn.commit()
    mcur.close()

# -----------------------------------------------------------------------------
# 3. INITIALIZATION & 3-CASE DETECTION
# -----------------------------------------------------------------------------
def init_db_system():
    """
    Detects MySQL server presence and database state:
    Case 1: MySQL server is present & database exists -> DUAL mode (fetch from SQLite, update both).
    Case 2: MySQL server is not present -> SQLITE mode (SQLite as primary).
    Case 3: MySQL server is present but database is missing -> Create DB on MySQL, fetch from SQLite, then DUAL mode.
    """
    global DB_MODE, db_pool, _db_initialized
    if _db_initialized:
        return

    # First, ensure SQLite database exists and has schema
    sconn = get_sqlite_connection()
    init_sqlite_tables_if_needed(sconn)

    # Check if SQLite has existing data
    scur = sconn.cursor()
    scur.execute("SELECT COUNT(*) as count FROM users")
    sqlite_user_count = scur.fetchone()['count']

    # Step 1: Detect if MySQL Server is present
    server_present = False
    database_present = False
    mysql_conn = None

    try:
        # Test connection to MySQL server (without specifying DB first)
        mysql_conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            connection_timeout=2
        )
        server_present = True
    except Exception as e:
        server_present = False
        print(f"[DB System] MySQL server not reachable ({e}).")

    if not server_present:
        # =====================================================================
        # CASE 2: MySQL Server is NOT present -> Set SQLite as PRIMARY
        # =====================================================================
        DB_MODE = 'SQLITE'
        print("=" * 65)
        print("  [DATABASE MODE: CASE 2 - SQLITE PRIMARY]")
        print("  MySQL Server: NOT DETECTED (Server offline or not installed)")
        print(f"  Primary Engine: SQLite ({Config.SQLITE_DB_PATH})")
        print("  Status: All operations will execute against SQLite directly.")
        print("=" * 65)
        sconn.close()
        _db_initialized = True
        return

    # MySQL Server IS present: Check if database exists
    try:
        mcur = mysql_conn.cursor(buffered=True)
        mcur.execute("SHOW DATABASES LIKE %s", (Config.DB_NAME,))
        res = mcur.fetchone()
        database_present = (res is not None)
        mcur.close()
    except Exception:
        database_present = False

    if not database_present:
        # =====================================================================
        # CASE 3: MySQL Server present, but database does NOT exist
        # -> Create database on MySQL and fetch from SQLite
        # =====================================================================
        print("=" * 65)
        print("  [DATABASE MODE: CASE 3 - FETCH FROM SQLITE TO MYSQL]")
        print("  MySQL Server: CONNECTED")
        print(f"  MySQL Database: NOT FOUND ('{Config.DB_NAME}')")
        print("  Action: Creating database on MySQL and fetching tables & data from SQLite...")
        
        mcur = mysql_conn.cursor(buffered=True)
        mcur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        mysql_conn.database = Config.DB_NAME
        mcur.close()

        fetch_database_from_sqlite_to_mysql(mysql_conn, sconn)
        DB_MODE = 'DUAL'
        print(f"  Status: Database '{Config.DB_NAME}' created and synchronized from SQLite successfully!")
        print("  Active Mode: DUAL (MySQL Server + SQLite)")
        print("=" * 65)
    else:
        # =====================================================================
        # CASE 1: MySQL Server is present AND database exists
        # -> Update all operations in SQLite and MySQL (at first fetch/sync from SQLite)
        # =====================================================================
        mysql_conn.database = Config.DB_NAME
        print("=" * 65)
        print("  [DATABASE MODE: CASE 1 - DUAL ENGINE SYNCHRONIZED]")
        print("  MySQL Server: CONNECTED")
        print(f"  MySQL Database: FOUND ('{Config.DB_NAME}')")
        
        # Check if MySQL has tables
        mcur = mysql_conn.cursor(buffered=True)
        mcur.execute("SHOW TABLES")
        mysql_tables = [row[0] for row in mcur.fetchall()]
        mcur.close()

        if len(mysql_tables) < len(TABLE_SYNC_ORDER) and sqlite_user_count > 0:
            print("  Action: Missing tables in MySQL. Fetching database from SQLite...")
            fetch_database_from_sqlite_to_mysql(mysql_conn, sconn)
        elif sqlite_user_count == 0 and len(mysql_tables) >= len(TABLE_SYNC_ORDER):
            print("  Action: SQLite is empty. Seeding SQLite from MySQL...")
            sync_mysql_to_sqlite(mysql_conn, sconn)
        else:
            print("  Action: Both MySQL and SQLite are verified and ready.")

        DB_MODE = 'DUAL'
        print("  Status: Initial state synchronized. Dual-write active for all operations.")
        print("=" * 65)

    if mysql_conn:
        mysql_conn.close()
    sconn.close()

    # Initialize connection pool for MySQL if in DUAL mode
    if DB_MODE == 'DUAL':
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
            print(f"Warning: Failed to create MySQL pool, direct connections will be used: {e}")

    _db_initialized = True

# Helper getters
def get_db_mode():
    global DB_MODE
    return DB_MODE

def get_db_mode_display():
    global DB_MODE
    if DB_MODE == 'DUAL':
        return "MySQL 8.0 & SQLite (Dual Synced)"
    return "SQLite (Primary Standalone Engine)"

def get_mysql_connection():
    """Retrieve a MySQL connection from pool or direct connect."""
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

def get_db_connection():
    """Returns MySQL connection in DUAL mode or SQLite connection in SQLITE mode."""
    init_db_system()
    if DB_MODE == 'DUAL':
        try:
            return get_mysql_connection()
        except Exception:
            return get_sqlite_connection()
    return get_sqlite_connection()

# -----------------------------------------------------------------------------
# 4. SQL QUERY ANALYSIS & TELEMETRY
# -----------------------------------------------------------------------------
def analyze_sql_query(sql_text):
    """
    Returns (classification, description, date_note) for an executed SQL query.
    Classifications: DQL, DML, DCL, TCL, DDL.
    """
    upper_sql = sql_text.upper() if sql_text else ""

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

# -----------------------------------------------------------------------------
# 5. CORE DATABASE APIS: query_db, execute_db, get_db_transaction
# -----------------------------------------------------------------------------
def query_db(query, args=(), one=False):
    """
    Execute a SELECT query and return dictionary results.
    In DUAL mode, reads from MySQL with automatic SQLite fallback.
    In SQLITE mode, reads directly from SQLite.
    """
    init_db_system()
    start = time.perf_counter()

    if DB_MODE == 'DUAL':
        try:
            mconn = get_mysql_connection()
            try:
                mcur = mconn.cursor(dictionary=True)
                mcur.execute(query, args)
                duration = time.perf_counter() - start
                record_query(mcur, query, args, duration)
                rv = mcur.fetchall()
                mcur.close()
                return (rv[0] if rv else None) if one else rv
            finally:
                mconn.close()
        except Exception as e:
            # Fallback to SQLite if MySQL temporarily unavailable
            print(f"[Query Fallback to SQLite] MySQL error: {e}")

    # SQLite query execution
    sconn = get_sqlite_connection()
    try:
        scur = sconn.cursor()
        sqlite_sql = adapt_query_for_sqlite(query)
        sqlite_args = adapt_params_for_sqlite(args)
        scur.execute(sqlite_sql, sqlite_args)
        duration = time.perf_counter() - start
        record_query(None, query, args, duration)
        rv = scur.fetchall()
        scur.close()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        duration = time.perf_counter() - start
        record_query(None, query, args, duration, error=str(e))
        raise e
    finally:
        sconn.close()

def execute_db(query, args=(), commit=True):
    """
    Execute an INSERT, UPDATE, or DELETE query.
    In DUAL mode, updates BOTH MySQL and SQLite.
    In SQLITE mode, updates SQLite.
    """
    init_db_system()
    start = time.perf_counter()
    last_id = None
    row_count = 0

    if DB_MODE == 'DUAL':
        # 1. Execute on MySQL
        mconn = get_mysql_connection()
        try:
            mcur = mconn.cursor(dictionary=True)
            mcur.execute(query, args)
            last_id = mcur.lastrowid
            row_count = mcur.rowcount
            if commit:
                mconn.commit()
            mcur.close()
        except Exception as e:
            mconn.rollback()
            mconn.close()
            duration = time.perf_counter() - start
            record_query(None, query, args, duration, error=str(e))
            raise e
        finally:
            mconn.close()

        # 2. Update all operations in SQLite as well (Dual Write)
        sconn = get_sqlite_connection()
        try:
            scur = sconn.cursor()
            sqlite_sql = adapt_query_for_sqlite(query)
            sqlite_args = adapt_params_for_sqlite(args)
            scur.execute(sqlite_sql, sqlite_args)
            if commit:
                sconn.commit()
            scur.close()
        except Exception as se:
            sconn.rollback()
            print(f"[Warning] Dual-write to SQLite failed: {se}")
        finally:
            sconn.close()

        duration = time.perf_counter() - start
        record_query(None, query, args, duration)
        return {'lastrowid': last_id, 'rowcount': row_count}

    # SQLITE Mode (Primary)
    sconn = get_sqlite_connection()
    try:
        scur = sconn.cursor()
        sqlite_sql = adapt_query_for_sqlite(query)
        sqlite_args = adapt_params_for_sqlite(args)
        scur.execute(sqlite_sql, sqlite_args)
        last_id = scur.lastrowid
        row_count = scur.rowcount
        if commit:
            sconn.commit()
        scur.close()
        duration = time.perf_counter() - start
        record_query(None, query, args, duration)
        return {'lastrowid': last_id, 'rowcount': row_count}
    except Exception as e:
        sconn.rollback()
        duration = time.perf_counter() - start
        record_query(None, query, args, duration, error=str(e))
        raise e
    finally:
        sconn.close()

class DualTransactionCursor:
    """
    Cursor wrapper for DUAL mode transactions.
    Executes all queries on MySQL and mirrors mutating statements (INSERT, UPDATE, DELETE) to SQLite.
    """
    def __init__(self, mcur, scur):
        self._mcur = mcur
        self._scur = scur

    def __getattr__(self, name):
        return getattr(self._mcur, name)

    def __iter__(self):
        return iter(self._mcur)

    def execute(self, operation, params=None, *args, **kwargs):
        start = time.perf_counter()
        try:
            # Execute on MySQL
            res = self._mcur.execute(operation, params, *args, **kwargs)

            # Check if operation mutates data; mirror to SQLite
            op_upper = str(operation).strip().split()[0].upper() if operation else ""
            if op_upper in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
                sqlite_sql = adapt_query_for_sqlite(operation)
                sqlite_args = adapt_params_for_sqlite(params)
                self._scur.execute(sqlite_sql, sqlite_args)

            duration = time.perf_counter() - start
            record_query(self._mcur, operation, params, duration)
            return res
        except Exception as e:
            duration = time.perf_counter() - start
            record_query(self._mcur, operation, params, duration, error=str(e))
            raise e

    def fetchone(self):
        return self._mcur.fetchone()

    def fetchall(self):
        return self._mcur.fetchall()

    def fetchmany(self, size=None):
        return self._mcur.fetchmany(size) if size else self._mcur.fetchmany()

class SQLiteTransactionCursor:
    """
    Cursor wrapper for SQLITE mode transactions.
    Transparently adapts query syntax and parameter formatting.
    """
    def __init__(self, scur):
        self._scur = scur

    def __getattr__(self, name):
        return getattr(self._scur, name)

    def __iter__(self):
        return iter(self._scur)

    def execute(self, operation, params=None, *args, **kwargs):
        start = time.perf_counter()
        try:
            sqlite_sql = adapt_query_for_sqlite(operation)
            sqlite_args = adapt_params_for_sqlite(params)
            res = self._scur.execute(sqlite_sql, sqlite_args)
            duration = time.perf_counter() - start
            record_query(None, operation, params, duration)
            return res
        except Exception as e:
            duration = time.perf_counter() - start
            record_query(None, operation, params, duration, error=str(e))
            raise e

    def fetchone(self):
        return self._scur.fetchone()

    def fetchall(self):
        return self._scur.fetchall()

    def fetchmany(self, size=None):
        return self._scur.fetchmany(size) if size else self._scur.fetchmany()

@contextmanager
def get_db_transaction():
    """
    Context manager for atomic multi-statement database transactions (TCL).
    Guarantees ACID transactions across MySQL and SQLite.
    Automatically commits on success or rolls back on exception.
    """
    init_db_system()

    if DB_MODE == 'DUAL':
        mconn = get_mysql_connection()
        sconn = get_sqlite_connection()

        mconn.start_transaction()
        sconn.execute("BEGIN TRANSACTION")
        record_query(None, "START TRANSACTION", None, 0.0)

        mcur = mconn.cursor(dictionary=True)
        scur = sconn.cursor()
        dual_cursor = DualTransactionCursor(mcur, scur)
        try:
            yield dual_cursor
            mconn.commit()
            sconn.commit()
            record_query(None, "COMMIT", None, 0.0)
        except Exception as e:
            mconn.rollback()
            sconn.rollback()
            record_query(None, "ROLLBACK", None, 0.0, error=str(e))
            raise e
        finally:
            mcur.close()
            scur.close()
            mconn.close()
            sconn.close()
    else:
        # SQLite Only Mode
        sconn = get_sqlite_connection()
        sconn.execute("BEGIN TRANSACTION")
        record_query(None, "START TRANSACTION", None, 0.0)
        scur = sconn.cursor()
        sqlite_cursor = SQLiteTransactionCursor(scur)
        try:
            yield sqlite_cursor
            sconn.commit()
            record_query(None, "COMMIT", None, 0.0)
        except Exception as e:
            sconn.rollback()
            record_query(None, "ROLLBACK", None, 0.0, error=str(e))
            raise e
        finally:
            scur.close()
            sconn.close()

# Auto-initialize database system on import
init_db_system()
