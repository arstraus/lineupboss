/**
 * Backend Status Check Script
 * 
 * This script tests API connectivity to see if the backend is responding 
 * properly after the analytics service fixes.
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2ODI0NywianRpIjoiMWQwZTliNzktMzhjOC00MzZlLWEzOWItYThkMmYzNWFlMWFkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjgyNDcsImV4cCI6MTc0Mzk2NDI0N30.YUo2Ya8H48SVxiYTAJLemXAKMNVMtgi-1Zrm-C6iR9w';
const teamId = 2;  // Team ID to test

// Setup API call
const api = axios.create({
  baseURL: 'https://www.lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

async function checkBackend() {
  console.log('BACKEND STATUS CHECK');
  console.log('===================\n');
  
  try {
    // 1. Basic Health Check
    console.log('1. Basic Health Check');
    console.log('-----------------');
    
    try {
      const response = await api.get('/');
      console.log('✅ API root endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Response: ${JSON.stringify(response.data)}\n`);
    } catch (error) {
      console.log('❌ API root endpoint failed');
      printErrorDetails(error);
    }
    
    // 2. Check Analytics Module Status
    console.log('2. Analytics Module Status');
    console.log('-----------------------');
    
    try {
      const response = await api.get('/analytics/status');
      console.log('✅ Analytics status endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Response: ${JSON.stringify(response.data)}\n`);
    } catch (error) {
      console.log('❌ Analytics status endpoint failed');
      printErrorDetails(error);
    }
    
    // 3. Teams List
    console.log('3. Teams Endpoint');
    console.log('----------------');
    
    try {
      const response = await api.get('/teams');
      console.log('✅ Teams endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Found ${response.data.length} teams\n`);
    } catch (error) {
      console.log('❌ Teams endpoint failed');
      printErrorDetails(error);
    }
    
    // 4. Team Analytics Endpoint
    console.log(`4. Team Analytics Endpoint (Team ID: ${teamId})`);
    console.log('----------------------------------------');
    
    try {
      const response = await api.get(`/analytics/teams/${teamId}/analytics`);
      console.log('✅ Team analytics endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Response: ${JSON.stringify(response.data)}\n`);
    } catch (error) {
      console.log('❌ Team analytics endpoint failed');
      printErrorDetails(error);
    }
    
    // 5. Batting Analytics Endpoint
    console.log(`5. Batting Analytics Endpoint (Team ID: ${teamId})`);
    console.log('-------------------------------------------');
    
    try {
      const response = await api.get(`/analytics/teams/${teamId}/batting-analytics`);
      console.log('✅ Batting analytics endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Found data for ${response.data.length} players\n`);
    } catch (error) {
      console.log('❌ Batting analytics endpoint failed');
      printErrorDetails(error);
    }
    
    // 6. Fielding Analytics Endpoint
    console.log(`6. Fielding Analytics Endpoint (Team ID: ${teamId})`);
    console.log('--------------------------------------------');
    
    try {
      const response = await api.get(`/analytics/teams/${teamId}/fielding-analytics`);
      console.log('✅ Fielding analytics endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Found data for ${response.data.length} players\n`);
    } catch (error) {
      console.log('❌ Fielding analytics endpoint failed');
      printErrorDetails(error);
    }
    
    // 7. Debug Endpoint
    console.log(`7. Debug Analytics Endpoint (Team ID: ${teamId})`);
    console.log('-------------------------------------------');
    
    try {
      const response = await api.get(`/analytics/teams/${teamId}/debug`);
      console.log('✅ Debug endpoint: Success!');
      console.log(`Status: ${response.status}`);
      console.log(`Response: ${JSON.stringify(response.data)}\n`);
    } catch (error) {
      console.log('❌ Debug endpoint failed');
      printErrorDetails(error);
    }
    
    console.log('BACKEND CHECK COMPLETE');
    
  } catch (error) {
    console.error('Error during backend check:', error.message);
  }
}

// Helper function to print error details
function printErrorDetails(error) {
  if (error.response) {
    // Server responded with an error
    console.log(`  Status: ${error.response.status}`);
    console.log(`  Response: ${JSON.stringify(error.response.data)}`);
  } else if (error.request) {
    // Request was made but no response received
    console.log('  No response received from server');
  } else {
    // Error in setting up the request
    console.log(`  Error message: ${error.message}`);
  }
  console.log('');
}

// Run the check
checkBackend();