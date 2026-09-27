-- =============================================================================
-- LIBRARY MANAGEMENT SYSTEM - DATA CONTROL LANGUAGE (DCL) DEMONSTRATION
-- Database: library_db
-- Topics: CREATE USER, GRANT, REVOKE, SHOW GRANTS, Database vs App Permissions
-- =============================================================================

USE `library_db`;

-- =============================================================================
-- ACADEMIC CONCEPT DISTINCTION:
-- 1. MySQL DCL (Demonstrated Here):
--    Native database engine security managed by DBA to grant/revoke database privileges
--    (SELECT, INSERT, UPDATE, DELETE) to database user accounts.
-- 2. Library Borrowing Permission (Application Level):
--    Business rule stored in `students.borrowing_permission` (GRANTED / REVOKED)
--    toggled by Librarian via Admin Web Dashboard to allow or deny student book checkout.
-- =============================================================================

-- =============================================================================
-- STEP 1: CREATE DATABASE USERS WITH DIFFERENT RESPONSIBILITY TIERS
-- =============================================================================

-- 1.1 Library Admin User (Full administrative control over library_db)
CREATE USER IF NOT EXISTS 'library_admin'@'localhost' IDENTIFIED BY 'Admin@Pass2026';

-- 1.2 Library Staff / Circulation Desk User (Can issue/return books, view catalog)
CREATE USER IF NOT EXISTS 'library_staff'@'localhost' IDENTIFIED BY 'Staff@Pass2026';

-- 1.3 Library Read-Only Catalog User (Can only browse books, e.g., OPAC public kiosk)
CREATE USER IF NOT EXISTS 'library_readonly'@'localhost' IDENTIFIED BY 'Readonly@Pass2026';

-- Flush privileges to apply
FLUSH PRIVILEGES;


-- =============================================================================
-- STEP 2: DEMONSTRATING SQL 'GRANT' COMMANDS
-- =============================================================================

-- 2.1 GRANT ALL PRIVILEGES: Give library_admin full schema control
GRANT ALL PRIVILEGES ON `library_db`.* TO 'library_admin'@'localhost';

-- 2.2 GRANT SPECIFIC DML PRIVILEGES: Give library_staff read/write rights on operational tables
GRANT SELECT, INSERT, UPDATE ON `library_db`.`books` TO 'library_staff'@'localhost';
GRANT SELECT, INSERT, UPDATE ON `library_db`.`issued_books` TO 'library_staff'@'localhost';
GRANT SELECT, INSERT, UPDATE ON `library_db`.`fines` TO 'library_staff'@'localhost';
GRANT SELECT ON `library_db`.`students` TO 'library_staff'@'localhost';
GRANT SELECT ON `library_db`.`categories` TO 'library_staff'@'localhost';
GRANT SELECT ON `library_db`.`authors` TO 'library_staff'@'localhost';
GRANT SELECT ON `library_db`.`book_authors` TO 'library_staff'@'localhost';

-- 2.3 GRANT READ-ONLY PRIVILEGES: Public kiosk user can only SELECT from books and categories
GRANT SELECT ON `library_db`.`books` TO 'library_readonly'@'localhost';
GRANT SELECT ON `library_db`.`categories` TO 'library_readonly'@'localhost';
GRANT SELECT ON `library_db`.`authors` TO 'library_readonly'@'localhost';
GRANT SELECT ON `library_db`.`book_authors` TO 'library_readonly'@'localhost';

FLUSH PRIVILEGES;


-- =============================================================================
-- STEP 3: AUDITING PRIVILEGES WITH 'SHOW GRANTS'
-- =============================================================================

-- Inspect privileges granted to library_admin
SHOW GRANTS FOR 'library_admin'@'localhost';

-- Inspect privileges granted to library_staff
SHOW GRANTS FOR 'library_staff'@'localhost';

-- Inspect privileges granted to library_readonly
SHOW GRANTS FOR 'library_readonly'@'localhost';


-- =============================================================================
-- STEP 4: DEMONSTRATING SQL 'REVOKE' COMMANDS
-- =============================================================================

-- Scenario: Library policy changes. Circulation staff are no longer allowed to UPDATE
-- fines directly (only chief librarian can waive/edit fines).
-- Revoke UPDATE on fines table from library_staff:
REVOKE UPDATE ON `library_db`.`fines` FROM 'library_staff'@'localhost';

-- Scenario: Revoke book insertion rights from library_staff
REVOKE INSERT ON `library_db`.`books` FROM 'library_staff'@'localhost';

FLUSH PRIVILEGES;

-- Verify that the revoked privileges are no longer present:
SHOW GRANTS FOR 'library_staff'@'localhost';


-- =============================================================================
-- STEP 5: CLEANUP / DEMO TEARDOWN (OPTIONAL FOR LAB TEST)
-- =============================================================================
-- DROP USER IF EXISTS 'library_admin'@'localhost';
-- DROP USER IF EXISTS 'library_staff'@'localhost';
-- DROP USER IF EXISTS 'library_readonly'@'localhost';
-- FLUSH PRIVILEGES;
