import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { get, post, put, del as deleteMethod } from "../../services/api";
import GameForm from "./GameForm";
import CSVUploadForm from "./CSVUploadForm";
import "./GameList.css";

const GameList = ({ teamId }) => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [showCSVUpload, setShowCSVUpload] = useState(false);
  const [editingGame, setEditingGame] = useState(null);

  useEffect(() => {
    fetchGames();
  }, [teamId]);

  const fetchGames = async () => {
    try {
      setLoading(true);
      const response = await get(`/teams/${teamId}/games`);
      
      // Sort games by game_number
      const sortedGames = [...response.data].sort((a, b) => {
        return parseInt(a.game_number) - parseInt(b.game_number);
      });
      
      setGames(sortedGames);
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
      // Use the RESTful endpoint format
      await post(`/teams/${teamId}/games`, gameData);
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
      const response = await put(`/games/${gameId}`, gameData);
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
        console.log(`Attempting to delete game with ID: ${gameId}`);
        const response = await deleteMethod(`/games/${gameId}`);
        console.log('Delete game response:', response);
        
        // Show success message
        setError("");
        // Use a brief timeout to ensure state updates don't conflict
        setTimeout(() => {
          fetchGames();
        }, 300);
      } catch (err) {
        console.error("Delete game error:", err);
        if (err.response) {
          setError(`Failed to delete game: ${err.response.data?.error || err.message}`);
        } else {
          setError("Failed to delete game. Please try again.");
        }
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

  const handleCSVUploadComplete = () => {
    setShowCSVUpload(false);
    fetchGames();
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Games</h3>
        <div className="btn-group">
          <button 
            className="btn btn-success" 
            onClick={() => {
              setShowAddForm(!showAddForm);
              setShowCSVUpload(false);
            }}
          >
            {showAddForm ? "Cancel" : "Add Game"}
          </button>
          <button
            className="btn btn-outline-primary"
            onClick={() => {
              setShowCSVUpload(!showCSVUpload);
              setShowAddForm(false);
            }}
          >
            {showCSVUpload ? "Cancel" : "Upload CSV"}
          </button>
        </div>
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
      
      {showCSVUpload && (
        <CSVUploadForm
          teamId={teamId}
          onUploadComplete={handleCSVUploadComplete}
          onCancel={() => setShowCSVUpload(false)}
          hasExistingGames={games.length > 0}
        />
      )}

      {games.length === 0 ? (
        <div className="alert alert-info">
          No games scheduled yet. Click "Add Game" to get started.
        </div>
      ) : (
        <>
        <div className="d-flex justify-content-between align-items-center mb-2">
          <div><small className="text-muted">{games.length} game{games.length !== 1 ? 's' : ''} total</small></div>
        </div>
        <div className="table-responsive">
          <table className="table table-striped game-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Opponent</th>
                <th>Date</th>
                <th>Time</th>
                <th>Innings</th>
                <th className="text-center game-actions-column">Actions</th>
              </tr>
            </thead>
            <tbody>
              {games.map(game => (
                <tr key={game.id}>
                  <td>{game.game_number}</td>
                  <td>{game.opponent}</td>
                  <td>{formatDate(game.date)}</td>
                  <td>{formatTime(game.time)}</td>
                  <td>{game.innings}</td>
                  <td className="text-center">
                    <div className="btn-group">
                      <Link to={`/games/${game.id}`} className="btn btn-primary btn-sm">
                        Manage
                      </Link>
                      <button 
                        className="btn btn-outline-secondary btn-sm"
                        onClick={() => setEditingGame(game)}
                        title="Edit Game"
                      >
                        Edit
                      </button>
                      <button 
                        className="btn btn-outline-danger btn-sm"
                        onClick={() => handleDeleteGame(game.id)}
                        title="Delete Game"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </>
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