import React, { useState, useEffect } from "react";
import { getFieldingRotations, saveFieldingRotation, getPlayerAvailability } from "../../services/api";
import FieldPositionEditor from "./FieldPositionEditor";

// Constants from CLAUDE.md
const POSITIONS = ["Pitcher", "Catcher", "1B", "2B", "3B", "SS", "LF", "RF", "LC", "RC", "Bench"];
const INFIELD = ["Pitcher", "1B", "2B", "3B", "SS"];
const OUTFIELD = ["Catcher", "LF", "RF", "LC", "RC"];
const BENCH = ["Bench"];

const FieldingRotationTab = ({ gameId, players, innings = 6 }) => {
  const [currentInning, setCurrentInning] = useState(1);
  const [rotations, setRotations] = useState({});
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchData();
  }, [gameId, players]);

  const fetchData = async () => {
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
  };

  const handleSaveRotation = async () => {
    try {
      setSaving(true);
      setSuccess("");
      setError("");
      
      await saveFieldingRotation(gameId, currentInning, rotations[currentInning] || {});
      setSuccess("Fielding rotation saved successfully.");
    } catch (err) {
      setError("Failed to save fielding rotation. Please try again.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handlePositionChange = (position, playerId) => {
    // Create a new rotation for the current inning if it doesn't exist
    const currentRotation = rotations[currentInning] || {};
    
    // Update the position with the player ID
    const updatedRotation = {
      ...currentRotation,
      [position]: playerId
    };
    
    // Update the rotations state
    setRotations({
      ...rotations,
      [currentInning]: updatedRotation
    });
  };

  const generateDefaultRotation = () => {
    // Get current rotation
    const currentRotation = rotations[currentInning] || {};
    
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
      [currentInning]: newRotation
    });
  };

  const copyFromPreviousInning = () => {
    if (currentInning > 1) {
      const previousInning = currentInning - 1;
      const previousRotation = rotations[previousInning] || {};
      
      setRotations({
        ...rotations,
        [currentInning]: { ...previousRotation }
      });
    }
  };

  const getPositionClass = (position) => {
    if (INFIELD.includes(position)) return "infield";
    if (OUTFIELD.includes(position)) return "outfield";
    return "bench";
  };

  const getPlayerById = (playerId) => {
    return availablePlayers.find(player => player.id === playerId);
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

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Fielding Rotations</h3>
        <div>
          <button 
            className="btn btn-outline-secondary me-2"
            onClick={copyFromPreviousInning}
            disabled={currentInning === 1 || !rotations[currentInning - 1]}
          >
            Copy from Previous Inning
          </button>
          <button 
            className="btn btn-outline-primary me-2"
            onClick={generateDefaultRotation}
          >
            Auto-Assign Positions
          </button>
          <button 
            className="btn btn-primary"
            onClick={handleSaveRotation}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Rotation"}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="card mb-4">
        <div className="card-header">
          <ul className="nav nav-tabs card-header-tabs">
            {inningsArray.map(inning => (
              <li className="nav-item" key={inning}>
                <button
                  className={`nav-link ${currentInning === inning ? 'active' : ''}`}
                  onClick={() => setCurrentInning(inning)}
                >
                  Inning {inning}
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-8">
              <FieldPositionEditor 
                positions={rotations[currentInning] || {}}
                availablePlayers={availablePlayers}
                onPositionChange={handlePositionChange}
              />
            </div>
            <div className="col-md-4">
              <div className="card">
                <div className="card-header">
                  <h5 className="mb-0">Position Assignments</h5>
                </div>
                <div className="card-body">
                  <div className="mb-3">
                    <h6>Infield</h6>
                    {INFIELD.map(position => (
                      <div className="d-flex justify-content-between mb-1" key={position}>
                        <span>{position}:</span>
                        <span>
                          {rotations[currentInning]?.[position] ? 
                            `#${getPlayerById(rotations[currentInning][position])?.jersey_number} ${getPlayerById(rotations[currentInning][position])?.name}` : 
                            <span className="text-muted">Unassigned</span>
                          }
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mb-3">
                    <h6>Outfield</h6>
                    {OUTFIELD.map(position => (
                      <div className="d-flex justify-content-between mb-1" key={position}>
                        <span>{position}:</span>
                        <span>
                          {rotations[currentInning]?.[position] ? 
                            `#${getPlayerById(rotations[currentInning][position])?.jersey_number} ${getPlayerById(rotations[currentInning][position])?.name}` : 
                            <span className="text-muted">Unassigned</span>
                          }
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldingRotationTab;