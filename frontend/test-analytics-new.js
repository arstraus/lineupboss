/**
 * Analytics API Test with New Token
 * 
 * This script tests basic API access and the analytics endpoints
 */
const axios = require('axios');

// Set the new token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDcyOSwianRpIjoiZTMxNzc3YjUtYjkyOS00M2E5LWIyNTAtNDg4Nzc1ZGU3NDU4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjA3MjksImV4cCI6MTc0Mzk1NjcyOX0.x-2T5y0s2Tg1CX1-PM-ildtvIPeDcz4o8WsG24Di8X8';

// Setup API call with the correct URL
const api = axios.create({
  baseURL: 'https://www.lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Check if we can get teams
async function checkTeams() {
  console.log('BASIC API ACCESS TEST\n');
  
  try {
    console.log('Fetching teams...');
    const teamsResponse = await api.get('/teams');
    console.log('✅ Teams fetched successfully');
    console.log(`Found ${teamsResponse.data.length} teams`);
    
    // List teams
    console.log('\nTeams:');
    teamsResponse.data.forEach(team => {
      console.log(`ID: ${team.id}, Name: ${team.name}`);
    });
    
    return teamsResponse.data;
  } catch (error) {
    console.log('❌ Failed to fetch teams');
    console.log('Error:', error.response?.status || error.message);
    if (error.response?.data) {
      console.log('Response data:', error.response.data);
    }
    return [];
  }
}

// Test analytics for a specific team
async function testAnalytics(teamId) {
  console.log(`\n\nTESTING ANALYTICS FOR TEAM ID: ${teamId}\n`);
  
  let battingAnalyticsResponse;
  
  try {
    console.log('1. Testing team analytics endpoint...');
    const teamAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/analytics`);
    console.log('✅ Team analytics response received');
    console.log('Response data:');
    console.log('- has_data flag present:', teamAnalyticsResponse.data.hasOwnProperty('has_data'));
    console.log('- has_data value:', teamAnalyticsResponse.data.has_data);
    console.log('- total_games:', teamAnalyticsResponse.data.total_games);
    console.log('- games_by_month count:', Object.keys(teamAnalyticsResponse.data.games_by_month || {}).length);
    console.log('- games_by_day count:', Object.keys(teamAnalyticsResponse.data.games_by_day || {}).length);
    
    // Frontend logic for deciding what to display
    const hasGameData = teamAnalyticsResponse.data.has_data || 
                      (teamAnalyticsResponse.data.total_games > 0 && 
                      (Object.keys(teamAnalyticsResponse.data.games_by_month || {}).length > 0 || 
                        Object.values(teamAnalyticsResponse.data.games_by_day || {}).some(count => count > 0)));
    
    console.log('\nFrontend hasGameData evaluation:', hasGameData);
    console.log('Component would show:', hasGameData ? "ANALYTICS DATA" : "NO DATA MESSAGE");
  } catch (error) {
    console.log('❌ Team analytics error');
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log('Response:', error.response.data);
    } else {
      console.log('Error:', error.message);
    }
  }
  
  try {
    console.log('\n2. Testing batting analytics endpoint...');
    battingAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/batting-analytics`);
    console.log('✅ Batting analytics response received');
    console.log(`Found ${battingAnalyticsResponse.data.length} players`);
    
    // Check if any players have data
    const playersWithData = battingAnalyticsResponse.data.filter(p => p.has_data).length;
    console.log(`Players with has_data=true: ${playersWithData}/${battingAnalyticsResponse.data.length}`);
  } catch (error) {
    console.log('❌ Batting analytics error');
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log('Response:', error.response.data);
    } else {
      console.log('Error:', error.message);
    }
  }
  
  try {
    console.log('\n3. Testing fielding analytics endpoint...');
    const fieldingAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/fielding-analytics`);
    console.log('✅ Fielding analytics response received');
    console.log(`Found ${fieldingAnalyticsResponse.data.length} players`);
    
    // Check if any players have data
    const playersWithData = fieldingAnalyticsResponse.data.filter(p => p.has_data).length;
    console.log(`Players with has_data=true: ${playersWithData}/${fieldingAnalyticsResponse.data.length}`);
    
    // Frontend logic for player analytics
    const hasPlayerData = 
      (battingAnalyticsResponse?.data?.some(p => p.has_data) || 
       fieldingAnalyticsResponse.data.some(p => p.has_data));
    
    console.log('\nFrontend hasActualData evaluation:', hasPlayerData);
    console.log('Component would show:', hasPlayerData ? "ANALYTICS DATA" : "NO DATA MESSAGE");
  } catch (error) {
    console.log('❌ Fielding analytics error');
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log('Response:', error.response.data);
    } else {
      console.log('Error:', error.message);
    }
  }
}

// Run the test
async function run() {
  const teams = await checkTeams();
  
  if (teams.length > 0) {
    for (const team of teams) {
      await testAnalytics(team.id);
    }
  }
}

run();