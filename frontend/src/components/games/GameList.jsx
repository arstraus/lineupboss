import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
import GameForm from "./GameForm";

const GameList = ({ teamId }) => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingGame, setEditingGame] = useState(null);

  useEffect(() => {
    fetchGames();
  }, [teamId]);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/games/team/${teamId}`);
      setGames(response.data);
      setError("");
    } catch (err) {
      setError("Failed to load games. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGame = async (gameData) => {
    try {
      await api.post(`/games/team/${teamId}`, gameData);
      setShowAddForm(false);
      fetchGames();
    } catch (err) {
      setError("Failed to add game. Please try again.");
      console.error(err);
      throw err;
    }
  };

  const handleUpdateGame = async (gameId, gameData) => {
    try {
      setError("");
      console.log("Updating game with data:", gameData);
      const response = await api.put(`/games/${gameId}`, gameData);
      console.log("Update response:", response);
      
      // Close the modal first
      setEditingGame(null);
      
      // Then refresh the games list
      setTimeout(() => fetchGames(), 100);
    } catch (err) {
      setError("Failed to update game. Please try again.");
      console.error("Update game error:", err);
      // Don't throw error here to avoid unhandled promise rejection
    }
  };

  const handleDeleteGame = async (gameId) => {
    if (window.confirm("Are you sure you want to delete this game? This action cannot be undone.")) {
      try {
        await api.delete(`/games/${gameId}`);
        fetchGames();
      } catch (err) {
        setError("Failed to delete game. Please try again.");
        console.error(err);
      }
    }
  };

  // Helper function to format date
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    
    // Fix for timezone issue: parse date parts directly to avoid timezone offset
    const [year, month, day] = dateString.split('-').map(num => parseInt(num, 10));
    // Month is 0-indexed in JavaScript Date
    const date = new Date(year, month - 1, day);
    
    return date.toLocaleDateString(undefined, options);
  };

  // Helper function to format time
  const formatTime = (timeString) => {
    if (!timeString) return "N/A";
    
    try {
      // Handle ISO format or time-only string
      let time;
      if (timeString.includes("T")) {
        time = new Date(timeString);
      } else {
        // For time-only string in format HH:MM:SS
        const [hours, minutes] = timeString.split(":");
        time = new Date();
        time.setHours(hours, minutes);
      }
      
      return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return timeString;
    }
  };

  if (loading) {
    return <div className="text-center mt-3"><div className="spinner-border"></div></div>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Games</h3>
        <button 
          className="btn btn-success" 
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? "Cancel" : "Add Game"}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {showAddForm && (
        <div className="card mb-3">
          <div className="card-header">
            <h4 className="mb-0">Add New Game</h4>
          </div>
          <div className="card-body">
            <GameForm 
              onSubmit={handleAddGame} 
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        </div>
      )}

      {games.length === 0 ? (
        <div className="alert alert-info">
          No games scheduled yet. Click "Add Game" to get started.
        </div>
      ) : (
        <div className="row">
          {games.map(game => (
            <div className="col-md-4 mb-3" key={game.id}>
              <div className="card h-100">
                <div className="card-header">
                  <h5 className="mb-0">
                    Game #{game.game_number} - {game.opponent}
                  </h5>
                </div>
                <div className="card-body">
                  <p><strong>Date:</strong> {formatDate(game.date)}</p>
                  <p><strong>Time:</strong> {formatTime(game.time)}</p>
                  <p><strong>Innings:</strong> {game.innings}</p>
                </div>
                <div className="card-footer d-flex justify-content-between">
                  <Link to={`/games/${game.id}`} className="btn btn-primary btn-sm">
                    Manage Game
                  </Link>
                  <div>
                    <button 
                      className="btn btn-outline-secondary btn-sm me-2"
                      onClick={() => setEditingGame(game)}
                    >
                      Edit
                    </button>
                    <button 
                      className="btn btn-outline-danger btn-sm"
                      onClick={() => handleDeleteGame(game.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {editingGame && (
        <div className="modal-overlay" onClick={(e) => {
          // Only close if clicking directly on the overlay, not its children
          if (e.target === e.currentTarget) {
            setEditingGame(null);
          }
        }}>
          <div className="modal show d-block" tabIndex="-1" role="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-dialog" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Edit Game: vs {editingGame.opponent}</h5>
                  <button 
                    type="button" 
                    className="btn-close" 
                    onClick={() => setEditingGame(null)}
                    aria-label="Close"
                  ></button>
                </div>
                <div className="modal-body">
                  <GameForm 
                    game={editingGame} 
                    onSubmit={(data) => handleUpdateGame(editingGame.id, data)}
                    onCancel={() => setEditingGame(null)}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameList;