// test-player-analytics.js
// Simple script to test the player analytics endpoints

const axios = require('axios');

const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2ODg3NiwianRpIjoiZjhiMmI3MGQtOThiMi00YzlkLTg3MmMtMzQ0YTI1OWRmZmYwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2Njg4NzYsImV4cCI6MTc0Mzk2NDg3Nn0.n5rm-77qiwY5O1kXl76u-xXfFz2qJT-9YvZeafGBZB0";
const teamId = 2; // Using team ID 2 from previous context
const baseUrl = 'https://www.lineupboss.app/api';

// Helper to print responses nicely
const printResponse = (endpoint, data) => {
  console.log(`\n=== ${endpoint} Response ===`);
  console.log(JSON.stringify(data, null, 2));
};

// Make the API calls
async function testEndpoints() {
  try {
    // Setup axios with the token
    const instance = axios.create({
      baseURL: baseUrl,
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    // Test Batting Analytics endpoint
    console.log('\nTesting Batting Analytics endpoint...');
    const battingResponse = await instance.get(`/analytics/teams/${teamId}/batting-analytics`);
    printResponse('Batting Analytics', battingResponse.data);
    
    // Test Fielding Analytics endpoint
    console.log('\nTesting Fielding Analytics endpoint...');
    const fieldingResponse = await instance.get(`/analytics/teams/${teamId}/fielding-analytics`);
    printResponse('Fielding Analytics', fieldingResponse.data);
    
    // Add a debug endpoint call
    console.log('\nTesting Debug endpoint...');
    const debugResponse = await instance.get(`/analytics/teams/${teamId}/debug`);
    printResponse('Debug', debugResponse.data);
    
  } catch (error) {
    console.error('Error during API calls:');
    if (error.response) {
      console.error(`Status: ${error.response.status}`);
      console.error('Response data:', error.response.data);
    } else if (error.request) {
      console.error('No response received');
    } else {
      console.error('Error:', error.message);
    }
  }
}

testEndpoints();