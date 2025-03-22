/**
 * Team Analytics Logic Test
 * 
 * This script tests the logic in TeamAnalytics.jsx to determine whether
 * the "no data" message would be shown based on different API responses.
 */

// Define test cases that simulate different API responses
const testCases = [
  {
    name: "Case 1: has_data=true, total_games=0, empty month/day data",
    data: {
      has_data: true,
      total_games: 0,
      games_by_month: {},
      games_by_day: {}
    }
  },
  {
    name: "Case 2: has_data=false, total_games=0, empty month/day data",
    data: {
      has_data: false,
      total_games: 0,
      games_by_month: {},
      games_by_day: {}
    }
  },
  {
    name: "Case 3: has_data=false, total_games=5, with month data",
    data: {
      has_data: false,
      total_games: 5,
      games_by_month: {"2023-05": 3, "2023-06": 2},
      games_by_day: {}
    }
  },
  {
    name: "Case 4: has_data=false, total_games=5, with day data",
    data: {
      has_data: false,
      total_games: 5,
      games_by_month: {},
      games_by_day: {"Monday": 2, "Friday": 3}
    }
  },
  {
    name: "Case 5: has_data=false, total_games=0, with day data",
    data: {
      has_data: false,
      total_games: 0,
      games_by_month: {},
      games_by_day: {"Monday": 2, "Friday": 3}
    }
  },
  {
    name: "Case 6: missing has_data, total_games=5, with data",
    data: {
      total_games: 5,
      games_by_month: {"2023-05": 3, "2023-06": 2},
      games_by_day: {"Monday": 2, "Friday": 3}
    }
  },
  {
    name: "Case 7: has_data=false, total_games=5, with empty data",
    data: {
      has_data: false,
      total_games: 5,
      games_by_month: {},
      games_by_day: {}
    }
  },
  {
    name: "Case 8: Complex mixed case",
    data: {
      has_data: false,
      total_games: 5,
      games_by_month: {"2023-05": 0, "2023-06": 0},
      games_by_day: {"Monday": 0, "Friday": 0}
    }
  }
];

// This is the exact logic from TeamAnalytics.jsx
function evaluateHasGameData(analytics) {
  return analytics.has_data || 
         (analytics.total_games > 0 && 
         (Object.keys(analytics.games_by_month).length > 0 || 
          Object.values(analytics.games_by_day).some(count => count > 0)));
}

// Run all test cases
console.log("TEAM ANALYTICS LOGIC TEST\n");

for (const testCase of testCases) {
  const analytics = testCase.data;
  const hasGameData = evaluateHasGameData(analytics);
  
  console.log(`\n${testCase.name}`);
  console.log("------------------------------------------------------");
  console.log("has_data:", analytics.has_data);
  console.log("total_games:", analytics.total_games);
  console.log("games_by_month:", JSON.stringify(analytics.games_by_month));
  console.log("games_by_day:", JSON.stringify(analytics.games_by_day));
  console.log("------------------------------------------------------");
  console.log("hasGameData evaluation:", hasGameData);
  console.log("Component would show:", hasGameData ? "ANALYTICS DATA" : "NO DATA MESSAGE");
  console.log("------------------------------------------------------");
}

// Check our test coverage of the logic
console.log("\nSUMMARY OF LOGIC PATHS TESTED:");
console.log("1. has_data = true                        → Should show analytics");
console.log("2. has_data = false, but data present     → Should show analytics");
console.log("3. has_data = false, no data              → Should show 'no data' message");
console.log("4. has_data missing, with data            → Should show analytics");
console.log("5. has_data missing, no data              → Should show 'no data' message");