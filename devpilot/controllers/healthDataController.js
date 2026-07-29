// healthDataController.js

const express = require('express');
const router = express.Router();
const User = require('./models/User'); // Assuming models/User is imported from ./models/User.js
const nutritionAnalysis = require('./utils/nutritionAnalysis'); // Assuming utils/nutritionAnalysis.js is imported
const workoutTrackerBackend = require('./controllers/workoutTrackerController'); // Assuming controllers/workoutTrackerController.js is imported

// Health data controller routes for logging, customizing diet and workout plans based on user input.

// Example route to log a new health entry (diet or workout)
router.post('/log', async (req, res) => {
  const { type, details } = req.body;
  try {
    // Validate the request body
    if (!type || !details) throw new Error('Missing required fields');
    
    // Log the data to the database
    await User.findByIdAndUpdate(req.user.id, { $push: { [type]: details } });
    
    res.status(201).send({ message: 'Data logged successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).send({ error: 'Internal server error' });
  }
});

// Example route to customize diet based on user input
router.post('/customizeDiet', async (req, res) => {
  const { nutrients, goals } = req.body;
  try {
    // Validate the request body
    if (!nutrients || !goals) throw new Error('Missing required fields');
    
    // Perform nutrition analysis and update user's diet plan accordingly
    await nutritionAnalysis.analyzeNutrition(nutrients, goals);
    
    res.status(201).send({ message: 'Diet customized successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).send({ error: 'Internal server error' });
  }
});

// Example route to customize workout plan based on user input
router.post('/customizeWorkout', async (req, res) => {
  const { exercises, intensity } = req.body;
  try {
    // Validate the request body
    if (!exercises || !intensity) throw new Error('Missing required fields');
    
    // Perform workout analysis and update user's workout plan accordingly
    await workoutTrackerBackend.analyzeWorkout(exercises, intensity);
    
    res.status(201).send({ message: 'Workout customized successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).send({ error: 'Internal server error' });
  }
});

module.exports = router;