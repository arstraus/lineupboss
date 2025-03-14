import React, { useState } from "react";

// Constants from constants.js
import { POSITIONS } from "../../constants";

const FieldPositionEditor = ({ positions, availablePlayers, onPositionChange }) => {
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [showPositionSelector, setShowPositionSelector] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const getPlayerById = (playerId) => {
    return availablePlayers.find(player => player.id === playerId);
  };

  const getAvailablePlayers = () => {
    // Get all currently assigned players
    const assignedPlayerIds = Object.values(positions);
    
    // If a position is selected and has a player assigned, include that player
    // in the available list so they can be unassigned
    const selectedPlayerId = selectedPosition ? positions[selectedPosition] : null;
    
    // Filter available players
    let filteredPlayers = availablePlayers.filter(player => {
      // Include the player if they're not assigned or if they're assigned to the selected position
      const isAvailable = !assignedPlayerIds.includes(player.id) || player.id === selectedPlayerId;
      
      // Filter by search term if provided
      const matchesSearch = searchTerm ? 
        player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        player.jersey_number.toString().includes(searchTerm) : 
        true;
      
      return isAvailable && matchesSearch;
    });
    
    // Sort by jersey number
    return filteredPlayers.sort((a, b) => a.jersey_number - b.jersey_number);
  };

  const handlePositionClick = (position) => {
    setSelectedPosition(position);
    setShowPositionSelector(true);
    setSearchTerm("");
  };

  const handlePlayerSelect = (playerId) => {
    if (selectedPosition) {
      onPositionChange(selectedPosition, playerId);
      setShowPositionSelector(false);
      setSelectedPosition(null);
    }
  };

  const handleClearPosition = () => {
    if (selectedPosition) {
      onPositionChange(selectedPosition, null);
      setShowPositionSelector(false);
      setSelectedPosition(null);
    }
  };

  // Calculate position coordinates for the baseball field
  const getPositionStyle = (position) => {
    // Base styles for all positions
    const baseStyle = {
      position: "absolute",
      width: "50px",
      height: "50px",
      borderRadius: "50%",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      cursor: "pointer",
      backgroundColor: positions[position] ? "#007bff" : "#f8f9fa",
      color: positions[position] ? "#fff" : "#212529",
      border: `2px solid ${positions[position] ? "#0056b3" : "#dee2e6"}`,
      zIndex: 2,
      transition: "all 0.2s"
    };
    
    // Position-specific coordinates
    const positionCoords = {
      "Pitcher": { top: "38%", left: "50%" },
      "Catcher": { top: "85%", left: "50%" },
      "1B": { top: "40%", left: "65%" },
      "2B": { top: "30%", left: "60%" },
      "SS": { top: "30%", left: "40%" },
      "3B": { top: "40%", left: "35%" },
      "LF": { top: "15%", left: "30%" },
      "LC": { top: "15%", left: "50%" },
      "RC": { top: "15%", left: "70%" },
      "RF": { top: "25%", left: "80%" }
    };
    
    return { ...baseStyle, ...positionCoords[position] };
  };

  return (
    <div className="position-relative" style={{ width: "100%", height: "400px" }}>
      {/* Baseball field background */}
      <div 
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          borderRadius: "50% 50% 0 0",
          backgroundColor: "#92d36e", // Grass green
          overflow: "hidden",
          zIndex: 1
        }}
      >
        {/* Infield dirt */}
        <div 
          style={{
            position: "absolute",
            width: "70%",
            height: "70%",
            bottom: "0",
            left: "15%",
            backgroundColor: "#c19a6b", // Dirt color
            borderRadius: "50% 50% 0 0",
            zIndex: 1
          }}
        />
        
        {/* Base paths */}
        <div 
          style={{
            position: "absolute",
            width: "35%",
            height: "35%",
            bottom: "0",
            left: "32.5%",
            backgroundColor: "#92d36e", // Grass green
            transform: "rotate(45deg)",
            transformOrigin: "center bottom",
            zIndex: 1
          }}
        />
        
        {/* Home Plate */}
        <div 
          style={{
            position: "absolute",
            width: "20px",
            height: "20px",
            bottom: "10%",
            left: "calc(50% - 10px)",
            backgroundColor: "white",
            transform: "rotate(45deg)",
            zIndex: 1
          }}
        />
        
        {/* Pitcher's Mound */}
        <div 
          style={{
            position: "absolute",
            width: "30px",
            height: "30px",
            top: "40%",
            left: "calc(50% - 15px)",
            backgroundColor: "#c19a6b", // Dirt color
            borderRadius: "50%",
            zIndex: 1
          }}
        />
      </div>
      
      {/* Position markers */}
      {POSITIONS.filter(pos => pos !== "Bench").map(position => (
        <div 
          key={position}
          style={getPositionStyle(position)}
          className={`position-marker ${selectedPosition === position ? 'selected' : ''}`}
          onClick={() => handlePositionClick(position)}
        >
          {positions[position] ? (
            <span title={getPlayerById(positions[position])?.name}>
              {getPlayerById(positions[position])?.jersey_number}
            </span>
          ) : (
            <span>{position}</span>
          )}
        </div>
      ))}
      
      {/* Player selector */}
      {showPositionSelector && (
        <div 
          className="position-absolute end-0 top-0 bg-white shadow-sm p-3 rounded"
          style={{ width: "300px", zIndex: 5, maxHeight: "300px", overflow: "auto" }}
        >
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h6 className="mb-0">Assign player to {selectedPosition}</h6>
            <button 
              type="button" 
              className="btn-close" 
              onClick={() => setShowPositionSelector(false)}
            ></button>
          </div>
          
          <div className="mb-2">
            <input
              type="text"
              className="form-control"
              placeholder="Search by name or jersey #"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="list-group">
            {positions[selectedPosition] && (
              <button
                className="list-group-item list-group-item-action d-flex justify-content-between align-items-center text-danger"
                onClick={handleClearPosition}
              >
                Clear position
              </button>
            )}
            
            {getAvailablePlayers().map(player => (
              <button
                key={player.id}
                className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${positions[selectedPosition] === player.id ? 'active' : ''}`}
                onClick={() => handlePlayerSelect(player.id)}
              >
                <span>{player.name}</span>
                <span className="badge bg-secondary">{player.jersey_number}</span>
              </button>
            ))}
            
            {getAvailablePlayers().length === 0 && (
              <div className="list-group-item text-center text-muted">
                No available players
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldPositionEditor;