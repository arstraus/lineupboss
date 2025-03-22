/**
 * Detailed Check for Team 2 Data
 * 
 * This script checks the basic data for team 2 to investigate 
 * why analytics might not be showing data that exists in the database
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDcyOSwianRpIjoiZTMxNzc3YjUtYjkyOS00M2E5LWIyNTAtNDg4Nzc1ZGU3NDU4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjA3MjksImV4cCI6MTc0Mzk1NjcyOX0.x-2T5y0s2Tg1CX1-PM-ildtvIPeDcz4o8WsG24Di8X8';
const teamId = 2;

// Setup API call with the correct URL
const api = axios.create({
  baseURL: 'https://www.lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

async function checkTeamDetails() {
  console.log(`DETAILED CHECK FOR TEAM ID ${teamId}`);
  console.log('===============================\n');
  
  try {
    // Get team details
    console.log('1. Fetching team details...');
    const teamResponse = await api.get(`/teams/${teamId}`);
    console.log('✅ Team details fetched successfully');
    console.log(`Team name: ${teamResponse.data.name}`);
    console.log('');
    
    // Get players for the team
    console.log('2. Fetching players for the team...');
    const playersResponse = await api.get(`/teams/${teamId}/players`);
    console.log('✅ Players fetched successfully');
    console.log(`Found ${playersResponse.data.length} players`);
    console.log('\nPlayers:');
    
    // Display player details
    playersResponse.data.forEach((player, index) => {
      console.log(`${index + 1}. ${player.first_name} ${player.last_name} (#${player.jersey_number})`);
    });
    console.log('');
    
    // Get games for the team
    console.log('3. Fetching games for the team...');
    const gamesResponse = await api.get(`/teams/${teamId}/games`);
    console.log('✅ Games fetched successfully');
    console.log(`Found ${gamesResponse.data.length} games`);
    
    // Check games with dates
    const gamesWithDates = gamesResponse.data.filter(game => game.date);
    const gamesWithoutDates = gamesResponse.data.filter(game => !game.date);
    
    console.log(`Games with dates: ${gamesWithDates.length}`);
    console.log(`Games without dates: ${gamesWithoutDates.length}`);
    
    // Display game details
    console.log('\nGames:');
    gamesResponse.data.forEach((game, index) => {
      console.log(`${index + 1}. Opponent: ${game.opponent || 'Unnamed'}, Date: ${game.date || 'No date'}, ID: ${game.id}`);
      
      // Check if it has a date
      if (!game.date) {
        console.log(`   ⚠️ This game has no date set, which is required for analytics`);
      }
    });
    console.log('');
    
    // Check batting orders and fielding rotations for a few games
    console.log('4. Checking game data (batting orders and fielding)...');
    
    // Take the first 3 games to check in detail
    const gamesToCheck = gamesResponse.data.slice(0, Math.min(3, gamesResponse.data.length));
    
    for (const game of gamesToCheck) {
      console.log(`\nGame: ${game.opponent || 'Unnamed'} (ID: ${game.id})`);
      console.log(`Date: ${game.date || 'No date'}`);
      
      try {
        // Check batting order
        const battingResponse = await api.get(`/games/${game.id}/batting-order`);
        if (battingResponse.data && battingResponse.data.length > 0) {
          console.log(`✅ Batting order: ${battingResponse.data.length} positions filled`);
        } else {
          console.log(`❌ No batting order set for this game`);
        }
      } catch (error) {
        console.log(`❌ Error fetching batting order: ${error.message}`);
      }
      
      try {
        // Check fielding rotations
        const fieldingResponse = await api.get(`/games/${game.id}/fielding-rotations`);
        if (fieldingResponse.data && Object.keys(fieldingResponse.data).length > 0) {
          const innings = Object.keys(fieldingResponse.data).length;
          console.log(`✅ Fielding rotations: ${innings} innings defined`);
        } else {
          console.log(`❌ No fielding rotations set for this game`);
        }
      } catch (error) {
        console.log(`❌ Error fetching fielding rotations: ${error.message}`);
      }
    }
    
    // Check analytics again
    console.log('\n5. Re-checking analytics endpoints...');
    try {
      const teamAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/analytics`);
      console.log('Team analytics response:');
      console.log('- has_data flag value:', teamAnalyticsResponse.data.has_data);
      console.log('- total_games:', teamAnalyticsResponse.data.total_games);
      console.log('- games_by_month:', teamAnalyticsResponse.data.games_by_month);
      console.log('- games_by_day:', teamAnalyticsResponse.data.games_by_day);
    } catch (error) {
      console.log(`❌ Team analytics error: ${error.message}`);
    }
    
    console.log('\n6. Checking API rate limiting...');
    console.log('Attempting multiple rapid requests to see if rate limiting is an issue...');
    
    // Make a few rapid requests to check for rate limiting
    let successCount = 0;
    let failureCount = 0;
    
    for (let i = 0; i < 3; i++) {
      try {
        await api.get('/teams');
        successCount++;
      } catch (error) {
        failureCount++;
        console.log(`  Request ${i+1} failed: ${error.response?.status || error.message}`);
      }
    }
    
    console.log(`Rapid request results: ${successCount} succeeded, ${failureCount} failed`);
    
    console.log('\nDIAGNOSIS COMPLETE');
    
  } catch (error) {
    console.error('Error during team data check:', error.message);
  }
}

// Run the check
checkTeamDetails();