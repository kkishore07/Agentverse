# Student Mark Allocator

## Short Description
A web application for staffs to award marks to students in a school management system.

## Tech Stack
- Flask: Web framework for building APIs.
- SQLAlchemy: ORM for interacting with a relational database.
- pytest: Testing library for writing and running tests.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/student-mark-allocator.git
   cd student-mark-allocator
   ```
2. Create virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```
3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the development server:
   ```bash
   flask run
   ```
2. Access the application in your browser at [http://localhost:5000](http://localhost:5000).

## Project Structure

- **`app/main.py`**: Defines API endpoints for mark allocation.
  - This file contains the main logic of the application, including routes and controllers.

- **`app/models.py`**: Models for student marks and staff awards.
  - Contains classes representing entities in the database schema (e.g., `Student`, `Mark`, `StaffAward`).

- **`db/schema.sql`**: Creates the database schema.
  - This file contains SQL commands to create tables, indexes, etc. that are used by the application.

- **`tests/test_main.py`**: Unit tests on the mark allocation system.
  - Contains test cases for various functionalities of the application using pytest.

## Running Tests
1. Install pytest if you haven't already:
   ```bash
   pip install pytest
   ```
2. Run the unit tests:
   ```bash
   pytest
   ```

This README provides a comprehensive guide to setting up, running, and testing your project.