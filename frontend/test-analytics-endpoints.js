/**
 * Analytics Endpoints Test
 * 
 * This script directly tests the analytics endpoints to diagnose issues 
 * with the analytics data display.
 */
const axios = require('axios');

// Set the token and team ID
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDM1NiwianRpIjoiMTM2MGM1NzgtMmYyMS00NDU5LTlkYzctYzc5NzRhYTgxYTI0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjAzNTYsImV4cCI6MTc0Mzk1NjM1Nn0.4auCDrNvCokfBAXHR6S8emsnRFoEEoc6hPNPeQSh8NA';

// Setup API call
const api = axios.create({
  baseURL: 'https://lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Check the analytics endpoints for multiple team IDs
async function testAnalyticsEndpoints() {
  console.log('TESTING ANALYTICS ENDPOINTS');
  console.log('==========================\n');
  
  // Try multiple team IDs since we're not sure which one to use
  for (const teamId of [1, 2, 3, 4, 5]) {
    try {
      console.log(`\n🔍 Checking Team ID: ${teamId}\n`);
      
      // Test team analytics endpoint
      console.log('Testing team analytics endpoint...');
      try {
        const teamAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/analytics`);
        console.log('✅ Team analytics response received');
        console.log('has_data flag present:', teamAnalyticsResponse.data.hasOwnProperty('has_data'));
        console.log('has_data value:', teamAnalyticsResponse.data.has_data);
        console.log('total_games:', teamAnalyticsResponse.data.total_games);
        
        // Check months and days data
        const monthsCount = Object.keys(teamAnalyticsResponse.data.games_by_month || {}).length;
        const daysCount = Object.keys(teamAnalyticsResponse.data.games_by_day || {}).length;
        console.log(`games_by_month entries: ${monthsCount}`);
        console.log(`games_by_day entries: ${daysCount}`);
        
        // Show some sample data if available
        if (monthsCount > 0) {
          console.log('Sample months data:', Object.entries(teamAnalyticsResponse.data.games_by_month).slice(0, 2));
        }
        if (daysCount > 0) {
          console.log('Sample days data:', Object.entries(teamAnalyticsResponse.data.games_by_day).slice(0, 2));
        }
        
        // Frontend logic for deciding what to display
        const hasGameData = teamAnalyticsResponse.data.has_data || 
                          (teamAnalyticsResponse.data.total_games > 0 && 
                          (Object.keys(teamAnalyticsResponse.data.games_by_month || {}).length > 0 || 
                            Object.values(teamAnalyticsResponse.data.games_by_day || {}).some(count => count > 0)));
        
        console.log('Frontend hasGameData evaluation:', hasGameData);
        console.log('Component would show:', hasGameData ? "ANALYTICS DATA" : "NO DATA MESSAGE");
      } catch (error) {
        console.log(`❌ Team analytics error: ${error.response?.status || error.message}`);
      }
      
      // Test player batting analytics endpoint
      console.log('\nTesting batting analytics endpoint...');
      try {
        const battingAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/batting-analytics`);
        console.log('✅ Batting analytics response received');
        console.log(`Found ${battingAnalyticsResponse.data.length} players`);
        
        // Check has_data flag on players
        const playersWithData = battingAnalyticsResponse.data.filter(p => p.has_data).length;
        console.log(`Players with has_data=true: ${playersWithData}/${battingAnalyticsResponse.data.length}`);
        
        if (battingAnalyticsResponse.data.length > 0) {
          // Show sample player data
          console.log('Sample player data:');
          console.log(JSON.stringify(battingAnalyticsResponse.data[0], null, 2).slice(0, 500) + '...');
        }
      } catch (error) {
        console.log(`❌ Batting analytics error: ${error.response?.status || error.message}`);
      }
      
      // Test player fielding analytics endpoint
      console.log('\nTesting fielding analytics endpoint...');
      try {
        const fieldingAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/fielding-analytics`);
        console.log('✅ Fielding analytics response received');
        console.log(`Found ${fieldingAnalyticsResponse.data.length} players`);
        
        // Check has_data flag on players
        const playersWithData = fieldingAnalyticsResponse.data.filter(p => p.has_data).length;
        console.log(`Players with has_data=true: ${playersWithData}/${fieldingAnalyticsResponse.data.length}`);
      } catch (error) {
        console.log(`❌ Fielding analytics error: ${error.response?.status || error.message}`);
      }
      
      console.log('\n-----------------------------------');
    } catch (error) {
      console.error(`Error testing team ${teamId}:`, error.message);
    }
  }
}

// Run the diagnostics
testAnalyticsEndpoints();