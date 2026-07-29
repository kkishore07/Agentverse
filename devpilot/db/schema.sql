-- db/schema.sql

CREATE TABLE IF NOT EXISTS `students` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) UNIQUE NOT NULL,
    `marks` JSON DEFAULT '[]' COMMENT 'Marks awarded to the student'
);

CREATE TABLE IF NOT EXISTS `staffs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS `assignments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT DEFAULT '',
    `due_date` DATE NOT NULL,
    `staff_id` INT REFERENCES staffs(id)
);

CREATE TABLE IF NOT EXISTS `marks` (
    `student_id` INT REFERENCES students(id),
    `assignment_id` INT REFERENCES assignments(id),
    `mark` DECIMAL(5, 2) NOT NULL,
    PRIMARY KEY (student_id, assignment_id)
);

-- Example data insertion
INSERT INTO `students` (`name`, `email`) VALUES ('John Doe', 'john.doe@example.com');
INSERT INTO `staffs` (`name`, `email`) VALUES ('Jane Smith', 'jane.smith@example.com');

INSERT INTO `assignments` (`title`, `description`, `due_date`, `staff_id`) VALUES
('Assignment 1', 'Description for Assignment 1', '2023-04-05', 1),
('Assignment 2', 'Description for Assignment 2', '2023-04-10', 2);

INSERT INTO `marks` (`student_id`, `assignment_id`, `mark`) VALUES
(1, 1, 85.00), (1, 2, 90.00);