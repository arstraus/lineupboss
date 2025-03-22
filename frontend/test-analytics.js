// Simple script to test the analytics API response
const axios = require('axios');

// Set the token and team ID
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDExMiwianRpIjoiNWFkYTg2ODMtOWZhMC00ZDkyLThkYTMtNDEzYzE4ODMzYTI5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjAxMTIsImV4cCI6MTc0Mzk1NjExMn0._sIiyq7OHDcBLHsayQEzGhUDgzyHGYLISqajvERm6LQ';
const teamId = 2; // Use team ID 2

// Setup API call
const api = axios.create({
  baseURL: 'https://lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

async function testAnalytics() {
  try {
    console.log(`Testing team analytics for team ID: ${teamId}`);
    
    // Test team analytics
    const teamResponse = await api.get(`/analytics/teams/${teamId}/analytics`);
    console.log('\n===== TEAM ANALYTICS =====');
    console.log('Status:', teamResponse.status);
    console.log('has_data flag present:', teamResponse.data.hasOwnProperty('has_data'));
    console.log('has_data value:', teamResponse.data.has_data);
    console.log('total_games:', teamResponse.data.total_games);
    console.log('Data structure:', Object.keys(teamResponse.data).join(', '));
    
    // Check if there's actual game data according to frontend logic
    const hasGameData = teamResponse.data.has_data || 
                      (teamResponse.data.total_games > 0 && 
                      (Object.keys(teamResponse.data.games_by_month).length > 0 || 
                        Object.values(teamResponse.data.games_by_day).some(count => count > 0)));
    
    console.log('\nFrontend hasGameData evaluation:', hasGameData);
    console.log('games_by_month count:', Object.keys(teamResponse.data.games_by_month).length);
    console.log('games_by_day has non-zero values:', Object.values(teamResponse.data.games_by_day).some(count => count > 0));
    
    // Print sample of month and day data if available
    if (Object.keys(teamResponse.data.games_by_month).length > 0) {
      console.log('\nSample month data:', Object.entries(teamResponse.data.games_by_month).slice(0, 3));
    }
    
    if (Object.keys(teamResponse.data.games_by_day).length > 0) {
      console.log('Sample day data:', teamResponse.data.games_by_day);
    }
    
  } catch (error) {
    console.error('Error occurred:');
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Status:', error.response.status);
      console.error('Headers:', error.response.headers);
      console.error('Data:', error.response.data);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error setting up request:', error.message);
    }
  }
}

// Run the test
testAnalytics();