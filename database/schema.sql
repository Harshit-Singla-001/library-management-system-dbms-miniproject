-- =============================================================================
-- LIBRARY MANAGEMENT SYSTEM - DATABASE SCHEMA (DDL)
-- Database Engine: MySQL 8.0 (InnoDB)
-- Normalization Level: Third Normal Form (3NF)
-- Character Set: utf8mb4 / utf8mb4_unicode_ci
-- =============================================================================

-- Step 1: Create and Switch to Database
CREATE DATABASE IF NOT EXISTS `library_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `library_db`;

-- Step 2: Drop existing tables in reverse dependency order (safe script re-run)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `fines`;
DROP TABLE IF EXISTS `issued_books`;
DROP TABLE IF EXISTS `book_authors`;
DROP TABLE IF EXISTS `books`;
DROP TABLE IF EXISTS `authors`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `students`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- TABLE 1: users
-- Purpose: Authentication store for both Admins and Students with role mapping.
-- Password hashes use standard secure hashes (PBKDF2/Bcrypt).
-- =============================================================================
CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT 'Unique login identifier (admin or student 7-digit roll number)',
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'Secure hash of password',
    `role` ENUM('ADMIN', 'STUDENT') NOT NULL COMMENT 'Security role context',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Account creation timestamp'
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 2: students
-- Purpose: Academic profiles, institutional roll numbers, and library privileges.
-- Includes borrowing_permission which is checked by backend logic.
-- =============================================================================
CREATE TABLE `students` (
    `student_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE COMMENT '1:1 link to users table for authentication',
    `roll_number` VARCHAR(20) NOT NULL UNIQUE COMMENT '7-digit roll number (e.g., 2417119)',
    `full_name` VARCHAR(100) NOT NULL COMMENT 'Student full name',
    `email` VARCHAR(120) NOT NULL UNIQUE COMMENT 'Student institutional email address',
    `phone` VARCHAR(20) NOT NULL COMMENT 'Contact phone number',
    `department` VARCHAR(60) NOT NULL COMMENT 'Department (e.g. CSE, IT, ECE, ME)',
    `borrowing_permission` ENUM('GRANTED', 'REVOKED') NOT NULL DEFAULT 'GRANTED' 
        COMMENT 'Library business rule: Admin can grant or revoke checkout privilege',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_students_user`
        FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 3: categories
-- Purpose: Subject/genre classifications for books.
-- Ensures 3NF by preventing repeating category descriptions in books table.
-- =============================================================================
CREATE TABLE `categories` (
    `category_id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_name` VARCHAR(80) NOT NULL UNIQUE COMMENT 'Subject taxonomy title (e.g., Database Systems, AI)',
    `description` TEXT NULL COMMENT 'Category overview and syllabus topics covered'
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 4: authors
-- Purpose: Master catalog of authors and contributors.
-- =============================================================================
CREATE TABLE `authors` (
    `author_id` INT AUTO_INCREMENT PRIMARY KEY,
    `author_name` VARCHAR(120) NOT NULL COMMENT 'Full name of author',
    `biography` TEXT NULL COMMENT 'Brief author biography and background'
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 5: books
-- Purpose: Book catalog metadata and physical inventory counts.
-- available_copies tracks physical units on shelves; total_copies is total owned.
-- =============================================================================
CREATE TABLE `books` (
    `book_id` INT AUTO_INCREMENT PRIMARY KEY,
    `isbn` VARCHAR(20) NOT NULL UNIQUE COMMENT 'Standard International Standard Book Number',
    `title` VARCHAR(200) NOT NULL COMMENT 'Book title',
    `category_id` INT NOT NULL COMMENT 'Foreign key to categories',
    `total_copies` INT NOT NULL DEFAULT 1 COMMENT 'Total physical copies owned by library',
    `available_copies` INT NOT NULL DEFAULT 1 COMMENT 'Copies currently available on shelf',
    `edition` VARCHAR(30) NULL COMMENT 'Edition (e.g. 7th Edition, Global Edition)',
    `publish_year` INT NULL COMMENT 'Year of publication',
    CONSTRAINT `chk_books_total_copies` CHECK (`total_copies` >= 0),
    CONSTRAINT `chk_books_avail_copies` CHECK (`available_copies` >= 0),
    CONSTRAINT `chk_books_avail_le_total` CHECK (`available_copies` <= `total_copies`),
    CONSTRAINT `fk_books_category`
        FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 6: book_authors (Junction Table for M:N Relationship)
-- Purpose: Resolves Many-to-Many relationship between books and authors.
-- Ensures 1NF (avoids multi-valued comma separated values in books table).
-- =============================================================================
CREATE TABLE `book_authors` (
    `book_id` INT NOT NULL COMMENT 'Foreign key to books',
    `author_id` INT NOT NULL COMMENT 'Foreign key to authors',
    PRIMARY KEY (`book_id`, `author_id`),
    CONSTRAINT `fk_ba_book`
        FOREIGN KEY (`book_id`) REFERENCES `books` (`book_id`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_ba_author`
        FOREIGN KEY (`author_id`) REFERENCES `authors` (`author_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 7: issued_books
-- Purpose: Active and past book checkout transactions, due dates, and return logs.
-- =============================================================================
CREATE TABLE `issued_books` (
    `issue_id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_id` INT NOT NULL COMMENT 'Borrowing student',
    `book_id` INT NOT NULL COMMENT 'Borrowed book',
    `issue_date` DATE NOT NULL COMMENT 'Date book was checked out',
    `due_date` DATE NOT NULL COMMENT 'Scheduled return deadline (typically issue_date + 14 days)',
    `return_date` DATE NULL COMMENT 'Actual date returned (NULL while actively issued)',
    `status` ENUM('ISSUED', 'RETURNED', 'OVERDUE') NOT NULL DEFAULT 'ISSUED' COMMENT 'Current loan lifecycle status',
    `remarks` VARCHAR(255) NULL COMMENT 'Notes on physical book condition or return notes',
    CONSTRAINT `fk_issues_student`
        FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_issues_book`
        FOREIGN KEY (`book_id`) REFERENCES `books` (`book_id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE 8: fines
-- Purpose: Monetary late fees incurred when a book is returned after due_date.
-- Linked 1:1 with issued_books to maintain precise audit trails.
-- =============================================================================
CREATE TABLE `fines` (
    `fine_id` INT AUTO_INCREMENT PRIMARY KEY,
    `issue_id` INT NOT NULL UNIQUE COMMENT '1:1 link to checkout incident that caused fine',
    `student_id` INT NOT NULL COMMENT 'Student who owes the fine',
    `fine_amount` DECIMAL(8,2) NOT NULL DEFAULT 0.00 COMMENT 'Penalty amount in INR (Rs.)',
    `payment_status` ENUM('UNPAID', 'PAID') NOT NULL DEFAULT 'UNPAID' COMMENT 'Settlement status',
    `paid_date` DATETIME NULL COMMENT 'Date and time payment was recorded',
    CONSTRAINT `chk_fines_amount` CHECK (`fine_amount` >= 0),
    CONSTRAINT `fk_fines_issue`
        FOREIGN KEY (`issue_id`) REFERENCES `issued_books` (`issue_id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_fines_student`
        FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =============================================================================
-- PERFORMANCE & QUERY INDEXES
-- Optimize lookups for frequently joined and filtered columns.
-- =============================================================================
CREATE INDEX `idx_books_category` ON `books` (`category_id`);
CREATE INDEX `idx_books_title` ON `books` (`title`);
CREATE INDEX `idx_issued_books_student` ON `issued_books` (`student_id`);
CREATE INDEX `idx_issued_books_status` ON `issued_books` (`status`);
CREATE INDEX `idx_issued_books_due` ON `issued_books` (`due_date`);
CREATE INDEX `idx_fines_student_status` ON `fines` (`student_id`, `payment_status`);

-- =============================================================================
-- VERIFICATION CHECK QUERY
-- Shows all tables created in library_db
-- =============================================================================
SHOW TABLES;
