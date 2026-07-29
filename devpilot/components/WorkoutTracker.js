import React from 'react';
import { useState } from 'react';

const WorkoutTracker = ({ user }) => {
    const [workoutData, setWorkoutData] = useState({});

    const handleAddWorkout = (newWorkout) => {
        // Add workout data to state
        setWorkoutData(prevData => ({
            ...prevData,
            [newWorkout.type]: newWorkout
        }));
    };

    return (
        <div>
            {/* Workout tracker form */}
            <form>
                <label htmlFor="workoutType">Choose a type:</label>
                <select id="workoutType" onChange={(e) => handleAddWorkout({ type: e.target.value })}>
                    <option value="">Select</option>
                    <option value="cardio">Cardio</option>
                    <option value="strength">Strength</option>
                    {/* Add more workout types as needed */}
                </select>

                <label htmlFor="workoutDuration">Duration (in minutes):</label>
                <input type="number" id="workoutDuration" onChange={(e) => handleAddWorkout({ duration: e.target.value })} />

                {/* Additional workout details fields */}
            </form>

            {/* Display workout data */}
            {Object.keys(workoutData).map((type, index) => (
                <div key={index}>
                    <h3>{type}</h3>
                    <p>Duration: {workoutData[type].duration} minutes</p>
                    {/* Add more details as needed */}
                </div>
            ))}
        </div>
    );
};

export default WorkoutTracker;