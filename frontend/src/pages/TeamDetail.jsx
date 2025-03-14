import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getTeam, updateTeam } from "../services/api";
import PlayerList from "../components/players/PlayerList";
import GameList from "../components/games/GameList";

const TeamDetail = () => {
  const { teamId } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: "",
    league: "",
    head_coach: "",
    assistant_coach1: "",
    assistant_coach2: ""
  });
  const [activeTab, setActiveTab] = useState("players");

  useEffect(() => {
    fetchTeam();
  }, [teamId]);

  const fetchTeam = async () => {
    try {
      setLoading(true);
      const response = await getTeam(teamId);
      setTeam(response.data);
      setEditFormData({
        name: response.data.name || "",
        league: response.data.league || "",
        head_coach: response.data.head_coach || "",
        assistant_coach1: response.data.assistant_coach1 || "",
        assistant_coach2: response.data.assistant_coach2 || ""
      });
      setError("");
    } catch (err) {
      setError("Failed to load team details. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditFormChange = (e) => {
    const { name, value } = e.target;
    setEditFormData({
      ...editFormData,
      [name]: value
    });
  };

  const handleEditFormSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateTeam(teamId, editFormData);
      setIsEditing(false);
      fetchTeam(); // Refresh team data
    } catch (err) {
      setError("Failed to update team. Please try again.");
      console.error(err);
    }
  };

  if (loading) {
    return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
  }

  if (!team) {
    return <div className="alert alert-danger">Team not found</div>;
  }

  return (
    <div>
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h2 className="mb-0">{team.name}</h2>
          <button 
            className="btn btn-outline-primary" 
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? "Cancel" : "Edit Team"}
          </button>
        </div>
        <div className="card-body">
          {isEditing ? (
            <form onSubmit={handleEditFormSubmit}>
              <div className="mb-3">
                <label htmlFor="name" className="form-label">Team Name *</label>
                <input
                  type="text"
                  className="form-control"
                  id="name"
                  name="name"
                  value={editFormData.name}
                  onChange={handleEditFormChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label htmlFor="league" className="form-label">League</label>
                <input
                  type="text"
                  className="form-control"
                  id="league"
                  name="league"
                  value={editFormData.league}
                  onChange={handleEditFormChange}
                />
              </div>
              <div className="mb-3">
                <label htmlFor="head_coach" className="form-label">Head Coach</label>
                <input
                  type="text"
                  className="form-control"
                  id="head_coach"
                  name="head_coach"
                  value={editFormData.head_coach}
                  onChange={handleEditFormChange}
                />
              </div>
              <div className="mb-3">
                <label htmlFor="assistant_coach1" className="form-label">Assistant Coach 1</label>
                <input
                  type="text"
                  className="form-control"
                  id="assistant_coach1"
                  name="assistant_coach1"
                  value={editFormData.assistant_coach1}
                  onChange={handleEditFormChange}
                />
              </div>
              <div className="mb-3">
                <label htmlFor="assistant_coach2" className="form-label">Assistant Coach 2</label>
                <input
                  type="text"
                  className="form-control"
                  id="assistant_coach2"
                  name="assistant_coach2"
                  value={editFormData.assistant_coach2}
                  onChange={handleEditFormChange}
                />
              </div>
              <button type="submit" className="btn btn-success">Save Changes</button>
            </form>
          ) : (
            <div>
              {team.league && <p><strong>League:</strong> {team.league}</p>}
              {team.head_coach && <p><strong>Head Coach:</strong> {team.head_coach}</p>}
              {team.assistant_coach1 && <p><strong>Assistant Coach 1:</strong> {team.assistant_coach1}</p>}
              {team.assistant_coach2 && <p><strong>Assistant Coach 2:</strong> {team.assistant_coach2}</p>}
            </div>
          )}
        </div>
      </div>

      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === "players" ? "active" : ""}`}
            onClick={() => setActiveTab("players")}
          >
            Players
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === "games" ? "active" : ""}`}
            onClick={() => setActiveTab("games")}
          >
            Games
          </button>
        </li>
      </ul>

      {activeTab === "players" ? (
        <PlayerList teamId={teamId} />
      ) : (
        <GameList teamId={teamId} />
      )}
    </div>
  );
};

export default TeamDetail;