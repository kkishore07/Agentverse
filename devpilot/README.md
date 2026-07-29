# Health Tracker

## Short Description
A simple health tracker application that allows users to log their diet and workout activities for better understanding of their daily habits.

## Tech Stack
- **React**: Frontend framework for building user interfaces.
- **Node.js**: Backend server using Express for handling requests and managing database interactions.
- **MongoDB**: NoSQL database for storing user data, including diet entries and workout logs.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/health-tracker.git
   ```
2. Navigate to the project directory:
   ```bash
   cd health-tracker
   ```
3. Install dependencies:
   ```bash
   npm install
   ```

## Usage
1. Start the backend server:
   ```bash
   node src/server.js
   ```
2. Open your browser and navigate to `http://localhost:5000` to access the application.
3. Log diet entries by visiting `/diet` and entering details in the form.
4. Record workout activities by navigating to `/workout` and filling out the form with relevant information.

## Project Structure
- **src/**:
  - Contains all frontend components (`App.js`, `DietTracker.js`, `WorkoutLog.js`) and utility functions for data storage (`dataStorage.js`).
  - Also includes unit tests (`tests/unit/App.test.js`).

- **tests/**:
  - Contains test files for the main application component.

## Running Tests
1. Ensure you have Node.js installed on your system.
2. Navigate to the project directory and run:
   ```bash
   npm test
   ```
This will execute all unit tests in the `src/components` folder, ensuring that components are functioning as expected.