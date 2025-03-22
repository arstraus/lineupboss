/**
 * Analytics Diagnostic Tool
 * 
 * This script performs a comprehensive diagnosis of the analytics endpoints
 * and data structures to help identify why analytics data might not be displaying.
 */
const axios = require('axios');

// Set the token and team ID
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDM1NiwianRpIjoiMTM2MGM1NzgtMmYyMS00NDU5LTlkYzctYzc5NzRhYTgxYTI0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjAzNTYsImV4cCI6MTc0Mzk1NjM1Nn0.4auCDrNvCokfBAXHR6S8emsnRFoEEoc6hPNPeQSh8NA';
const teamId = 2; // Using team ID 2

// Setup API call
const api = axios.create({
  baseURL: 'https://lineupboss.app/api',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Check if we can get games data first
async function diagnoseGameData() {
  console.log(`\n📊 ANALYTICS DIAGNOSIS FOR TEAM ID: ${teamId}\n`);
  console.log('STEP 1: Checking basic team and game data...\n');
  
  try {
    // Check team data first
    console.log('Fetching team data...');
    const teamResponse = await api.get(`/teams/${teamId}`);
    console.log(`✅ Team found: "${teamResponse.data.name}"\n`);
    
    // Check games data
    console.log('Fetching games data...');
    const gamesResponse = await api.get(`/teams/${teamId}/games`);
    
    if (gamesResponse.data.length === 0) {
      console.log('❌ NO GAMES FOUND. This is why analytics shows no data.\n');
      console.log('SOLUTION: Add some games to your team first.\n');
      return false;
    }
    
    console.log(`✅ Found ${gamesResponse.data.length} games\n`);
    
    // Check if games have dates
    const gamesWithDates = gamesResponse.data.filter(game => game.date);
    const gamesWithoutDates = gamesResponse.data.filter(game => !game.date);
    
    console.log(`Games with dates: ${gamesWithDates.length}`);
    console.log(`Games without dates: ${gamesWithoutDates.length}\n`);
    
    if (gamesWithDates.length === 0) {
      console.log('❌ NO GAMES HAVE DATES. Analytics requires games with dates.\n');
      console.log('SOLUTION: Add dates to your games.\n');
      return false;
    }
    
    // Print sample game data
    console.log('Sample game data:');
    for (let i = 0; i < Math.min(3, gamesResponse.data.length); i++) {
      const game = gamesResponse.data[i];
      console.log(`- Game ${i+1}: ${game.opponent || 'Unnamed'}, Date: ${game.date || 'No date'}, ID: ${game.id}`);
    }
    console.log('');
    
    return {
      teamId,
      gamesData: gamesResponse.data,
      gamesWithDates
    };
  } catch (error) {
    handleError(error, 'basic team/game data');
    return false;
  }
}

// Check batting order data for a sample of games
async function diagnoseBattingOrderData(gameData) {
  console.log('\nSTEP 2: Checking batting order data...\n');
  
  if (!gameData || !gameData.gamesWithDates.length) {
    console.log('❌ No valid games with dates to check batting orders.\n');
    return false;
  }
  
  try {
    // Take first 3 games with dates to check
    const gamesToCheck = gameData.gamesWithDates.slice(0, 3);
    let totalOrdersFound = 0;
    
    for (const game of gamesToCheck) {
      console.log(`Checking batting order for game: ${game.opponent || 'Unnamed'} (ID: ${game.id})...`);
      
      try {
        const orderResponse = await api.get(`/games/${game.id}/batting-order`);
        
        if (!orderResponse.data || !orderResponse.data.length) {
          console.log(`❌ No batting order found for this game\n`);
        } else {
          console.log(`✅ Found batting order with ${orderResponse.data.length} positions\n`);
          totalOrdersFound++;
        }
      } catch (error) {
        console.log(`❌ Error fetching batting order: ${error.message}\n`);
      }
    }
    
    if (totalOrdersFound === 0) {
      console.log('❌ NO BATTING ORDERS FOUND in sample games.\n');
      console.log('SOLUTION: Create batting orders for your games.\n');
    } else {
      console.log(`✅ Found batting orders in ${totalOrdersFound}/${gamesToCheck.length} sample games\n`);
    }
    
    return totalOrdersFound > 0;
  } catch (error) {
    handleError(error, 'batting order data');
    return false;
  }
}

// Check fielding rotation data for a sample of games
async function diagnoseFieldingData(gameData) {
  console.log('\nSTEP 3: Checking fielding rotation data...\n');
  
  if (!gameData || !gameData.gamesWithDates.length) {
    console.log('❌ No valid games with dates to check fielding rotations.\n');
    return false;
  }
  
  try {
    // Take first 3 games with dates to check
    const gamesToCheck = gameData.gamesWithDates.slice(0, 3);
    let totalRotationsFound = 0;
    
    for (const game of gamesToCheck) {
      console.log(`Checking fielding rotations for game: ${game.opponent || 'Unnamed'} (ID: ${game.id})...`);
      
      try {
        const rotationsResponse = await api.get(`/games/${game.id}/fielding-rotations`);
        
        if (!rotationsResponse.data || !Object.keys(rotationsResponse.data).length) {
          console.log(`❌ No fielding rotations found for this game\n`);
        } else {
          const inningsCount = Object.keys(rotationsResponse.data).length;
          console.log(`✅ Found fielding rotations for ${inningsCount} innings\n`);
          totalRotationsFound++;
        }
      } catch (error) {
        console.log(`❌ Error fetching fielding rotations: ${error.message}\n`);
      }
    }
    
    if (totalRotationsFound === 0) {
      console.log('❌ NO FIELDING ROTATIONS FOUND in sample games.\n');
      console.log('SOLUTION: Create fielding rotations for your games.\n');
    } else {
      console.log(`✅ Found fielding rotations in ${totalRotationsFound}/${gamesToCheck.length} sample games\n`);
    }
    
    return totalRotationsFound > 0;
  } catch (error) {
    handleError(error, 'fielding rotation data');
    return false;
  }
}

// Finally check the analytics endpoints
async function checkAnalyticsEndpoints() {
  console.log('\nSTEP 4: Testing analytics endpoints directly...\n');
  
  try {
    // Test team analytics endpoint
    console.log('Testing team analytics endpoint...');
    const teamAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/analytics`);
    
    console.log('Team analytics response:');
    console.log('- has_data flag present:', teamAnalyticsResponse.data.hasOwnProperty('has_data'));
    console.log('- has_data value:', teamAnalyticsResponse.data.has_data);
    console.log('- total_games:', teamAnalyticsResponse.data.total_games);
    console.log('- games_by_month count:', Object.keys(teamAnalyticsResponse.data.games_by_month || {}).length);
    console.log('- games_by_day count:', Object.keys(teamAnalyticsResponse.data.games_by_day || {}).length);
    
    // Evaluate using the exact same logic as the front-end component
    const hasGameData = teamAnalyticsResponse.data.has_data || 
                      (teamAnalyticsResponse.data.total_games > 0 && 
                      (Object.keys(teamAnalyticsResponse.data.games_by_month || {}).length > 0 || 
                        Object.values(teamAnalyticsResponse.data.games_by_day || {}).some(count => count > 0)));
    
    console.log('\nFrontend hasGameData evaluation:', hasGameData);
    console.log('Component would show:', hasGameData ? "ANALYTICS DATA" : "NO DATA MESSAGE\n");
    
    // Test player analytics endpoints
    console.log('\nTesting batting analytics endpoint...');
    const battingAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/batting-analytics`);
    
    console.log(`Found ${battingAnalyticsResponse.data.length} players with batting data`);
    const battingHasData = battingAnalyticsResponse.data.some(p => p.has_data);
    console.log('At least one player has batting data:', battingHasData);
    
    console.log('\nTesting fielding analytics endpoint...');
    const fieldingAnalyticsResponse = await api.get(`/analytics/teams/${teamId}/fielding-analytics`);
    
    console.log(`Found ${fieldingAnalyticsResponse.data.length} players with fielding data`);
    const fieldingHasData = fieldingAnalyticsResponse.data.some(p => p.has_data);
    console.log('At least one player has fielding data:', fieldingHasData);
    
    // Evaluate using the exact same logic as the front-end component
    const hasPlayerData = battingHasData || fieldingHasData;
    
    console.log('\nFrontend hasActualData evaluation:', hasPlayerData);
    console.log('Component would show:', hasPlayerData ? "ANALYTICS DATA" : "NO DATA MESSAGE");
    
    return {
      teamAnalytics: {
        hasData: hasGameData,
        responseData: teamAnalyticsResponse.data
      },
      playerAnalytics: {
        hasData: hasPlayerData,
        battingData: battingAnalyticsResponse.data,
        fieldingData: fieldingAnalyticsResponse.data
      }
    };
  } catch (error) {
    handleError(error, 'analytics endpoints');
    return false;
  }
}

// Error handling helper
function handleError(error, context) {
  console.error(`\n❌ Error fetching ${context}:`);
  if (error.response) {
    console.error(`Status: ${error.response.status}`);
    console.error('Response:', error.response.data);
  } else if (error.request) {
    console.error('No response received from server');
  } else {
    console.error(`Error message: ${error.message}`);
  }
  console.error('');
}

// Run all diagnostic checks
async function runDiagnostics() {
  try {
    const gameData = await diagnoseGameData();
    
    if (gameData) {
      const hasBattingOrders = await diagnoseBattingOrderData(gameData);
      const hasFieldingRotations = await diagnoseFieldingData(gameData);
      const analyticsResults = await checkAnalyticsEndpoints();
      
      console.log('\n📋 DIAGNOSTIC SUMMARY:');
      console.log('=====================');
      
      if (!gameData.gamesWithDates.length) {
        console.log('❌ No games with dates found');
        console.log('    This is a critical requirement for analytics.');
      } else {
        console.log(`✅ Found ${gameData.gamesWithDates.length} games with dates`);
      }
      
      if (!hasBattingOrders) {
        console.log('❌ No batting orders found in sample games');
        console.log('    Batting orders are required for player batting analytics.');
      } else {
        console.log('✅ Batting orders found in at least one game');
      }
      
      if (!hasFieldingRotations) {
        console.log('❌ No fielding rotations found in sample games');
        console.log('    Fielding rotations are required for player fielding analytics.');
      } else {
        console.log('✅ Fielding rotations found in at least one game');
      }
      
      if (analyticsResults) {
        if (analyticsResults.teamAnalytics.hasData) {
          console.log('✅ Team analytics has data to display');
        } else {
          console.log('❌ Team analytics lacks data to display');
          if (analyticsResults.teamAnalytics.responseData.has_data === false) {
            console.log('    The has_data flag is explicitly set to false');
          }
        }
        
        if (analyticsResults.playerAnalytics.hasData) {
          console.log('✅ Player analytics has data to display');
        } else {
          console.log('❌ Player analytics lacks data to display');
        }
      }
      
      console.log('\n🔍 CONCLUSION:');
      if (
        (!gameData.gamesWithDates.length) || 
        (!hasBattingOrders && !hasFieldingRotations) ||
        (analyticsResults && !analyticsResults.teamAnalytics.hasData && !analyticsResults.playerAnalytics.hasData)
      ) {
        console.log('Insufficient data detected. The error messages are correct.');
        console.log('To fix, ensure you have:');
        console.log('1. Games with valid dates');
        console.log('2. Complete batting orders in games');
        console.log('3. Complete fielding rotations in games');
      } else if (analyticsResults) {
        if (!analyticsResults.teamAnalytics.hasData) {
          console.log('Team analytics should show "no data" message (correctly)');
        }
        if (!analyticsResults.playerAnalytics.hasData) {
          console.log('Player analytics should show "no data" message (correctly)');
        }
        if (analyticsResults.teamAnalytics.hasData || analyticsResults.playerAnalytics.hasData) {
          console.log('Some analytics data exists and should be displayed');
          console.log('There may be an issue with the frontend logic or backend API response');
        }
      }
    }
  } catch (error) {
    console.error('Diagnostic process failed:', error);
  }
}

// Run the diagnostics
runDiagnostics();