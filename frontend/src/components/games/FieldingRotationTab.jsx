import React, { useState, useEffect, useCallback } from "react";
import { getFieldingRotations, saveFieldingRotation, getPlayerAvailability, getBattingOrder } from "../../services/api";

// Constants from constants.js
const POSITIONS = ["Pitcher", "Catcher", "1B", "2B", "3B", "SS", "LF", "RF", "LC", "RC", "Bench"];
const INFIELD = ["Pitcher", "1B", "2B", "3B", "SS"];
const OUTFIELD = ["Catcher", "LF", "RF", "LC", "RC"];
const FIELD_POSITIONS = POSITIONS.filter(pos => pos !== "Bench");

const FieldingRotationTab = ({ gameId, players, innings = 6 }) => {
  const [rotations, setRotations] = useState({});
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [validationErrors, setValidationErrors] = useState({});
  const [battingOrder, setBattingOrder] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Get player availability
      const availabilityResponse = await getPlayerAvailability(gameId);
      const availabilityMap = {};
      availabilityResponse.data.forEach(item => {
        availabilityMap[item.player_id] = item.available;
      });
      
      // Filter available players
      const availPlayers = players.filter(player => 
        availabilityMap[player.id] !== false
      ).map(player => ({
        id: player.id,
        name: player.full_name,
        jersey_number: player.jersey_number
      }));
      
      setAvailablePlayers(availPlayers);
      
      // Get batting order
      try {
        const battingOrderResponse = await getBattingOrder(gameId);
        if (battingOrderResponse.data && battingOrderResponse.data.order_data) {
          setBattingOrder(battingOrderResponse.data.order_data);
        } else {
          setBattingOrder([]);
        }
      } catch (err) {
        // If no batting order exists yet
        setBattingOrder([]);
        console.log("No batting order found or error fetching batting order");
      }
      
      // Get fielding rotations
      try {
        const rotationsResponse = await getFieldingRotations(gameId);
        
        // Create a map of inning to positions
        const rotationsMap = {};
        rotationsResponse.data.forEach(rotation => {
          rotationsMap[rotation.inning] = rotation.positions || {};
        });
        
        setRotations(rotationsMap);
      } catch (err) {
        // If no rotations exist yet, initialize an empty object
        setRotations({});
      }
      
      setError("");
    } catch (err) {
      setError("Failed to load fielding rotation data. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [gameId, players]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Get position count summary for a player
  const getPlayerPositionSummary = (playerId) => {
    const summary = {
      infield: 0,
      outfield: 0,
      bench: 0,
      positions: {}
    };
    
    // Generate array of innings
    const inningsArray = Array.from({ length: innings }, (_, i) => i + 1);
    
    inningsArray.forEach(inning => {
      const inningRotation = rotations[inning] || {};
      let found = false;
      
      // Look for the player in this inning
      for (const [position, pid] of Object.entries(inningRotation)) {
        if (pid === playerId) {
          // Count by position type
          if (INFIELD.includes(position)) {
            summary.infield++;
          } else if (OUTFIELD.includes(position)) {
            summary.outfield++;
          }
          
          // Count specific positions
          if (!summary.positions[position]) {
            summary.positions[position] = 0;
          }
          summary.positions[position]++;
          
          found = true;
          break;
        }
      }
      
      // If player is not found in any position in this inning, they're on the bench
      if (!found) {
        summary.bench++;
      }
    });
    
    return summary;
  };
  
  // Validate rotations before saving
  const validateRotations = () => {
    const errors = {};
    const playerErrors = {};
    
    // Generate array of innings
    const inningsArray = Array.from({ length: innings }, (_, i) => i + 1);
    
    // Check each inning
    inningsArray.forEach(inning => {
      const inningErrors = [];
      const inningRotation = rotations[inning] || {};
      
      // 1. Check for missing positions
      const assignedPositions = Object.keys(inningRotation);
      const missingPositions = FIELD_POSITIONS.filter(pos => !assignedPositions.includes(pos));
      
      if (missingPositions.length > 0) {
        inningErrors.push(`Missing positions: ${missingPositions.join(', ')}`);
      }
      
      // 2. Check for duplicate player assignments in an inning
      const positionsByPlayer = {};
      Object.entries(inningRotation).forEach(([position, playerId]) => {
        if (!positionsByPlayer[playerId]) {
          positionsByPlayer[playerId] = [];
        }
        positionsByPlayer[playerId].push(position);
      });
      
      const duplicates = Object.entries(positionsByPlayer)
        .filter(([_, positions]) => positions.length > 1)
        .map(([playerId, positions]) => {
          const player = availablePlayers.find(p => p.id === parseInt(playerId));
          return `#${player?.jersey_number} ${player?.name}: ${positions.join(', ')}`;
        });
      
      if (duplicates.length > 0) {
        inningErrors.push(`Players assigned multiple positions: ${duplicates.join('; ')}`);
      }
      
      if (inningErrors.length > 0) {
        errors[inning] = inningErrors;
      }
    });
    
    // 3. Check if players play the same position more than once in the game
    availablePlayers.forEach(player => {
      const playerErrs = [];
      const positionSummary = getPlayerPositionSummary(player.id);
      
      // Check for duplicate positions
      const repeatPositions = Object.entries(positionSummary.positions)
        .filter(([_, count]) => count > 1)
        .map(([position, count]) => `${position} (${count} times)`);
      
      if (repeatPositions.length > 0) {
        playerErrs.push(`Plays same position multiple times: ${repeatPositions.join(', ')}`);
      }
      
      // 4. Check for consecutive infield or outfield innings
      for (let i = 1; i < innings; i++) {
        const currentInning = rotations[i] || {};
        const nextInning = rotations[i + 1] || {};
        
        let currentPosition = null;
        let nextPosition = null;
        
        // Find position in current inning
        for (const [pos, pid] of Object.entries(currentInning)) {
          if (pid === player.id) {
            currentPosition = pos;
            break;
          }
        }
        
        // Find position in next inning
        for (const [pos, pid] of Object.entries(nextInning)) {
          if (pid === player.id) {
            nextPosition = pos;
            break;
          }
        }
        
        // Check for consecutive infield innings
        if (currentPosition && nextPosition) {
          if (INFIELD.includes(currentPosition) && INFIELD.includes(nextPosition)) {
            playerErrs.push(`Plays infield in consecutive innings (${i} and ${i+1})`);
          }
          
          // Check for consecutive outfield innings
          if (OUTFIELD.includes(currentPosition) && OUTFIELD.includes(nextPosition)) {
            playerErrs.push(`Plays outfield in consecutive innings (${i} and ${i+1})`);
          }
        }
      }
      
      if (playerErrs.length > 0) {
        playerErrors[player.id] = playerErrs;
      }
    });
    
    // Combine inning errors and player errors
    setValidationErrors({ innings: errors, players: playerErrors });
    
    return Object.keys(errors).length === 0 && Object.keys(playerErrors).length === 0;
  };

  const handleSaveRotation = async (forceIgnoreValidation = false) => {
    try {
      // Validate rotations
      const isValid = validateRotations();
      
      // Show validation errors but don't block saving if forceIgnoreValidation is true
      if (!isValid && !forceIgnoreValidation) {
        setError("There are validation errors. Click 'Save Anyway' if you need to save despite these issues.");
        return;
      }
      
      setSaving(true);
      setSuccess("");
      setError("");
      
      // Generate array of innings
      const inningsArray = Array.from({ length: innings }, (_, i) => i + 1);
      
      // Save each inning
      for (const inning of inningsArray) {
        await saveFieldingRotation(gameId, inning, rotations[inning] || {});
      }
      
      setSuccess(isValid ? 
        "Fielding rotations saved successfully." :
        "Fielding rotations saved with validation issues.");
    } catch (err) {
      setError("Failed to save fielding rotations. Please try again.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handlePositionChange = (player, inning, position) => {
    // Create a new rotation for the specified inning if it doesn't exist
    const inningRotation = rotations[inning] || {};
    
    // Update the position with the player ID
    const updatedRotation = {
      ...inningRotation,
      [position]: player.id
    };
    
    // Update the rotations state
    setRotations({
      ...rotations,
      [inning]: updatedRotation
    });
  };

  const handleClearPosition = (inning, position) => {
    // Create a copy of current rotations
    const inningRotation = { ...rotations[inning] };
    
    // Delete the position from the rotation
    delete inningRotation[position];
    
    // Update the rotations state
    setRotations({
      ...rotations,
      [inning]: inningRotation
    });
  };

  const autoAssignPositions = (inning) => {
    // Get current rotation
    const currentRotation = rotations[inning] || {};
    
    // Get unassigned players
    const assignedPlayerIds = Object.values(currentRotation);
    const unassignedPlayers = availablePlayers.filter(
      player => !assignedPlayerIds.includes(player.id)
    );
    
    // Generate default assignments
    const newRotation = { ...currentRotation };
    
    // First, try to assign catchers
    const catcherPosition = POSITIONS.find(pos => pos === "Catcher");
    if (!newRotation[catcherPosition] && unassignedPlayers.length > 0) {
      // Find a player that can play catcher
      const catcherPlayer = unassignedPlayers.find(player => {
        // Check if player can play catcher (would need to extend player data)
        return true; // For now, assume any player can play catcher
      });
      
      if (catcherPlayer) {
        newRotation[catcherPosition] = catcherPlayer.id;
        // Remove from unassigned
        const index = unassignedPlayers.findIndex(p => p.id === catcherPlayer.id);
        unassignedPlayers.splice(index, 1);
      }
    }
    
    // Then assign infield positions
    for (const position of INFIELD) {
      if (!newRotation[position] && unassignedPlayers.length > 0) {
        newRotation[position] = unassignedPlayers[0].id;
        unassignedPlayers.shift();
      }
    }
    
    // Then assign outfield positions
    for (const position of OUTFIELD) {
      if (position !== "Catcher" && !newRotation[position] && unassignedPlayers.length > 0) {
        newRotation[position] = unassignedPlayers[0].id;
        unassignedPlayers.shift();
      }
    }
    
    // Update rotations
    setRotations({
      ...rotations,
      [inning]: newRotation
    });
  };

  const autoAssignAllInnings = () => {
    // Generate array of innings
    const inningsArray = Array.from({ length: innings }, (_, i) => i + 1);
    
    // Auto-assign each inning
    inningsArray.forEach(inning => {
      autoAssignPositions(inning);
    });
  };

  const copyFromPreviousInning = (inning) => {
    if (inning > 1) {
      const previousInning = inning - 1;
      const previousRotation = rotations[previousInning] || {};
      
      setRotations({
        ...rotations,
        [inning]: { ...previousRotation }
      });
    }
  };

  if (loading) {
    return <div className="text-center mt-3"><div className="spinner-border"></div></div>;
  }

  if (players.length === 0) {
    return (
      <div className="alert alert-info">
        No players have been added to this team yet. Add players from the team page first.
      </div>
    );
  }

  // Generate array of innings
  const inningsArray = Array.from({ length: innings }, (_, i) => i + 1);

  // Get player batting order position
  const getPlayerBattingPosition = (playerId) => {
    const index = battingOrder.findIndex(id => id === playerId);
    return index !== -1 ? index + 1 : null;
  };
  
  // Sort players by batting order, then by jersey number
  const sortedPlayers = [...availablePlayers].sort((a, b) => {
    const aOrder = getPlayerBattingPosition(a.id);
    const bOrder = getPlayerBattingPosition(b.id);
    
    // If both have batting positions, sort by batting order
    if (aOrder !== null && bOrder !== null) {
      return aOrder - bOrder;
    }
    
    // If only one has a batting position, put that one first
    if (aOrder !== null) return -1;
    if (bOrder !== null) return 1;
    
    // If neither has a batting position, sort by jersey number
    return a.jersey_number - b.jersey_number;
  });

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Fielding Rotations</h3>
        <div>
          <button 
            className="btn btn-outline-primary me-2"
            onClick={autoAssignAllInnings}
          >
            Auto-Assign All Innings
          </button>
          <button 
            className="btn btn-primary me-2"
            onClick={() => handleSaveRotation(false)}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Rotations"}
          </button>
          <button 
            className="btn btn-outline-warning"
            onClick={() => handleSaveRotation(true)}
            disabled={saving}
            title="Ignore validation errors and save anyway"
          >
            Save Anyway
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Display validation errors */}
      {(validationErrors.innings && Object.keys(validationErrors.innings).length > 0) || 
       (validationErrors.players && Object.keys(validationErrors.players).length > 0) ? (
        <div className="alert alert-warning">
          <h5>Please fix the following issues:</h5>
          
          {/* Inning errors */}
          {validationErrors.innings && Object.keys(validationErrors.innings).length > 0 && (
            <div>
              <h6>Inning Issues:</h6>
              <ul>
                {Object.entries(validationErrors.innings).map(([inning, errors]) => (
                  <li key={inning}>
                    <strong>Inning {inning}:</strong>
                    <ul>
                      {errors.map((err, index) => (
                        <li key={index}>{err}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Player errors */}
          {validationErrors.players && Object.keys(validationErrors.players).length > 0 && (
            <div>
              <h6>Player Issues:</h6>
              <ul>
                {Object.entries(validationErrors.players).map(([playerId, errors]) => {
                  const player = availablePlayers.find(p => p.id.toString() === playerId);
                  return (
                    <li key={playerId}>
                      <strong>#{player?.jersey_number} {player?.name}:</strong>
                      <ul>
                        {errors.map((err, index) => (
                          <li key={index}>{err}</li>
                        ))}
                      </ul>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      ) : null}

      {/* Position Assignment Table */}
      <div className="card mb-4">
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-striped">
              <thead>
                <tr>
                  <th>Batting</th>
                  <th>#</th>
                  <th>Player</th>
                  <th>Summary</th>
                  {inningsArray.map(inning => (
                    <th key={inning}>
                      Inning {inning}
                      <div className="btn-group btn-group-sm ms-2">
                        <button 
                          className="btn btn-outline-secondary btn-sm"
                          onClick={() => autoAssignPositions(inning)}
                          title="Auto-assign positions for this inning"
                        >
                          <i className="bi bi-lightning"></i>
                        </button>
                        {inning > 1 && (
                          <button 
                            className="btn btn-outline-secondary btn-sm"
                            onClick={() => copyFromPreviousInning(inning)}
                            title="Copy from previous inning"
                          >
                            <i className="bi bi-arrow-left"></i>
                          </button>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedPlayers.map(player => {
                  const positionSummary = getPlayerPositionSummary(player.id);
                  return (
                  <tr key={player.id}>
                    <td>
                      {getPlayerBattingPosition(player.id) ? 
                        getPlayerBattingPosition(player.id) : 
                        '-'}
                    </td>
                    <td>{player.jersey_number}</td>
                    <td>{player.name}</td>
                    <td>
                      <small>
                        IF: {positionSummary.infield} &middot; 
                        OF: {positionSummary.outfield} &middot; 
                        Bench: {positionSummary.bench}
                      </small>
                    </td>
                    {inningsArray.map(inning => {
                      // Find the position for this player in this inning
                      let position = null;
                      const inningRotation = rotations[inning] || {};
                      for (const [pos, playerId] of Object.entries(inningRotation)) {
                        if (playerId === player.id) {
                          position = pos;
                          break;
                        }
                      }
                      
                      // Check if this is a problematic position (consecutive infield or outfield)
                      let isProblematic = false;
                      if (position) {
                        // Check previous inning
                        if (inning > 1) {
                          const prevInningRotation = rotations[inning - 1] || {};
                          let prevPosition = null;
                          
                          for (const [pos, pid] of Object.entries(prevInningRotation)) {
                            if (pid === player.id) {
                              prevPosition = pos;
                              break;
                            }
                          }
                          
                          if (prevPosition) {
                            if (INFIELD.includes(position) && INFIELD.includes(prevPosition)) {
                              isProblematic = true;
                            } else if (OUTFIELD.includes(position) && OUTFIELD.includes(prevPosition)) {
                              isProblematic = true;
                            }
                          }
                        }
                        
                        // Check next inning
                        if (inning < innings) {
                          const nextInningRotation = rotations[inning + 1] || {};
                          let nextPosition = null;
                          
                          for (const [pos, pid] of Object.entries(nextInningRotation)) {
                            if (pid === player.id) {
                              nextPosition = pos;
                              break;
                            }
                          }
                          
                          if (nextPosition) {
                            if (INFIELD.includes(position) && INFIELD.includes(nextPosition)) {
                              isProblematic = true;
                            } else if (OUTFIELD.includes(position) && OUTFIELD.includes(nextPosition)) {
                              isProblematic = true;
                            }
                          }
                        }
                      }
                      
                      return (
                        <td key={inning}>
                          <select 
                            className={`form-select form-select-sm ${isProblematic ? 'border-danger' : ''}`}
                            value={position || ""}
                            onChange={(e) => {
                              const newPosition = e.target.value;
                              if (newPosition === "") {
                                // If empty, clear any existing position for this player in this inning
                                if (position) {
                                  handleClearPosition(inning, position);
                                }
                              } else {
                                // Assign the player to the new position
                                handlePositionChange(player, inning, newPosition);
                              }
                            }}
                          >
                            <option value="">Not Playing</option>
                            {FIELD_POSITIONS.map(pos => {
                              // Check if this position already appears for this player in the game
                              const isDuplicatePosition = positionSummary.positions[pos] && 
                                                        (position !== pos || positionSummary.positions[pos] > 1);
                              
                              return (
                                <option 
                                  key={pos} 
                                  value={pos}
                                  className={isDuplicatePosition ? 'text-danger' : ''}
                                >
                                  {pos}{isDuplicatePosition ? ` (${positionSummary.positions[pos]}×)` : ''}
                                </option>
                              );
                            })}
                          </select>
                        </td>
                      );
                    })}
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      {/* Position Summary Table */}
      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0">Position Summaries</h5>
        </div>
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-sm">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Player</th>
                  <th>Infield</th>
                  <th>Outfield</th>
                  <th>Bench</th>
                  <th>Positions Played</th>
                </tr>
              </thead>
              <tbody>
                {sortedPlayers.map(player => {
                  const positionSummary = getPlayerPositionSummary(player.id);
                  const positionsPlayed = Object.entries(positionSummary.positions)
                    .map(([position, count]) => `${position}${count > 1 ? ` (${count}×)` : ''}`)
                    .join(', ');
                    
                  return (
                    <tr key={player.id}>
                      <td>{player.jersey_number}</td>
                      <td>{player.name}</td>
                      <td>{positionSummary.infield}</td>
                      <td>{positionSummary.outfield}</td>
                      <td>{positionSummary.bench}</td>
                      <td><small>{positionsPlayed || 'None'}</small></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldingRotationTab;