import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getTeams, createTeam, deleteTeam } from "../services/api";

const Dashboard = () => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showNewTeamForm, setShowNewTeamForm] = useState(false);
  const [newTeam, setNewTeam] = useState({
    name: "",
    league: "",
    head_coach: ""
  });

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      // Get token directly before making the request
      const token = localStorage.getItem("token");
      console.log("Fetching teams with token:", token ? "Present" : "Not found");
      
      // Force headers to be set with correct token
      const response = await getTeams();
      console.log("Teams API response:", response);
      
      setTeams(response.data);
      setError("");
    } catch (err) {
      console.error("Error fetching teams:", err);
      if (err.response) {
        console.error("Response status:", err.response.status);
        console.error("Response data:", err.response.data);
      }
      setError("Failed to load teams. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleNewTeamChange = (e) => {
    const { name, value } = e.target;
    setNewTeam({
      ...newTeam,
      [name]: value
    });
  };

  const handleNewTeamSubmit = async (e) => {
    e.preventDefault();
    try {
      console.log("Creating team with data:", newTeam);
      // Check token before team creation
      const token = localStorage.getItem("token");
      console.log("Creating team with token:", token ? "Present" : "Not found");
      
      const response = await createTeam(newTeam);
      console.log("Team creation response:", response);
      
      setNewTeam({
        name: "",
        league: "",
        head_coach: ""
      });
      setShowNewTeamForm(false);
      fetchTeams();
    } catch (err) {
      console.error("Error creating team:", err);
      if (err.response) {
        console.error("Response status:", err.response.status);
        console.error("Response data:", err.response.data);
      }
      setError("Failed to create team. Please try again.");
    }
  };

  const handleDeleteTeam = async (teamId) => {
    if (window.confirm("Are you sure you want to delete this team? This action cannot be undone.")) {
      try {
        await deleteTeam(teamId);
        fetchTeams();
      } catch (err) {
        setError("Failed to delete team. Please try again.");
        console.error(err);
      }
    }
  };

  if (loading) {
    return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
  }

  return (
    <div className="dashboard">
      {/* Hero Section */}
      <div className="hero-section mb-4">
        <div className="hero-content">
          <h1 className="text-white">Welcome to Lineup Boss</h1>
          <p className="text-white">The ultimate baseball lineup management application</p>
        </div>
      </div>

      {/* App Features */}
      <div className="container mt-4">
        <div className="app-features mb-4">
          <h2 className="text-center mb-3">Organize Your Team with Ease</h2>
          <div className="row text-center">
            <div className="col-md-4 mb-4">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="bi bi-people-fill"></i>
                </div>
                <h3>Team Management</h3>
                <p>Create and manage multiple teams with detailed rosters</p>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="bi bi-calendar-check"></i>
                </div>
                <h3>Game Scheduling</h3>
                <p>Organize your season schedule and track game details</p>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="bi bi-list-ol"></i>
                </div>
                <h3>Fair Rotations</h3>
                <p>Create balanced batting orders and field rotations</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Teams Section */}
      <div className="teams-section mb-5">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h2 className="section-title">
            <i className="bi bi-trophy"></i> My Teams
          </h2>
          <button 
            className="btn btn-primary" 
            onClick={() => setShowNewTeamForm(!showNewTeamForm)}
          >
            <i className="bi bi-plus-circle me-2"></i>
            {showNewTeamForm ? "Cancel" : "Add New Team"}
          </button>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {showNewTeamForm && (
          <div className="card mb-4 new-team-card">
            <div className="card-header bg-primary text-white">
              <h3 className="mb-0">Create New Team</h3>
            </div>
            <div className="card-body">
              <form onSubmit={handleNewTeamSubmit}>
                <div className="mb-3">
                  <label htmlFor="name" className="form-label">Team Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    id="name"
                    name="name"
                    value={newTeam.name}
                    onChange={handleNewTeamChange}
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
                    value={newTeam.league}
                    onChange={handleNewTeamChange}
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="head_coach" className="form-label">Head Coach</label>
                  <input
                    type="text"
                    className="form-control"
                    id="head_coach"
                    name="head_coach"
                    value={newTeam.head_coach}
                    onChange={handleNewTeamChange}
                  />
                </div>
                <button type="submit" className="btn btn-success">
                  <i className="bi bi-check-circle me-2"></i>Create Team
                </button>
              </form>
            </div>
          </div>
        )}

        {teams.length === 0 ? (
          <div className="alert alert-info">
            <i className="bi bi-info-circle-fill me-2"></i>
            You have not created any teams yet. Click "Add New Team" to get started.
          </div>
        ) : (
          <div className="team-cards">
            {teams.map((team) => (
              <div className="team-card" key={team.id}>
                <div className="team-card-header">
                  <h3>{team.name}</h3>
                </div>
                <div className="team-card-body">
                  {team.league && <p><i className="bi bi-trophy-fill me-2"></i><strong>League:</strong> {team.league}</p>}
                  {team.head_coach && <p><i className="bi bi-whistle-fill me-2"></i><strong>Head Coach:</strong> {team.head_coach}</p>}
                </div>
                <div className="team-card-footer">
                  <Link to={`/teams/${team.id}`} className="btn btn-primary">
                    <i className="bi bi-clipboard-data me-2"></i>Manage Team
                  </Link>
                  <button 
                    className="btn btn-outline-danger"
                    onClick={() => handleDeleteTeam(team.id)}
                  >
                    <i className="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* App Info Section */}
      <div className="app-info mb-5">
        <div className="row align-items-center">
          <div className="col-md-6">
            <h3>Make Game Day a Home Run!</h3>
            <p>LineupBoss helps coaches create balanced batting orders and field rotations that give every player fair playing time while optimizing your team's performance.</p>
            <ul className="app-features-list">
              <li><i className="bi bi-check2-circle"></i> Manage multiple teams in one place</li>
              <li><i className="bi bi-check2-circle"></i> Create fair batting orders across all games</li>
              <li><i className="bi bi-check2-circle"></i> Track which players are available for each game</li>
              <li><i className="bi bi-check2-circle"></i> Generate printable game-day lineup sheets</li>
            </ul>
          </div>
          <div className="col-md-6">
            <div className="app-screenshot">
              {/* Placeholder for app screenshot - you can replace this with an actual image */}
              <div className="screenshot-placeholder">
                <i className="bi bi-phone"></i>
                <p>LineupBoss works great on mobile and desktop!</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
