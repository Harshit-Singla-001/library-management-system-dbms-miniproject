-- =============================================================================
-- LIBRARY MANAGEMENT SYSTEM - SQL QUERY DEMONSTRATION SUITE
-- Database: library_db
-- Topics: DDL, DML, DQL, Joins, Aggregates, Group By, Having, Subqueries, Reports
-- =============================================================================

USE `library_db`;

-- =============================================================================
-- SECTION 1: DATA DEFINITION LANGUAGE (DDL) DEMONSTRATIONS
-- Note: Safe examples shown. Destructive commands are commented for demonstration.
-- =============================================================================

-- 1.1 ALTER TABLE: Adding a demonstration audit column
ALTER TABLE `books` ADD COLUMN `location_rack` VARCHAR(30) NULL DEFAULT 'Main-Stack-A';

-- 1.2 ALTER TABLE: Modifying column data type
ALTER TABLE `books` MODIFY COLUMN `location_rack` VARCHAR(50) NULL DEFAULT 'General-Stack';

-- 1.3 ALTER TABLE: Dropping demonstration column safely
ALTER TABLE `books` DROP COLUMN `location_rack`;

-- 1.4 Demonstrating Constraints (Unique & Foreign Key)
-- (Already active in schema: UNIQUE(isbn), UNIQUE(roll_number), CHECK(available_copies >= 0))


-- =============================================================================
-- SECTION 2: DATA MANIPULATION LANGUAGE (DML) DEMONSTRATIONS
-- =============================================================================

-- 2.1 INSERT: Adding a single student
-- (Tested within application workflow)

-- 2.2 UPDATE: Modifying an author's biography
UPDATE `authors`
SET `biography` = 'Distinguished Professor Emeritus and Turing Award Contributor'
WHERE `author_id` = 1;

-- 2.3 UPDATE: Updating a student's phone number
UPDATE `students`
SET `phone` = '9876549999'
WHERE `roll_number` = '2417101';

-- 2.4 DELETE: Removing records safely (demonstrating safe delete)
-- DELETE FROM `categories` WHERE `category_id` = 999; -- Safe because ID 999 has no child books


-- =============================================================================
-- SECTION 3: DATA QUERY LANGUAGE (DQL) - BASIC & INTERMEDIATE
-- =============================================================================

-- 3.1 Basic SELECT with WHERE and ORDER BY
-- List all Computer Science students ordered by full name alphabetically
SELECT `roll_number`, `full_name`, `email`, `department`, `borrowing_permission`
FROM `students`
WHERE `department` = 'CSE'
ORDER BY `full_name` ASC;

-- 3.2 DISTINCT: View all unique departments with enrolled students
SELECT DISTINCT `department`
FROM `students`
ORDER BY `department` ASC;

-- 3.3 LIKE Operator: Search books containing 'Data' in the title
SELECT `book_id`, `isbn`, `title`, `total_copies`, `available_copies`
FROM `books`
WHERE `title` LIKE '%Data%'
ORDER BY `title`;

-- 3.4 BETWEEN Operator: Find books published between 2010 and 2020
SELECT `title`, `edition`, `publish_year`
FROM `books`
WHERE `publish_year` BETWEEN 2010 AND 2020
ORDER BY `publish_year` DESC;

-- 3.5 IN Operator: Find students belonging to CSE, IT, or ECE departments
SELECT `roll_number`, `full_name`, `department`
FROM `students`
WHERE `department` IN ('CSE', 'IT', 'ECE')
ORDER BY `department`, `full_name`;


-- =============================================================================
-- SECTION 4: AGGREGATE FUNCTIONS & GROUPING (GROUP BY, HAVING)
-- =============================================================================

-- 4.1 Basic Aggregates: Total physical books, total available books, average publication year
SELECT 
    COUNT(*) AS total_unique_titles,
    SUM(`total_copies`) AS total_physical_inventory,
    SUM(`available_copies`) AS currently_available_copies,
    ROUND(AVG(`publish_year`), 0) AS avg_publication_year,
    MIN(`publish_year`) AS oldest_book_year,
    MAX(`publish_year`) AS newest_book_year
FROM `books`;

-- 4.2 GROUP BY: Number of students per department
SELECT 
    `department`,
    COUNT(*) AS student_count
FROM `students`
GROUP BY `department`
ORDER BY student_count DESC;

-- 4.3 GROUP BY with HAVING: Categories containing 4 or more unique book titles
SELECT 
    c.`category_name`,
    COUNT(b.`book_id`) AS book_count,
    SUM(b.`total_copies`) AS total_shelf_copies
FROM `categories` c
JOIN `books` b ON c.`category_id` = b.`category_id`
GROUP BY c.`category_id`, c.`category_name`
HAVING COUNT(b.`book_id`) >= 4
ORDER BY book_count DESC;

-- 4.4 GROUP BY with HAVING: Students who currently have 2 or more active books
SELECT 
    s.`roll_number`,
    s.`full_name`,
    s.`department`,
    COUNT(ib.`issue_id`) AS active_loan_count
FROM `students` s
JOIN `issued_books` ib ON s.`student_id` = ib.`student_id`
WHERE ib.`status` IN ('ISSUED', 'OVERDUE')
GROUP BY s.`student_id`, s.`roll_number`, s.`full_name`, s.`department`
HAVING COUNT(ib.`issue_id`) >= 2
ORDER BY active_loan_count DESC;


-- =============================================================================
-- SECTION 5: RELATIONAL JOINS (INNER, LEFT, MULTI-TABLE)
-- =============================================================================

-- 5.1 Multi-Table INNER JOIN: Books with their Category and Authors (via junction table)
SELECT 
    b.`book_id`,
    b.`isbn`,
    b.`title`,
    c.`category_name`,
    GROUP_CONCAT(a.`author_name` SEPARATOR ', ') AS authors,
    b.`available_copies`,
    b.`total_copies`
FROM `books` b
INNER JOIN `categories` c ON b.`category_id` = c.`category_id`
INNER JOIN `book_authors` ba ON b.`book_id` = ba.`book_id`
INNER JOIN `authors` a ON ba.`author_id` = a.`author_id`
GROUP BY b.`book_id`, b.`isbn`, b.`title`, c.`category_name`, b.`available_copies`, b.`total_copies`
ORDER BY b.`title` ASC;

-- 5.2 LEFT JOIN: All students and their active book loans (includes students with 0 loans)
SELECT 
    s.`roll_number`,
    s.`full_name`,
    s.`borrowing_permission`,
    COALESCE(b.`title`, 'No Active Book') AS borrowed_book,
    ib.`issue_date`,
    ib.`due_date`,
    COALESCE(ib.`status`, 'N/A') AS loan_status
FROM `students` s
LEFT JOIN `issued_books` ib ON s.`student_id` = ib.`student_id` AND ib.`status` IN ('ISSUED', 'OVERDUE')
LEFT JOIN `books` b ON ib.`book_id` = b.`book_id`
ORDER BY s.`roll_number` ASC;

-- 5.3 LEFT JOIN with Aggregations: Fines summary per student
SELECT 
    s.`roll_number`,
    s.`full_name`,
    COUNT(f.`fine_id`) AS total_fines_incurred,
    COALESCE(SUM(CASE WHEN f.`payment_status` = 'UNPAID' THEN f.`fine_amount` ELSE 0 END), 0.00) AS total_unpaid_fines,
    COALESCE(SUM(CASE WHEN f.`payment_status` = 'PAID' THEN f.`fine_amount` ELSE 0 END), 0.00) AS total_paid_fines
FROM `students` s
LEFT JOIN `fines` f ON s.`student_id` = f.`student_id`
GROUP BY s.`student_id`, s.`roll_number`, s.`full_name`
HAVING total_fines_incurred > 0
ORDER BY total_unpaid_fines DESC;


-- =============================================================================
-- SECTION 6: SUBQUERIES (SCALAR, IN, EXISTS, CORRELATED)
-- =============================================================================

-- 6.1 Subquery with IN: Students who have borrowed books in the 'Database Systems' category
SELECT `roll_number`, `full_name`, `department`
FROM `students`
WHERE `student_id` IN (
    SELECT DISTINCT ib.`student_id`
    FROM `issued_books` ib
    JOIN `books` b ON ib.`book_id` = b.`book_id`
    JOIN `categories` c ON b.`category_id` = c.`category_id`
    WHERE c.`category_name` = 'Database Systems'
);

-- 6.2 Subquery with NOT IN: Students who have NEVER borrowed any book
SELECT `roll_number`, `full_name`, `department`, `borrowing_permission`
FROM `students`
WHERE `student_id` NOT IN (
    SELECT DISTINCT `student_id` 
    FROM `issued_books`
)
ORDER BY `roll_number` ASC;

-- 6.3 Subquery with EXISTS: Identify students who currently have an OVERDUE book
SELECT `roll_number`, `full_name`, `email`
FROM `students` s
WHERE EXISTS (
    SELECT 1 
    FROM `issued_books` ib
    WHERE ib.`student_id` = s.`student_id` 
      AND (ib.`status` = 'OVERDUE' OR (ib.`status` = 'ISSUED' AND ib.`due_date` < CURDATE()))
);

-- 6.4 Correlated Subquery: Compute live active book count alongside each student profile
SELECT 
    s.`roll_number`,
    s.`full_name`,
    s.`borrowing_permission`,
    (SELECT COUNT(*) FROM `issued_books` ib WHERE ib.`student_id` = s.`student_id` AND ib.`status` IN ('ISSUED', 'OVERDUE')) AS active_books_count,
    (SELECT COALESCE(SUM(`fine_amount`), 0.00) FROM `fines` f WHERE f.`student_id` = s.`student_id` AND f.`payment_status` = 'UNPAID') AS unpaid_fine_amount
FROM `students` s
ORDER BY active_books_count DESC, s.`roll_number` ASC;


-- =============================================================================
-- SECTION 7: CORE ADMINISTRATIVE REPORTS
-- =============================================================================

-- 7.1 REPORT 1: Top 5 Most Frequently Borrowed Books (Circulation Popularity)
SELECT 
    b.`book_id`,
    b.`title`,
    c.`category_name`,
    COUNT(ib.`issue_id`) AS total_times_borrowed
FROM `books` b
JOIN `categories` c ON b.`category_id` = c.`category_id`
LEFT JOIN `issued_books` ib ON b.`book_id` = ib.`book_id`
GROUP BY b.`book_id`, b.`title`, c.`category_name`
ORDER BY total_times_borrowed DESC
LIMIT 5;

-- 7.2 REPORT 2: Students who have reached the Maximum 3-Book Limit
SELECT 
    s.`roll_number`,
    s.`full_name`,
    s.`department`,
    COUNT(ib.`issue_id`) AS active_books
FROM `students` s
JOIN `issued_books` ib ON s.`student_id` = ib.`student_id`
WHERE ib.`status` IN ('ISSUED', 'OVERDUE')
GROUP BY s.`student_id`, s.`roll_number`, s.`full_name`, s.`department`
HAVING COUNT(ib.`issue_id`) = 3;

-- 7.3 REPORT 3: Overdue Loans Audit with Calculated Pending Fine
SELECT 
    ib.`issue_id`,
    s.`roll_number`,
    s.`full_name`,
    b.`title`,
    ib.`issue_date`,
    ib.`due_date`,
    DATEDIFF(CURDATE(), ib.`due_date`) AS overdue_days,
    DATEDIFF(CURDATE(), ib.`due_date`) * 5.00 AS calculated_accruing_fine
FROM `issued_books` ib
JOIN `students` s ON ib.`student_id` = s.`student_id`
JOIN `books` b ON ib.`book_id` = b.`book_id`
WHERE ib.`status` IN ('ISSUED', 'OVERDUE') AND ib.`due_date` < CURDATE()
ORDER BY overdue_days DESC;

-- 7.4 REPORT 4: Inventory Depletion Warning (Books with 0 or 1 copy remaining)
SELECT 
    b.`isbn`,
    b.`title`,
    c.`category_name`,
    b.`available_copies`,
    b.`total_copies`
FROM `books` b
JOIN `categories` c ON b.`category_id` = c.`category_id`
WHERE b.`available_copies` <= 1
ORDER BY b.`available_copies` ASC;
