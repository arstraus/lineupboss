/**
 * Check Teams Script
 * 
 * This script checks if we can get the teams list and validates
 * our API access.
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDM1NiwianRpIjoiMTM2MGM1NzgtMmYyMS00NDU5LTlkYzctYzc5NzRhYTgxYTI0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjAzNTYsImV4cCI6MTc0Mzk1NjM1Nn0.4auCDrNvCokfBAXHR6S8emsnRFoEEoc6hPNPeQSh8NA';

// Setup API call
const api = axios.create({
  baseURL: 'https://lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

async function checkTeams() {
  console.log('CHECKING API ACCESS AND TEAMS\n');
  
  // First check API health
  try {
    console.log('Testing API health...');
    const healthResponse = await api.get('/');
    console.log('✅ API is healthy');
    console.log('Response:', healthResponse.data);
  } catch (error) {
    console.log('❌ API health check failed');
    console.log('Error:', error.response?.status || error.message);
  }
  
  // Now check teams
  try {
    console.log('\nFetching teams...');
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
    return null;
  }
}

// Now check a specific team
async function checkTeam(teamId) {
  try {
    console.log(`\nFetching details for team ID ${teamId}...`);
    const teamResponse = await api.get(`/teams/${teamId}`);
    console.log('✅ Team details fetched successfully');
    console.log('Team name:', teamResponse.data.name);
    console.log('Team details:', teamResponse.data);
    
    // Check if team has games
    console.log(`\nFetching games for team ID ${teamId}...`);
    const gamesResponse = await api.get(`/teams/${teamId}/games`);
    console.log('✅ Games fetched successfully');
    console.log(`Found ${gamesResponse.data.length} games`);
    
    if (gamesResponse.data.length > 0) {
      console.log('\nSample games:');
      gamesResponse.data.slice(0, 3).forEach(game => {
        console.log(`ID: ${game.id}, Opponent: ${game.opponent}, Date: ${game.date || 'No date'}`);
      });
    }
  } catch (error) {
    console.log(`❌ Failed to fetch team details for ID ${teamId}`);
    console.log('Error:', error.response?.status || error.message);
  }
}

// Run the checks
async function run() {
  const teams = await checkTeams();
  
  if (teams && teams.length > 0) {
    // Check the first team in detail
    await checkTeam(teams[0].id);
  }
}

run();