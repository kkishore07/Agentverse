// models/User.js

import mongoose from 'mongoose';
import bcrypt from 'bcrypt';

const UserSchema = new mongoose.Schema({
    username: {
        type: String,
        required: true,
        unique: true
    },
    passwordHash: {
        type: String,
        required: true
    },
    dietTrackerId: {
        type: mongoose.Types.ObjectId,
        ref: 'DietTracker'
    },
    workoutTrackerId: {
        type: mongoose.Types.ObjectId,
        ref: 'WorkoutTracker'
    }
});

UserSchema.pre('save', async function(next) {
    if (!this.isModified('passwordHash')) return next();
    
    try {
        await bcrypt.hash(this.passwordHash, 10);
    } catch (error) {
        throw new Error('Failed to hash password');
    }

    next();
});

export default mongoose.model('User', UserSchema);
