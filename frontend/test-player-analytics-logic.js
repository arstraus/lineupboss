/**
 * Player Analytics Logic Test
 * 
 * This script tests the logic in PlayerAnalytics.jsx to determine whether
 * the "no data" message would be shown based on different API responses.
 */

// Define test cases that simulate different API responses
const testCases = [
  {
    name: "Case 1: One player with has_data=true, one without",
    data: {
      battingAnalytics: [
        { player_id: 1, name: "Player 1", has_data: true },
        { player_id: 2, name: "Player 2", has_data: false }
      ],
      fieldingAnalytics: [
        { player_id: 1, name: "Player 1", has_data: true },
        { player_id: 2, name: "Player 2", has_data: false }
      ]
    }
  },
  {
    name: "Case 2: All players with has_data=false",
    data: {
      battingAnalytics: [
        { player_id: 1, name: "Player 1", has_data: false },
        { player_id: 2, name: "Player 2", has_data: false }
      ],
      fieldingAnalytics: [
        { player_id: 1, name: "Player 1", has_data: false },
        { player_id: 2, name: "Player 2", has_data: false }
      ]
    }
  },
  {
    name: "Case 3: Empty arrays",
    data: {
      battingAnalytics: [],
      fieldingAnalytics: []
    }
  },
  {
    name: "Case 4: Missing has_data flag",
    data: {
      battingAnalytics: [
        { player_id: 1, name: "Player 1" },
        { player_id: 2, name: "Player 2" }
      ],
      fieldingAnalytics: [
        { player_id: 1, name: "Player 1" },
        { player_id: 2, name: "Player 2" }
      ]
    }
  },
  {
    name: "Case 5: None in batting but some in fielding",
    data: {
      battingAnalytics: [
        { player_id: 1, name: "Player 1", has_data: false },
        { player_id: 2, name: "Player 2", has_data: false }
      ],
      fieldingAnalytics: [
        { player_id: 1, name: "Player 1", has_data: true },
        { player_id: 2, name: "Player 2", has_data: false }
      ]
    }
  }
];

// This is the exact logic from PlayerAnalytics.jsx
function evaluateHasActualData(battingAnalytics, fieldingAnalytics) {
  // Check if we have data with content
  return (battingAnalytics.some(p => p.has_data) || fieldingAnalytics.some(p => p.has_data));
}

// Run all test cases
console.log("PLAYER ANALYTICS LOGIC TEST\n");

for (const testCase of testCases) {
  const { battingAnalytics, fieldingAnalytics } = testCase.data;
  const hasActualData = evaluateHasActualData(battingAnalytics, fieldingAnalytics);
  
  console.log(`\n${testCase.name}`);
  console.log("------------------------------------------------------");
  console.log("battingAnalytics:", JSON.stringify(battingAnalytics, null, 2));
  console.log("fieldingAnalytics:", JSON.stringify(fieldingAnalytics, null, 2));
  console.log("------------------------------------------------------");
  console.log("hasActualData evaluation:", hasActualData);
  console.log("Component would show:", hasActualData ? "ANALYTICS DATA" : "NO DATA MESSAGE");
  console.log("------------------------------------------------------");
}

// Check our test coverage of the logic
console.log("\nSUMMARY OF LOGIC PATHS TESTED:");
console.log("1. At least one player has has_data=true  → Should show analytics");
console.log("2. All players have has_data=false        → Should show 'no data' message");
console.log("3. Empty player arrays                    → Should show 'no data available' message (different logic)");
console.log("4. Missing has_data flag                  → Should show 'no data' message (has_data is undefined)");
console.log("5. One component has data, one doesn't    → Should show analytics");