import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import DietTracker from './components/DietTracker.js';
import WorkoutLog from './components/WorkoutLog.js';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DietTracker />} />
        <Route path="/workout-log" element={<WorkoutLog />} />
      </Routes>
    </Router>
  );
}

export default App;