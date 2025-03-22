/**
 * Debug Batting Order Data
 * 
 * This script makes low-level requests to diagnose why batting order data 
 * isn't being correctly fetched from the API for game 14
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDcyOSwianRpIjoiZTMxNzc3YjUtYjkyOS00M2E5LWIyNTAtNDg4Nzc1ZGU3NDU4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjA3MjksImV4cCI6MTc0Mzk1NjcyOX0.x-2T5y0s2Tg1CX1-PM-ildtvIPeDcz4o8WsG24Di8X8';
const gameId = 14;

// Setup API call with the correct URL
const api = axios.create({
  baseURL: 'https://www.lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

async function debugBattingOrder() {
  console.log('DEBUGGING BATTING ORDER ISSUE FOR GAME 14');
  console.log('=========================================\n');
  
  try {
    // Make a direct request to the batting order endpoint
    console.log('1. Making direct GET request to batting order endpoint...');
    try {
      const directResponse = await api.get(`/games/${gameId}/batting-order`);
      
      console.log(`Response status: ${directResponse.status}`);
      console.log(`Response type: ${typeof directResponse.data}`);
      
      if (Array.isArray(directResponse.data)) {
        console.log(`Response is an array with ${directResponse.data.length} elements`);
        
        if (directResponse.data.length > 0) {
          console.log('\nSample of first item:');
          console.log(JSON.stringify(directResponse.data[0], null, 2));
          
          // Check if positions have player data
          const withPlayers = directResponse.data.filter(pos => pos.player).length;
          console.log(`\nPositions with players: ${withPlayers}/${directResponse.data.length}`);
        } else {
          console.log('Empty array returned (no batting order data)');
        }
      } else {
        console.log('Unexpected response format:');
        console.log(JSON.stringify(directResponse.data, null, 2));
      }
    } catch (error) {
      console.log('Error fetching batting order:');
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log('Response data:', error.response.data);
      } else {
        console.log(`Error message: ${error.message}`);
      }
    }
    
    // Check game details to confirm existence
    console.log('\n2. Fetching game details to confirm existence...');
    try {
      const gameResponse = await api.get(`/games/${gameId}`);
      console.log(`Game found: ${gameResponse.data.opponent} (${gameResponse.data.date})`);
      console.log('Game data:', JSON.stringify(gameResponse.data, null, 2));
    } catch (error) {
      console.log(`Error fetching game details: ${error.message}`);
    }
    
    // Try accessing API endpoint for batting orders in a different format
    console.log('\n3. Trying alternative URL formats for batting order...');
    
    const altUrls = [
      `/games/${gameId}/batting_order`,
      `/games/${gameId}/batting-order/`,
      `/games/${gameId}/batting_orders`,
      `/batting-orders/game/${gameId}`
    ];
    
    for (const url of altUrls) {
      try {
        console.log(`Trying URL: ${url}`);
        const response = await api.get(url);
        console.log(`✅ Success! Status: ${response.status}`);
        console.log('Response type:', typeof response.data);
        if (Array.isArray(response.data)) {
          console.log(`Found array with ${response.data.length} elements`);
        } else {
          console.log('Response data keys:', Object.keys(response.data));
        }
      } catch (error) {
        console.log(`❌ Failed with status: ${error.response?.status || error.message}`);
      }
    }
    
    // Check analytical debug points
    console.log('\n4. Checking analytical debug points...');
    
    try {
      console.log('Attempting to access analytics debug endpoint for the team...');
      const debugResponse = await api.get(`/debug/analytics-data/2`);
      console.log('Response:', JSON.stringify(debugResponse.data, null, 2));
    } catch (error) {
      console.log('Error accessing debug endpoint:');
      console.log(`Status: ${error.response?.status || 'No response'}`);
      console.log('Message:', error.message);
    }
    
    // Try to get raw batting order data
    console.log('\n5. Attempting to get raw data via direct request...');
    try {
      // This is a lower-level request with fewer abstractions
      const rawResponse = await axios({
        method: 'get',
        url: 'https://www.lineupboss.app/api/games/14/batting-order',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        validateStatus: () => true  // Accept any status code
      });
      
      console.log(`Raw response status: ${rawResponse.status}`);
      console.log('Headers:', rawResponse.headers);
      console.log('Data type:', typeof rawResponse.data);
      console.log('Data preview:', JSON.stringify(rawResponse.data).substring(0, 300) + '...');
    } catch (error) {
      console.log('Error with raw request:', error.message);
    }
    
  } catch (error) {
    console.error('General error during debugging:', error.message);
  }
}

// Run the debug
debugBattingOrder();