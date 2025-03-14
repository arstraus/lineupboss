import React, { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { getGame, getPlayers } from "../services/api";
import BattingOrderTab from "../components/games/BattingOrderTab";
import FieldingRotationTab from "../components/games/FieldingRotationTab";
import PlayerAvailabilityTab from "../components/games/PlayerAvailabilityTab";

const GameDetail = () => {
  const { gameId } = useParams();
  const [game, setGame] = useState(null);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("availability");

  const fetchGameData = useCallback(async () => {
    try {
      setLoading(true);
      // Get game details
      const gameResponse = await getGame(gameId);
      setGame(gameResponse.data);
      
      // Get team players
      const teamId = gameResponse.data.team_id;
      const playersResponse = await getPlayers(teamId);
      setPlayers(playersResponse.data);
      
      setError("");
    } catch (err) {
      setError("Failed to load game details. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [gameId]);
  
  useEffect(() => {
    fetchGameData();
  }, [fetchGameData]);

  // Helper function to format date
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
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
    return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (!game) {
    return <div className="alert alert-warning">Game not found</div>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Game #{game.game_number}: vs {game.opponent}</h1>
        <Link to={`/teams/${game.team_id}`} className="btn btn-outline-primary">
          Back to Team
        </Link>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <p><strong>Date:</strong> {formatDate(game.date)}</p>
              <p><strong>Time:</strong> {formatTime(game.time)}</p>
            </div>
            <div className="col-md-6">
              <p><strong>Innings:</strong> {game.innings}</p>
              <p><strong>Opponent:</strong> {game.opponent}</p>
            </div>
          </div>
        </div>
      </div>

      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "availability" ? "active" : ""}`}
            onClick={() => setActiveTab("availability")}
          >
            Player Availability
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "batting" ? "active" : ""}`}
            onClick={() => setActiveTab("batting")}
          >
            Batting Order
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "fielding" ? "active" : ""}`}
            onClick={() => setActiveTab("fielding")}
          >
            Fielding Rotations
          </button>
        </li>
      </ul>

      {activeTab === "availability" && (
        <PlayerAvailabilityTab gameId={gameId} players={players} refreshPlayers={fetchGameData} />
      )}

      {activeTab === "batting" && (
        <BattingOrderTab gameId={gameId} players={players} />
      )}

      {activeTab === "fielding" && (
        <FieldingRotationTab gameId={gameId} players={players} innings={game.innings} />
      )}
    </div>
  );
};

export default GameDetail;