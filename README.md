# Library Management System (DBMS Project)

An academic, college-level **Library Management System** built with **HTML, CSS, JavaScript, Python (Flask), and a standalone Local MySQL Server 8.0**. 

Engineered specifically to demonstrate relational database design, 3NF normalization, transactional integrity (TCL), user privilege management (DCL), and real-world SQL query patterns (joins, groupings, subqueries) without external framework bloat.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, Vanilla CSS3 (Modern, responsive, accessible design), Vanilla JavaScript.
- **Backend**: Python 3.14 + Flask 3.1 + `mysql-connector-python` / `Werkzeug`.
- **Database Architecture**: Intelligent Dual Engine (**MySQL 8.0** and **SQLite 3**):
  - **Case 1 (Server Present & DB Present)**: Dual-Engine Synchronized Mode. Reads from MySQL with instant SQLite fallback; all writes (INSERT, UPDATE, DELETE, Transactions) are synchronized across both engines.
  - **Case 2 (No Server Present)**: SQLite is automatically used as the **PRIMARY** database. The project runs out-of-the-box on any machine without requiring MySQL installation!
  - **Case 3 (Server Present, DB Missing)**: Automatically creates `library_db` on MySQL and fetches/migrates all tables and records directly from SQLite!
- **Environment**: Operates directly in the repository directory `d:\library-management-system`.

---

## 🚀 Quick Start Guide

### Step 1: Install Dependencies
Install all required Python packages via the newly provided `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 2: Database Configuration (Flexible)

The system automatically detects your environment:
- **Zero Configuration (Without MySQL Server)**: You do not need to install or configure MySQL. Simply run the app, and it will immediately use `database/library.db` as the primary database with all 50 students, books, categories, and authors pre-loaded!
- **With MySQL Server**: Ensure your `.env` contains your MySQL credentials:
  ```ini
  DB_HOST=127.0.0.1
  DB_PORT=3306
  DB_NAME=library_db
  DB_USER=root
  DB_PASSWORD=your_mysql_password
  ```
  If `library_db` does not exist on your MySQL server, the application will automatically create it and fetch all tables and data from SQLite.

### Step 3: Run the Application

In your project directory, execute:
```powershell
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 👥 User Roles & Default Credentials

| Role | Username / Student ID | Password | Access Area | Notes |
|---|---|---|---|---|
| **Librarian / Admin** | `admin` | `admin123` | `/admin/dashboard` | Full library catalog & permission control |
| **Student (Clean Profile)** | `2417101` | `std101` | `/student/dashboard` | 0 active books, ₹0 fine, GRANTED |
| **Student (1 Active Book)** | `2417105` | `std105` | `/student/dashboard` | 1 active book, ₹0 fine, GRANTED |
| **Student (Max 3 Books)** | `2417112` | `std112` | `/student/dashboard` | 3 active books, reached limit |
| **Student (Target Example)** | `2417119` | `std119` | `/student/dashboard` | Batch 2, 7-digit ID, custom password |
| **Student (Revoked Status)**| `2417125` | `std125` | `/student/dashboard` | Permission REVOKED by admin |
| **Student (Unpaid Fine)** | `2417130` | `std130` | `/student/dashboard` | Unpaid fine of ₹35.00 |

*(The complete seeded dataset includes exactly 50 students from `2417101` to `2417150` with passwords `std101` to `std150` for realistic presentation.)*

---

## 🏛️ Two-Tier Permission System: Academic Distinction

In your college viva, you can clearly demonstrate **both forms of permission**:

1. **Application-Level Borrowing Permission**:
   - Stored in MySQL: `students.borrowing_permission` (`GRANTED` / `REVOKED`).
   - Admin clicks `[ Grant ]` or `[ Revoke ]` in the Admin UI.
   - Python Flask queries the database on every issue request to enforce library rules.
2. **Database-Level Data Control Language (SQL DCL)**:
   - Managed via native MySQL accounts:
     - `library_admin`: Full database privileges (`ALL PRIVILEGES`).
     - `library_staff`: `SELECT`, `INSERT`, `UPDATE` on tables.
     - `library_readonly`: `SELECT` privileges only.
   - Demonstrated live using `GRANT` and `REVOKE` statements in `database/dcl.sql`.

---

## 📖 7 Core Library Rules & Invariants

1. **Max 3 Books**: A student cannot have more than 3 active (`ISSUED`) loans at any time.
2. **Borrowing Permission**: Student `borrowing_permission` in the database must be `'GRANTED'`.
3. **No Unpaid Fines**: Student cannot issue a book if they have any outstanding fines (`payment_status = 'UNPAID'`).
4. **Copy Availability**: Requested book must have `available_copies > 0`.
5. **No Duplicate Loans**: A student cannot hold multiple active copies of the same book.
6. **Return Process**: Mark issue returned, record return date, increment `available_copies`, and assess fines.
7. **Fine Calculation**: Standard 14-day loan period; ₹5.00/day fine incurred for overdue returns.

---

## 📂 Project Directory Structure

```
d:\library-management-system/
│
├── app.py                      # Flask main entrypoint
├── config.py                   # Loads MySQL credentials securely from .env
├── db.py                       # Connection pooling & ACID transaction helpers
│
├── blueprints/
│   ├── auth.py                 # Login, session management, logout
│   ├── admin.py                # Admin dashboard, student/book CRUD, permissions, reports
│   └── student.py              # Catalog browsing, issue/return book, fines, profile
│
├── templates/
│   ├── base.html               # Base layout with navbar & alerts
│   ├── auth/
│   │   └── login.html          # Clean dual-role login page
│   ├── admin/                  # Admin management templates
│   │   ├── dashboard.html
│   │   ├── students.html
│   │   ├── books.html
│   │   ├── authors.html
│   │   ├── categories.html
│   │   ├── permissions.html
│   │   ├── fines.html
│   │   └── reports.html
│   └── student/                # Student self-service templates
│       ├── dashboard.html
│       ├── books.html
│       ├── issue.html
│       ├── return.html
│       ├── history.html
│       ├── fines.html
│       └── profile.html
│
├── static/
│   ├── css/style.css           # Clean, responsive CSS (No heavy frameworks)
│   └── js/main.js              # Client validation & modal interactions
│
├── database/                   # SQL demonstration suite
│   ├── schema.sql              # 3NF DDL table definitions & constraints
│   ├── sample_data.sql         # 50 students, 40+ books, authors, issues, fines
│   ├── queries.sql             # DQL, Joins, Group By, Having, Subqueries
│   ├── tcl.sql                 # Transaction scripts (Commit, Rollback, Savepoint)
│   └── dcl.sql                 # Real MySQL User management (Grant, Revoke)
│
├── architecture.md             # Technical & database architecture specification
├── design.md                   # Table designs, state machines & UI wireframes
├── memory.md                   # Decisions log & 14-phase implementation tracker
├── prd.md                      # Product requirements document
├── rules.md                    # Core business rules & invariant logic
└── README.md                   # Project overview & running instructions
```

---

## 🎓 Viva & DBMS Practical Presentation Highlights

When demonstrating this project to examiners or professors, highlight:
- **Relational Normalization**: Explain why `book_authors` exists as a junction table to satisfy 1NF, and how `categories` and `authors` prevent 2NF/3NF anomalies.
- **Foreign Key Actions**: Explain `ON DELETE CASCADE` for auth user removal vs `RESTRICT` on book deletions when copies are on loan.
- **ACID Transactions**: Walk through book issue/return logic demonstrating row locking (`FOR UPDATE`), atomic updates, and rollback on constraint violation.
- **Aggregations & Analytical Queries**: Show reports utilizing `COUNT()`, `SUM()`, `GROUP BY`, and `HAVING` to isolate high-borrowing students and top categories.
- **DCL vs Business Privilege**: Distinguish how MySQL server users (`library_staff`) differ from application student privileges (`students.borrowing_permission`).
