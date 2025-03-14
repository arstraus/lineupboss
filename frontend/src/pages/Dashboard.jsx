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
      const response = await getTeams();
      setTeams(response.data);
      setError("");
    } catch (err) {
      setError("Failed to load teams. Please try again.");
      console.error(err);
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
      await createTeam(newTeam);
      setNewTeam({
        name: "",
        league: "",
        head_coach: ""
      });
      setShowNewTeamForm(false);
      fetchTeams();
    } catch (err) {
      setError("Failed to create team. Please try again.");
      console.error(err);
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
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>My Teams</h1>
        <button 
          className="btn btn-primary" 
          onClick={() => setShowNewTeamForm(!showNewTeamForm)}
        >
          {showNewTeamForm ? "Cancel" : "Add New Team"}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {showNewTeamForm && (
        <div className="card mb-4">
          <div className="card-header">
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
              <button type="submit" className="btn btn-success">Create Team</button>
            </form>
          </div>
        </div>
      )}

      {teams.length === 0 ? (
        <div className="alert alert-info">
          You have not created any teams yet. Click "Add New Team" to get started.
        </div>
      ) : (
        <div className="row">
          {teams.map((team) => (
            <div className="col-md-4 mb-4" key={team.id}>
              <div className="card h-100">
                <div className="card-header">
                  <h3 className="mb-0">{team.name}</h3>
                </div>
                <div className="card-body">
                  {team.league && <p><strong>League:</strong> {team.league}</p>}
                  {team.head_coach && <p><strong>Head Coach:</strong> {team.head_coach}</p>}
                </div>
                <div className="card-footer d-flex justify-content-between">
                  <Link to={`/teams/${team.id}`} className="btn btn-primary">Manage Team</Link>
                  <button 
                    className="btn btn-danger"
                    onClick={() => handleDeleteTeam(team.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
