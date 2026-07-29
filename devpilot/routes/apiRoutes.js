// Import necessary modules and dependencies
const express = require('express');
const router = express.Router();
const nutritionAnalysis = require('./utils/nutritionAnalysis.js');

// Define API routes for health data tracking
router.post('/healthData', async (req, res) => {
  try {
    // Extract relevant information from request body
    const { dietLog, workoutLog } = req.body;

    // Perform analysis on the provided diet and workout logs
    const nutritionAnalysisResult = await nutritionAnalysis(dietLog, workoutLog);

    // Return the analysis result as JSON response
    res.json(nutritionAnalysisResult);
  } catch (error) {
    console.error('Error processing health data:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Export the route configuration for use in other parts of the application
module.exports = router;