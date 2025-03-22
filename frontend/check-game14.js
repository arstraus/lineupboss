/**
 * Detailed Check for Game 14
 * 
 * This script verifies if Game 14 has complete batting order and fielding rotation data,
 * and why it might not be showing up in analytics.
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDcyOSwianRpIjoiZTMxNzc3YjUtYjkyOS00M2E5LWIyNTAtNDg4Nzc1ZGU3NDU4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjA3MjksImV4cCI6MTc0Mzk1NjcyOX0.x-2T5y0s2Tg1CX1-PM-ildtvIPeDcz4o8WsG24Di8X8';
const teamId = 2;
const gameId = 14;

// Setup API call with the correct URL
const api = axios.create({
  baseURL: 'https://www.lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

async function checkGameDetails() {
  console.log(`DETAILED CHECK FOR GAME ID ${gameId} (TEAM ${teamId})`);
  console.log('============================================\n');
  
  try {
    // Get game details
    console.log('1. Fetching game details...');
    const gameResponse = await api.get(`/games/${gameId}`);
    console.log('✅ Game details fetched successfully');
    console.log(`Opponent: ${gameResponse.data.opponent}`);
    console.log(`Date: ${gameResponse.data.date}`);
    console.log('');
    
    // Get batting order
    console.log('2. Checking batting order...');
    try {
      const battingResponse = await api.get(`/games/${gameId}/batting-order`);
      
      if (battingResponse.data && battingResponse.data.length > 0) {
        console.log(`✅ Batting order found with ${battingResponse.data.length} positions`);
        
        // Display batting order
        console.log('\nBatting Order:');
        battingResponse.data.forEach((position, index) => {
          console.log(`${index + 1}. ${position.player ? position.player.first_name + ' ' + position.player.last_name : 'Empty'}`);
        });
        
        // Check for empty positions
        const emptyPositions = battingResponse.data.filter(position => !position.player);
        if (emptyPositions.length > 0) {
          console.log(`\n⚠️ Found ${emptyPositions.length} empty positions in the batting order`);
          console.log('Analytics may require a complete batting order without empty positions');
        }
      } else {
        console.log('❌ No batting order found or it is empty');
      }
    } catch (error) {
      console.log(`❌ Error fetching batting order: ${error.message}`);
    }
    console.log('');
    
    // Get fielding rotations
    console.log('3. Checking fielding rotations...');
    try {
      const fieldingResponse = await api.get(`/games/${gameId}/fielding-rotations`);
      
      if (fieldingResponse.data && Object.keys(fieldingResponse.data).length > 0) {
        const innings = Object.keys(fieldingResponse.data);
        console.log(`✅ Fielding rotations found for ${innings.length} innings`);
        
        // Display fielding rotations
        console.log('\nFielding Rotations:');
        let emptyPositionsCount = 0;
        
        for (const inning of innings) {
          console.log(`\nInning ${inning}:`);
          const positions = fieldingResponse.data[inning];
          
          for (const position of Object.keys(positions)) {
            const player = positions[position];
            if (player) {
              console.log(`- ${position}: ${player.first_name} ${player.last_name}`);
            } else {
              console.log(`- ${position}: Empty`);
              emptyPositionsCount++;
            }
          }
        }
        
        if (emptyPositionsCount > 0) {
          console.log(`\n⚠️ Found ${emptyPositionsCount} empty positions in the fielding rotations`);
          console.log('Analytics may require complete fielding rotations without empty positions');
        }
      } else {
        console.log('❌ No fielding rotations found or they are empty');
      }
    } catch (error) {
      console.log(`❌ Error fetching fielding rotations: ${error.message}`);
    }
    console.log('');
    
    // Check player availability for this game
    console.log('4. Checking player availability...');
    try {
      const availabilityResponse = await api.get(`/games/${gameId}/player-availability`);
      
      if (availabilityResponse.data && availabilityResponse.data.length > 0) {
        const available = availabilityResponse.data.filter(p => p.status === 'available');
        const unavailable = availabilityResponse.data.filter(p => p.status === 'unavailable');
        const unknown = availabilityResponse.data.filter(p => p.status !== 'available' && p.status !== 'unavailable');
        
        console.log(`Player availability: ${available.length} available, ${unavailable.length} unavailable, ${unknown.length} unknown`);
      } else {
        console.log('No player availability data found');
      }
    } catch (error) {
      console.log(`Error fetching player availability: ${error.message}`);
    }
    console.log('');
    
    // Directly check analytics one more time
    console.log('5. Directly checking analytics endpoints...');
    try {
      // Team analytics
      const teamAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/analytics`);
      console.log('Team analytics response:');
      console.log('- has_data flag value:', teamAnalyticsResponse.data.has_data);
      console.log('- total_games:', teamAnalyticsResponse.data.total_games);
      console.log('- games_by_month:', JSON.stringify(teamAnalyticsResponse.data.games_by_month));
      console.log('- games_by_day:', JSON.stringify(teamAnalyticsResponse.data.games_by_day));
      
      // Check if game 14's date appears in the analytics
      const gameDate = new Date(gameResponse.data.date);
      const gameMonth = `${gameDate.getFullYear()}-${String(gameDate.getMonth() + 1).padStart(2, '0')}`;
      console.log(`\nChecking if game month (${gameMonth}) appears in analytics: ${teamAnalyticsResponse.data.games_by_month[gameMonth] ? 'YES' : 'NO'}`);
      
      // Get day of week
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const gameDay = days[gameDate.getDay()];
      console.log(`Checking if game day (${gameDay}) has a non-zero count: ${teamAnalyticsResponse.data.games_by_day[gameDay] > 0 ? 'YES' : 'NO'}`);
      
    } catch (error) {
      console.log(`❌ Error fetching analytics: ${error.message}`);
    }
    
    console.log('\n6. Making single direct request to debug endpoint...');
    try {
      // Try a special debug endpoint if it exists
      const debugResponse = await api.get(`/debug/analytics-data/${teamId}`);
      console.log('✅ Debug endpoint accessible');
      console.log('Debug data:', JSON.stringify(debugResponse.data, null, 2));
    } catch (error) {
      console.log(`❌ Debug endpoint not available: ${error.response?.status || error.message}`);
    }
    
    console.log('\nDIAGNOSIS COMPLETE');
    
  } catch (error) {
    console.error('Error during game data check:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Response:', error.response.data);
    }
  }
}

// Run the check
checkGameDetails();