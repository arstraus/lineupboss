import React, { useState, useEffect, useCallback } from "react";
import { getFieldingRotations, saveFieldingRotation, getPlayerAvailability } from "../../services/api";

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

  // Validate rotations before saving
  const validateRotations = () => {
    const errors = {};
    
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
      
      // 2. Check for duplicate player assignments
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
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSaveRotation = async () => {
    try {
      // Validate rotations first
      if (!validateRotations()) {
        setError("Please fix the validation errors before saving.");
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
      
      setSuccess("Fielding rotations saved successfully.");
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

  // Sort players by jersey number for display
  const sortedPlayers = [...availablePlayers].sort((a, b) => 
    a.jersey_number - b.jersey_number
  );

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
            className="btn btn-primary"
            onClick={handleSaveRotation}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Rotations"}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Display validation errors */}
      {Object.keys(validationErrors).length > 0 && (
        <div className="alert alert-warning">
          <h5>Please fix the following issues:</h5>
          <ul>
            {Object.entries(validationErrors).map(([inning, errors]) => (
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

      <div className="card mb-4">
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-striped">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Player</th>
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
                {sortedPlayers.map(player => (
                  <tr key={player.id}>
                    <td>{player.jersey_number}</td>
                    <td>{player.name}</td>
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
                      
                      return (
                        <td key={inning}>
                          <select 
                            className="form-select form-select-sm"
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
                            {FIELD_POSITIONS.map(pos => (
                              <option key={pos} value={pos}>
                                {pos}
                              </option>
                            ))}
                          </select>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldingRotationTab;