import React, { useState } from 'react';

const Counter = () => {
  // Initialize state with a counter value
  const [count, setCount] = useState(0);

  // Function to increment the counter
  const incrementCounter = () => {
    try {
      // Safely update the count by adding 1
      setCount(prevCount => prevCount + 1);
    } catch (error) {
      console.error("Error updating counter:", error);
    }
  };

  // Function to decrement the counter
  const decrementCounter = () => {
    try {
      // Safely update the count by subtracting 1
      setCount(prevCount => prevCount - 1);
    } catch (error) {
      console.error("Error updating counter:", error);
    }
  };

  return (
    <div>
      <h1>Counter: {count}</h1>
      <button onClick={incrementCounter}>Increment</button>
      <button onClick={decrementCounter}>Decrement</button>
    </div>
  );
};

export default Counter;