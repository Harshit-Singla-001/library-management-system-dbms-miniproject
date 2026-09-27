-- =============================================================================
-- LIBRARY MANAGEMENT SYSTEM - TRANSACTION CONTROL LANGUAGE (TCL) DEMONSTRATION
-- Database: library_db
-- Topics: START TRANSACTION, COMMIT, ROLLBACK, SAVEPOINT, ROLLBACK TO SAVEPOINT
-- =============================================================================

USE `library_db`;

-- =============================================================================
-- SCENARIO 1: ATOMIC BOOK CHECKOUT TRANSACTION (SUCCESSFUL COMMIT)
-- Invariant: Both the issue record insertion and available_copies decrement
-- must succeed together, or neither should take effect.
-- =============================================================================

-- Step 1: Check initial book availability for Book 2
SELECT `book_id`, `title`, `available_copies` FROM `books` WHERE `book_id` = 2;

-- Step 2: Begin Transaction
START TRANSACTION;

-- Step 3: Insert the issue transaction (Student 2417101 issues Book 2)
INSERT INTO `issued_books` (`student_id`, `book_id`, `issue_date`, `due_date`, `status`, `remarks`)
VALUES (1, 2, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'ISSUED', 'TCL Demo Successful Loan');

-- Step 4: Decrement available copies
UPDATE `books` 
SET `available_copies` = `available_copies` - 1 
WHERE `book_id` = 2;

-- Step 5: Verify changes within uncommitted transaction state
SELECT `book_id`, `title`, `available_copies` FROM `books` WHERE `book_id` = 2;

-- Step 6: Commit all changes permanently to disk
COMMIT;

-- Verify final persisted state
SELECT `book_id`, `title`, `available_copies` FROM `books` WHERE `book_id` = 2;


-- =============================================================================
-- SCENARIO 2: BOOK CHECKOUT FAILURE (TRANSACTION ROLLBACK)
-- Simulation: An unexpected constraint violation or business rule failure occurs
-- midway through execution. The entire transaction is rolled back to protect data integrity.
-- =============================================================================

-- Record copy count prior to failed transaction
SELECT `book_id`, `title`, `available_copies` FROM `books` WHERE `book_id` = 3;

-- Begin Transaction
START TRANSACTION;

-- Attempt step: Decrement available copies
UPDATE `books` 
SET `available_copies` = `available_copies` - 1 
WHERE `book_id` = 3;

-- Business check fails (e.g., student exceeds 3-book limit or has unpaid fine)
-- We abort the operation and restore all modified rows to original state:
ROLLBACK;

-- Verify that available_copies was NOT decremented:
SELECT `book_id`, `title`, `available_copies` FROM `books` WHERE `book_id` = 3;


-- =============================================================================
-- SCENARIO 3: DEMONSTRATING SAVEPOINT & PARTIAL ROLLBACK
-- Scenario: During a batch library inventory receipt, multiple books are registered.
-- One entry contains bad data and is rolled back to a SAVEPOINT without aborting
-- the previously successful entries.
-- =============================================================================

START TRANSACTION;

-- Stage 1: Add new inventory copy for Book 5
UPDATE `books` SET `total_copies` = `total_copies` + 1, `available_copies` = `available_copies` + 1 WHERE `book_id` = 5;

-- Create Savepoint A after first update
SAVEPOINT stage_one_complete;

-- Stage 2: Mistakenly try to update Book 999 (Non-existent or flawed)
UPDATE `books` SET `available_copies` = -5 WHERE `book_id` = 1; -- violates CHECK constraint or business rule

-- Roll back only to the savepoint (discards stage 2, preserves stage 1)
ROLLBACK TO SAVEPOINT stage_one_complete;

-- Finalize and commit stage 1
COMMIT;

-- =============================================================================
-- END OF TCL DEMONSTRATION
-- =============================================================================
