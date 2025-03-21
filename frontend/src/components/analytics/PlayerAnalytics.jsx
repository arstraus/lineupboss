import React, { useState, useEffect } from "react";
import { getBattingAnalytics, getFieldingAnalytics } from "../../services/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Colors for the position pie chart
const COLORS = [
  "#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", 
  "#82CA9D", "#A4DE6C", "#D0ED57", "#FAACC5", "#F0A77B", "#CF9FFF"
];

const PlayerAnalytics = ({ teamId }) => {
  const [battingAnalytics, setBattingAnalytics] = useState([]);
  const [fieldingAnalytics, setFieldingAnalytics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("batting");
  const [selectedPlayer, setSelectedPlayer] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");
        
        // Fetch batting analytics
        const battingResponse = await getBattingAnalytics(teamId);
        setBattingAnalytics(battingResponse.data);
        
        // Fetch fielding analytics
        const fieldingResponse = await getFieldingAnalytics(teamId);
        setFieldingAnalytics(fieldingResponse.data);
        
        // Set the first player as selected by default if available
        if (battingResponse.data.length > 0) {
          setSelectedPlayer(battingResponse.data[0]);
        }
        
      } catch (err) {
        setError("Failed to load analytics data. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [teamId]);
  
  // Function to handle player selection
  const handlePlayerSelect = (playerId) => {
    if (activeTab === "batting") {
      const player = battingAnalytics.find(p => p.player_id === playerId);
      setSelectedPlayer(player);
    } else {
      const player = fieldingAnalytics.find(p => p.player_id === playerId);
      setSelectedPlayer(player);
    }
  };
  
  // Function to transform batting position data for charts
  const prepareBattingPositionData = (player) => {
    if (!player || !player.batting_positions) return [];
    
    return Object.entries(player.batting_positions).map(([position, count]) => ({
      position: `#${position}`,
      count
    })).sort((a, b) => parseInt(a.position.substring(1)) - parseInt(b.position.substring(1)));
  };
  
  // Function to transform fielding position data for charts
  const prepareFieldingPositionData = (player) => {
    if (!player || !player.position_count) return [];
    
    return Object.entries(player.position_count)
      .filter(([position, _]) => position !== "Bench")  // Exclude Bench from this chart
      .map(([position, count]) => ({
        position,
        count
      }))
      .sort((a, b) => b.count - a.count);  // Sort by count descending
  };
  
  // Function to prepare the category data (infield/outfield/bench)
  const prepareFieldingCategoryData = (player) => {
    if (!player) return [];
    
    return [
      { name: "Infield", value: player.infield_innings },
      { name: "Outfield", value: player.outfield_innings },
      { name: "Bench", value: player.bench_innings }
    ];
  };
  
  // Render loading state
  if (loading) {
    return <div className="text-center my-5"><div className="spinner-border"></div></div>;
  }
  
  // Render error state
  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }
  
  // Render no data state
  if (battingAnalytics.length === 0 && fieldingAnalytics.length === 0) {
    return (
      <div className="alert alert-info">
        No analytics data available. Please add some games and player assignments first.
      </div>
    );
  }
  
  return (
    <div>
      <h2 className="mb-4">Player Analytics</h2>
      
      {/* Tab Navigation */}
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === "batting" ? "active" : ""}`}
            onClick={() => setActiveTab("batting")}
          >
            Batting Analytics
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === "fielding" ? "active" : ""}`}
            onClick={() => setActiveTab("fielding")}
          >
            Fielding Analytics
          </button>
        </li>
      </ul>
      
      <div className="row">
        {/* Player Selection Column */}
        <div className="col-md-3">
          <div className="card">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">Players</h5>
            </div>
            <div className="card-body p-0">
              <div className="list-group list-group-flush">
                {(activeTab === "batting" ? battingAnalytics : fieldingAnalytics).map(player => (
                  <button
                    key={player.player_id}
                    className={`list-group-item list-group-item-action ${selectedPlayer && selectedPlayer.player_id === player.player_id ? "active" : ""}`}
                    onClick={() => handlePlayerSelect(player.player_id)}
                  >
                    #{player.jersey_number} {player.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Analytics Display Column */}
        <div className="col-md-9">
          {selectedPlayer ? (
            <div>
              {activeTab === "batting" ? (
                /* Batting Analytics */
                <div>
                  <div className="card mb-4">
                    <div className="card-header bg-primary text-white">
                      <h5 className="mb-0">Batting Summary for #{selectedPlayer.jersey_number} {selectedPlayer.name}</h5>
                    </div>
                    <div className="card-body">
                      <div className="row">
                        <div className="col-md-6">
                          <h6>Batting Position Summary</h6>
                          <ul className="list-group">
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Total Games
                              <span className="badge bg-primary rounded-pill">{selectedPlayer.total_games}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Games in Lineup
                              <span className="badge bg-success rounded-pill">{selectedPlayer.games_in_lineup}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Average Batting Position
                              <span className="badge bg-info rounded-pill">
                                {selectedPlayer.avg_batting_position ? selectedPlayer.avg_batting_position.toFixed(1) : "N/A"}
                              </span>
                            </li>
                          </ul>
                        </div>
                        <div className="col-md-6">
                          <h6>Batting Position Distribution</h6>
                          <ResponsiveContainer width="100%" height={200}>
                            <BarChart data={prepareBattingPositionData(selectedPlayer)}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="position" />
                              <YAxis allowDecimals={false} />
                              <Tooltip />
                              <Bar dataKey="count" fill="#8884d8" name="Games" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Batting History */}
                  <div className="card">
                    <div className="card-header bg-primary text-white">
                      <h5 className="mb-0">Batting Position History</h5>
                    </div>
                    <div className="card-body">
                      <div className="table-responsive">
                        <table className="table table-striped">
                          <thead>
                            <tr>
                              <th>Date</th>
                              <th>Opponent</th>
                              <th>Batting Position</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedPlayer.batting_position_history.map((game, index) => (
                              <tr key={index}>
                                <td>{game.game_date || "No date"}</td>
                                <td>{game.opponent || "Unknown"}</td>
                                <td>
                                  <span className="badge bg-primary">{game.position}</span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                /* Fielding Analytics */
                <div>
                  <div className="card mb-4">
                    <div className="card-header bg-success text-white">
                      <h5 className="mb-0">Fielding Summary for #{selectedPlayer.jersey_number} {selectedPlayer.name}</h5>
                    </div>
                    <div className="card-body">
                      <div className="row">
                        <div className="col-md-4">
                          <h6>Fielding Summary</h6>
                          <ul className="list-group">
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Total Games
                              <span className="badge bg-primary rounded-pill">{selectedPlayer.total_games}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Games Available
                              <span className="badge bg-success rounded-pill">{selectedPlayer.games_available}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Games Unavailable
                              <span className="badge bg-danger rounded-pill">{selectedPlayer.games_unavailable}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Total Innings
                              <span className="badge bg-info rounded-pill">{selectedPlayer.total_innings}</span>
                            </li>
                          </ul>
                        </div>
                        <div className="col-md-4">
                          <h6>Position Distribution</h6>
                          <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                              <Pie
                                data={prepareFieldingCategoryData(selectedPlayer)}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                                nameKey="name"
                                label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              >
                                {prepareFieldingCategoryData(selectedPlayer).map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip />
                              <Legend />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="col-md-4">
                          <h6>Inning Distribution</h6>
                          <ul className="list-group">
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Infield Innings
                              <span className="badge bg-primary rounded-pill">{selectedPlayer.infield_innings}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Outfield Innings
                              <span className="badge bg-success rounded-pill">{selectedPlayer.outfield_innings}</span>
                            </li>
                            <li className="list-group-item d-flex justify-content-between align-items-center">
                              Bench Innings
                              <span className="badge bg-warning rounded-pill">{selectedPlayer.bench_innings}</span>
                            </li>
                          </ul>
                        </div>
                      </div>
                      
                      {/* Specific positions chart */}
                      <div className="mt-4">
                        <h6>Positions Played</h6>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={prepareFieldingPositionData(selectedPlayer)}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="position" />
                            <YAxis allowDecimals={false} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="count" fill="#82ca9d" name="Innings" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                  
                  {/* Fielding History */}
                  <div className="card">
                    <div className="card-header bg-success text-white">
                      <h5 className="mb-0">Fielding Position History</h5>
                    </div>
                    <div className="card-body">
                      <div className="table-responsive">
                        <table className="table table-striped">
                          <thead>
                            <tr>
                              <th>Date</th>
                              <th>Opponent</th>
                              <th>Positions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedPlayer.position_history.map((game, index) => (
                              <tr key={index}>
                                <td>{game.game_date || "No date"}</td>
                                <td>{game.opponent || "Unknown"}</td>
                                <td>
                                  {game.innings.map((inning, i) => (
                                    <span 
                                      key={i} 
                                      className={`badge me-1 mb-1 ${
                                        inning.position === "Bench" ? "bg-warning" :
                                        ["Pitcher", "1B", "2B", "3B", "SS"].includes(inning.position) ? "bg-primary" :
                                        "bg-success"
                                      }`}
                                      title={`Inning ${inning.inning}`}
                                    >
                                      {inning.position}
                                    </span>
                                  ))}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="alert alert-info">
              Please select a player to view analytics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerAnalytics;