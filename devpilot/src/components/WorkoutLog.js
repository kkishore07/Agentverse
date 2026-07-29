import React from 'react';
import { useState } from 'react';
import './WorkoutLog.css'; // Importing CSS file for styling

const WorkoutLog = ({ workoutData }) => {
    const [logEntries, setLogEntries] = useState([]);

    const addEntry = () => {
        if (workoutData) {
            logEntries.push(workoutData);
            setLogEntries([...logEntries]);
        } else {
            alert('Please select a workout data first.');
        }
    };

    return (
        <div className="workout-log">
            <h1>Workout Log</h1>
            <form>
                <label htmlFor="workout">Select Workout Data:</label>
                <select id="workout" onChange={(e) => {
                    const selectedValue = e.target.value;
                    if (selectedValue === 'running') {
                        setLogEntries([...logEntries, { type: 'Running', duration: 30 }]);
                    } else if (selectedValue === 'cycling') {
                        setLogEntries([...logEntries, { type: 'Cycling', distance: 25 }]);
                    }
                }}>
                    <option value="running">Running</option>
                    <option value="cycling">Cycling</option>
                </select>
            </form>
            <ul className="entries">
                {logEntries.map((entry) => (
                    <li key={entry.type}>
                        {entry.type}: {entry.duration || entry.distance}
                    </li>
                ))}
            </ul>
            <button onClick={addEntry}>Add Entry</button>
        </div>
    );
};

export default WorkoutLog;