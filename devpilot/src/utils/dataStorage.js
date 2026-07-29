// src/utils/dataStorage.js

import { MongoClient } from 'mongodb';
import express from 'express';

const dbUrl = 'mongodb://localhost:27017/healthTrackerDB'; // Replace with your MongoDB connection string

export async function connectToDatabase() {
  try {
    const client = new MongoClient(dbUrl);
    await client.connect();
    console.log('Connected to database');
    return client;
  } catch (error) {
    console.error('Error connecting to database:', error);
    throw new Error('Failed to connect to MongoDB');
  }
}

export async function closeDatabaseConnection(client) {
  try {
    await client.close();
    console.log('Closed database connection');
  } catch (error) {
    console.error('Error closing database connection:', error);
  }
}

export async function insertDietEntry(dietData, dietId) {
  const collection = 'dietEntries';
  const document = { ...dietData, _id: dietId };
  try {
    const client = await connectToDatabase();
    const db = client.db('healthTrackerDB');
    const result = await db.collection(collection).insertOne(document);
    console.log(`Inserted entry with ID ${result.insertedCount}`);
    return result;
  } catch (error) {
    console.error('Error inserting diet entry:', error);
    throw new Error('Failed to insert diet entry into database');
  }
}

export async function retrieveDietEntry(dietId) {
  const collection = 'dietEntries';
  try {
    const client = await connectToDatabase();
    const db = client.db('healthTrackerDB');
    const result = await db.collection(collection).findOne({ _id: dietId });
    console.log(`Retrieved entry with ID ${dietId}`);
    return result;
  } catch (error) {
    console.error('Error retrieving diet entry:', error);
    throw new Error('Failed to retrieve diet entry from database');
  }
}

export async function insertWorkoutLog(workoutData, workoutId) {
  const collection = 'workoutLogs';
  const document = { ...workoutData, _id: workoutId };
  try {
    const client = await connectToDatabase();
    const db = client.db('healthTrackerDB');
    const result = await db.collection(collection).insertOne(document);
    console.log(`Inserted log with ID ${result.insertedCount}`);
    return result;
  } catch (error) {
    console.error('Error inserting workout log:', error);
    throw new Error('Failed to insert workout log into database');
  }
}

export async function retrieveWorkoutLog(workoutId) {
  const collection = 'workoutLogs';
  try {
    const client = await connectToDatabase();
    const db = client.db('healthTrackerDB');
    const result = await db.collection(collection).findOne({ _id: workoutId });
    console.log(`Retrieved log with ID ${workoutId}`);
    return result;
  } catch (error) {
    console.error('Error retrieving workout log:', error);
    throw new Error('Failed to retrieve workout log from database');
  }
}