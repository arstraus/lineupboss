/**
 * Check All Games for Team 2
 * 
 * This script checks all games for Team 2 to see if any have both 
 * batting orders and fielding rotations required for analytics.
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

// Check batting order for a game
async function checkBattingOrder(gameId) {
  try {
    const response = await api.get(`/games/${gameId}/batting-order`);
    if (response.data && response.data.length > 0) {
      const filledPositions = response.data.filter(p => p.player).length;
      return {
        exists: true,
        positions: response.data.length,
        filledPositions: filledPositions,
        complete: filledPositions > 0
      };
    } else {
      return { exists: false };
    }
  } catch (error) {
    return { exists: false, error: error.message };
  }
}

// Check fielding rotations for a game
async function checkFieldingRotations(gameId) {
  try {
    const response = await api.get(`/games/${gameId}/fielding-rotations`);
    if (response.data && Object.keys(response.data).length > 0) {
      return {
        exists: true,
        innings: Object.keys(response.data).length
      };
    } else {
      return { exists: false };
    }
  } catch (error) {
    return { exists: false, error: error.message };
  }
}

async function checkAllGames() {
  console.log(`CHECKING ALL GAMES FOR TEAM ${teamId}`);
  console.log('=================================\n');
  
  try {
    // Get games for the team
    console.log('Fetching games...');
    const gamesResponse = await api.get(`/teams/${teamId}/games`);
    console.log(`✅ Found ${gamesResponse.data.length} games\n`);
    
    console.log('GAME DATA SUMMARY:');
    console.log('=================');
    
    // Check each game
    let gamesWithBothData = 0;
    let gamesWithBattingOnly = 0;
    let gamesWithFieldingOnly = 0;
    let gamesWithNoData = 0;
    
    for (const game of gamesResponse.data) {
      console.log(`\nGame ${game.id}: ${game.opponent || 'Unnamed'} (${game.date || 'No date'})`);
      
      // Check batting order
      const battingData = await checkBattingOrder(game.id);
      if (battingData.exists) {
        console.log(`✅ Batting order: ${battingData.filledPositions}/${battingData.positions} positions filled`);
      } else {
        console.log('❌ No batting order');
      }
      
      // Check fielding rotations
      const fieldingData = await checkFieldingRotations(game.id);
      if (fieldingData.exists) {
        console.log(`✅ Fielding rotations: ${fieldingData.innings} innings`);
      } else {
        console.log('❌ No fielding rotations');
      }
      
      // Count game types
      if (battingData.exists && battingData.complete && fieldingData.exists) {
        gamesWithBothData++;
        console.log('✅ This game has BOTH batting and fielding data (should count for analytics)');
      } else if (battingData.exists && battingData.complete) {
        gamesWithBattingOnly++;
        console.log('⚠️ This game has ONLY batting data');
      } else if (fieldingData.exists) {
        gamesWithFieldingOnly++;
        console.log('⚠️ This game has ONLY fielding data');
      } else {
        gamesWithNoData++;
        console.log('❌ This game has NO data');
      }
    }
    
    console.log('\n\nSUMMARY:');
    console.log('========');
    console.log(`Total games: ${gamesResponse.data.length}`);
    console.log(`Games with BOTH batting & fielding: ${gamesWithBothData}`);
    console.log(`Games with ONLY batting data: ${gamesWithBattingOnly}`);
    console.log(`Games with ONLY fielding data: ${gamesWithFieldingOnly}`);
    console.log(`Games with NO data: ${gamesWithNoData}`);
    
    if (gamesWithBothData === 0) {
      console.log('\n🔍 CONCLUSION: No games have both batting and fielding data required for analytics');
      console.log('Solution: Add batting orders to games that already have fielding rotations');
    } else {
      console.log(`\n🔍 CONCLUSION: ${gamesWithBothData} games should be eligible for analytics`);
      console.log('There might be other requirements or a backend issue preventing analytics generation');
    }
    
  } catch (error) {
    console.error('Error checking games:', error.message);
  }
}

// Run the check
checkAllGames();