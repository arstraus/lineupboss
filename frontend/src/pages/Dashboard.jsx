import React, { useState, useEffect, useContext } from "react";
import { Link } from "react-router-dom";
import { getTeams, createTeam, deleteTeam, checkApiHealth } from "../services/api";
import { AuthContext } from "../services/AuthContext";

const Dashboard = () => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showNewTeamModal, setShowNewTeamModal] = useState(false);
  const [newTeam, setNewTeam] = useState({
    name: "",
    league: "",
    head_coach: "",
    assistant_coach1: "",
    assistant_coach2: ""
  });

  const [apiStatus, setApiStatus] = useState(null);
  
  // Access auth context for token refresh
  const { refreshToken, currentUser } = useContext(AuthContext);

  useEffect(() => {
    // First check API health, then fetch teams if API is available
    checkApiConnection().then(() => {
      fetchTeams();
    });
  }, []);

  // Function to check if the API is accessible
  const checkApiConnection = async () => {
    try {
      const healthResult = await checkApiHealth();
      setApiStatus(healthResult);
      
      if (healthResult.status === 'error') {
        console.warn(`API health check failed: ${healthResult.message}`);
        // Don't set an error yet - we'll still try to fetch teams
        // This allows the app to work even if the health check endpoint isn't working
        return true; // Continue anyway
      }
      return true;
    } catch (error) {
      console.error("Error checking API health:", error);
      setApiStatus({ status: 'error', message: 'Failed to check API connection' });
      // Don't block the app from trying to fetch teams
      return true;
    }
  };

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
      
      let errorMessage = "Failed to load teams. ";
      
      if (err.response) {
        console.error("Response status:", err.response.status);
        console.error("Response data:", err.response.data);
        
        // Add more specific error information based on status code
        if (err.response.status === 401) {
          errorMessage += "Authentication error. Please try logging out and logging in again.";
        } else if (err.response.status === 404) {
          errorMessage += "API endpoint not found. This might be a configuration issue.";
        } else if (err.response.status >= 500) {
          errorMessage += "Server error. Please try again later.";
        } else {
          errorMessage += `Error code: ${err.response.status}`;
        }
        
        // Add specific error message from API if available
        if (err.response.data && err.response.data.error) {
          errorMessage += ` (${err.response.data.error})`;
        }
      } else if (err.request) {
        // Request was made but no response received (network error)
        console.error("No response received from server");
        errorMessage += "Could not connect to the server. Please check your internet connection.";
      } else {
        // Something else happened while setting up the request
        errorMessage += err.message || "Unknown error occurred";
      }
      
      setError(errorMessage);
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
      
      if (!token) {
        setError("Not logged in. Please log in again.");
        return;
      }
      
      // Make sure we have required fields
      if (!newTeam.name) {
        setError("Team name is required");
        return;
      }
      
      // Add debug logging for API URL
      console.log("Creating team at URL:", "/teams/");
      
      const response = await createTeam(newTeam);
      console.log("Team creation response:", response);
      
      // Clear form and reset state on success
      setNewTeam({
        name: "",
        league: "",
        head_coach: "",
        assistant_coach1: "",
        assistant_coach2: ""
      });
      setError("");
      setShowNewTeamModal(false);
      
      // Fetch updated teams list
      fetchTeams();
    } catch (err) {
      console.error("Error creating team:", err);
      
      // Get request details for debugging
      const requestConfig = err.config;
      console.error("Request details:", {
        url: requestConfig?.url,
        method: requestConfig?.method,
        headers: requestConfig?.headers,
        baseURL: requestConfig?.baseURL,
        data: requestConfig?.data
      });
      
      if (err.response) {
        console.error("Response status:", err.response.status);
        console.error("Response data:", err.response.data);
        
        // More detailed error message based on status code
        if (err.response.status === 401) {
          setError("Authentication error. Please try logging out and logging in again.");
          // Try to refresh token and user session
          try {
            const refreshed = await refreshToken();
            if (refreshed) {
              // If token refresh worked, try again
              const response = await createTeam(newTeam);
              
              // Handle success case
              setNewTeam({
                name: "",
                league: "",
                head_coach: "",
                assistant_coach1: "",
                assistant_coach2: ""
              });
              setError("");
              setShowNewTeamModal(false);
              fetchTeams();
              return;
            }
          } catch (refreshErr) {
            console.error("Token refresh failed:", refreshErr);
          }
        } else if (err.response.status === 403) {
          // Team limit reached - subscription tier limit
          if (err.response.data && err.response.data.error === 'Team limit reached') {
            setError(
              <div>
                <strong>Team limit reached:</strong> {err.response.data.message}
                <div className="mt-2">
                  <a href="/account/billing" className="btn btn-sm btn-primary">
                    <i className="bi bi-arrow-up-circle me-1"></i>
                    Upgrade Now
                  </a>
                </div>
              </div>
            );
          } else {
            setError(`Permission error: ${err.response.data.error || 'You don\'t have permission to perform this action'}`);
          }
        } else if (err.response.status === 400) {
          setError(`Bad request: ${err.response.data.error || 'Please check your input'}`);
        } else {
          setError(`Failed to create team: ${err.response.data.error || 'Unknown error'} (Status: ${err.response.status})`);
        }
      } else if (err.request) {
        setError("No response received from server. Please check your connection.");
      } else {
        setError(`Failed to create team: ${err.message || 'Unknown error'}`);
      }
    }
  };

  const handleDeleteTeam = async (teamId) => {
    if (window.confirm("Are you sure you want to delete this team? This action cannot be undone.")) {
      try {
        console.log(`Attempting to delete team with ID: ${teamId}`);
        const response = await deleteTeam(teamId);
        console.log('Delete team response:', response);
        
        // Show success message  
        setError("");
        // Use a brief timeout to ensure state updates don't conflict
        setTimeout(() => {
          fetchTeams();
        }, 300);
      } catch (err) {
        console.error("Delete team error:", err);
        if (err.response) {
          setError(`Failed to delete team: ${err.response.data?.error || err.message}`);
        } else {
          setError("Failed to delete team. Please try again.");
        }
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

      {/* Hidden API status debug info - only visible in development */}
      {process.env.NODE_ENV === 'development' && apiStatus && apiStatus.status === 'error' && (
        <div className="container mt-3">
          <div className="alert alert-warning">
            <h4 className="alert-heading">API Connection Issue (Debug Info)</h4>
            <p>Connection warning for developers only - this may not affect application functionality.</p>
            <hr />
            <p className="mb-0">
              <strong>Status:</strong> {apiStatus.message}<br />
              <strong>API URL:</strong> {process.env.REACT_APP_API_URL}<br />
              <strong>Browser URL:</strong> {window.location.origin}
            </p>
            <button className="btn btn-sm btn-info mt-2" onClick={checkApiConnection}>
              Retry API Connection
            </button>
          </div>
        </div>
      )}

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
      <div className="container">
        <div className="teams-section mb-5">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2 className="section-title">
              <i className="bi bi-trophy"></i> My Teams
            </h2>
            <button 
              className="btn btn-primary" 
              onClick={() => setShowNewTeamModal(true)}
              disabled={apiStatus && apiStatus.status === 'error'}
            >
              <i className="bi bi-plus-circle me-2"></i>
              Add New Team
            </button>
          </div>

          {error && !apiStatus && <div className="alert alert-danger">{error}</div>}

          {/* Team Creation Modal */}
          {showNewTeamModal && (
            <div className="modal-wrapper" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1050 }}>
              <div className="modal show d-block" style={{ position: 'relative', zIndex: 1055 }} tabIndex="-1" role="dialog">
                <div className="modal-dialog modal-lg" role="document" onClick={e => e.stopPropagation()}>
                  <div className="modal-content">
                    <div className="modal-header bg-primary text-white">
                      <h5 className="modal-title">Create New Team</h5>
                      <button 
                        type="button" 
                        className="btn-close btn-close-white" 
                        onClick={() => setShowNewTeamModal(false)}
                        aria-label="Close"
                      ></button>
                    </div>
                    <div className="modal-body">
                      {error && <div className="alert alert-danger">{error}</div>}
                      <form onSubmit={handleNewTeamSubmit} onClick={e => e.stopPropagation()}>
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
                            autoFocus
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
                        <div className="row">
                          <div className="col-md-6">
                            <div className="mb-3">
                              <label htmlFor="assistant_coach1" className="form-label">Assistant Coach 1</label>
                              <input
                                type="text"
                                className="form-control"
                                id="assistant_coach1"
                                name="assistant_coach1"
                                value={newTeam.assistant_coach1}
                                onChange={handleNewTeamChange}
                              />
                            </div>
                          </div>
                          <div className="col-md-6">
                            <div className="mb-3">
                              <label htmlFor="assistant_coach2" className="form-label">Assistant Coach 2</label>
                              <input
                                type="text"
                                className="form-control"
                                id="assistant_coach2"
                                name="assistant_coach2"
                                value={newTeam.assistant_coach2}
                                onChange={handleNewTeamChange}
                              />
                            </div>
                          </div>
                        </div>
                        <div className="modal-footer">
                          <button 
                            type="button" 
                            className="btn btn-secondary" 
                            onClick={() => setShowNewTeamModal(false)}
                          >
                            Cancel
                          </button>
                          <button type="submit" className="btn btn-success">
                            <i className="bi bi-check-circle me-2"></i>Create Team
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                </div>
              </div>
              {/* Modal backdrop with higher z-index */}
              <div 
                className="modal-backdrop show" 
                style={{ zIndex: 1050 }} 
                onClick={() => setShowNewTeamModal(false)}
              ></div>
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
      </div>
      
      {/* App Info Section */}
      <div className="container">
        <div className="app-info mb-5">
          <div className="row align-items-center">
            <div className="col-12">
              <h3 className="text-center">Make Game Day a Home Run!</h3>
              <p className="text-center">LineupBoss helps coaches create balanced batting orders and field rotations that give every player fair playing time while optimizing your team's performance.</p>
              <div className="row mt-4">
                <div className="col-md-6 mx-auto">
                  <ul className="app-features-list">
                    <li><i className="bi bi-check2-circle"></i> Manage multiple teams in one place</li>
                    <li><i className="bi bi-check2-circle"></i> Create fair batting orders across all games</li>
                    <li><i className="bi bi-check2-circle"></i> Track which players are available for each game</li>
                    <li><i className="bi bi-check2-circle"></i> Generate printable game-day lineup sheets</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
