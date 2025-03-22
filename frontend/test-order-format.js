/**
 * Test Batting Order Format Handling
 * 
 * This script compares the expected and actual formats of batting order data,
 * and how it would be processed by the analytics service.
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDcyOSwianRpIjoiZTMxNzc3YjUtYjkyOS00M2E5LWIyNTAtNDg4Nzc1ZGU3NDU4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjA3MjksImV4cCI6MTc0Mzk1NjcyOX0.x-2T5y0s2Tg1CX1-PM-ildtvIPeDcz4o8WsG24Di8X8';
const gameId = 14;
const teamId = 2;

// Setup API call with the correct URL
const api = axios.create({
  baseURL: 'https://www.lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Mock data in expected format
const expectedFormat = [
  {
    "position": 1,
    "player": {
      "id": 25,
      "first_name": "Player",
      "last_name": "One"
    }
  },
  {
    "position": 2,
    "player": {
      "id": 20,
      "first_name": "Player",
      "last_name": "Two"
    }
  }
];

async function testOrderFormat() {
  console.log('TESTING BATTING ORDER FORMAT HANDLING');
  console.log('====================================\n');
  
  try {
    // Fetch the actual batting order data
    console.log('1. Fetching actual batting order data...');
    const orderResponse = await api.get(`/games/${gameId}/batting-order`);
    console.log('Actual response format:');
    console.log(JSON.stringify(orderResponse.data, null, 2));
    
    // Fetch team players to map IDs to names
    console.log('\n2. Fetching team players to map IDs...');
    const playersResponse = await api.get(`/teams/${teamId}/players`);
    console.log(`Found ${playersResponse.data.length} players`);
    
    // Create a map of player IDs to names
    const playerMap = {};
    playersResponse.data.forEach(player => {
      playerMap[player.id] = {
        id: player.id,
        first_name: player.first_name,
        last_name: player.last_name,
        jersey_number: player.jersey_number
      };
    });
    
    console.log('\n3. Mapping order_data to player details...');
    // Try to map the order_data IDs to player names
    if (orderResponse.data && orderResponse.data.order_data && Array.isArray(orderResponse.data.order_data)) {
      const mappedOrder = orderResponse.data.order_data.map((playerId, index) => {
        const player = playerMap[playerId];
        return {
          position: index + 1,
          player: player ? player : { id: playerId, note: "Player not found" }
        };
      });
      
      console.log('Mapped batting order with player details:');
      console.log(JSON.stringify(mappedOrder, null, 2));
      
      // Count valid players in the order
      const validPlayers = mappedOrder.filter(pos => pos.player && pos.player.first_name).length;
      console.log(`\nValid players in batting order: ${validPlayers}/${mappedOrder.length}`);
      
      // Show how this would look in the expected format
      console.log('\nHow this SHOULD look in the expected format:');
      console.log(JSON.stringify(expectedFormat, null, 2));
    } else {
      console.log('Could not map player IDs, order_data not found or invalid');
    }
    
    // Summary of the issue
    console.log('\n4. ISSUE SUMMARY');
    console.log('================');
    console.log('Expected format: Array of objects with position and player details');
    console.log('Actual format: Object with game_id, id, and array of player IDs in order_data');
    console.log('\nThe analytics service and the BattingOrderTab.jsx component expect the format to be:');
    console.log('[{ position: 1, player: {id, first_name, last_name} }, ...]');
    console.log('\nBut the API is returning:');
    console.log('{ game_id: 14, id: 4, order_data: [25, 20, 16, ...] }');
    console.log('\nThis format mismatch is why the analytics service is not recognizing the batting order data');
    
  } catch (error) {
    console.error('Error during test:', error.message);
  }
}

// Run the test
testOrderFormat();