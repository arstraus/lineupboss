import React, { useState, useEffect } from "react";
import { getTeamAnalytics } from "../../services/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const TeamAnalytics = ({ teamId }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");
        
        // Fetch team analytics
        const response = await getTeamAnalytics(teamId);
        setAnalytics(response.data);
      } catch (err) {
        setError("Failed to load team analytics data. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [teamId]);
  
  // Function to transform month data for charts
  const prepareMonthlyData = (data) => {
    if (!data || !data.games_by_month) return [];
    
    return Object.entries(data.games_by_month).map(([month, count]) => {
      // Transform YYYY-MM to a more readable format
      const [year, monthNum] = month.split('-');
      const date = new Date(parseInt(year), parseInt(monthNum) - 1, 1);
      const monthName = date.toLocaleString('default', { month: 'short' });
      
      return {
        month: `${monthName} ${year}`,
        count
      };
    }).sort((a, b) => new Date(a.month) - new Date(b.month));
  };
  
  // Function to transform day of week data for charts
  const prepareDailyData = (data) => {
    if (!data || !data.games_by_day) return [];
    
    // Define the order of days for sorting
    const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    
    return Object.entries(data.games_by_day)
      .map(([day, count]) => ({
        day,
        count
      }))
      .sort((a, b) => dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day));
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
  if (!analytics) {
    return (
      <div className="alert alert-info">
        No team analytics data available. Please add some games first.
      </div>
    );
  }
  
  // Check if there's any actual game data
  const hasGameData = analytics.has_data || 
                     (analytics.total_games > 0 && 
                     (Object.keys(analytics.games_by_month).length > 0 || 
                      Object.values(analytics.games_by_day).some(count => count > 0)));
                      
  if (!hasGameData) {
    return (
      <div>
        <h2 className="mb-4">Team Analytics</h2>
        <div className="alert alert-warning">
          <i className="bi bi-exclamation-triangle me-2"></i>
          Team found, but no games with recorded data yet.
          <p className="mt-2 mb-0">
            To collect analytics: add games with dates and complete batting orders and fielding rotations.
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div>
      <h2 className="mb-4">Team Analytics</h2>
      
      <div className="row">
        <div className="col-md-4">
          <div className="card mb-4">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">Summary</h5>
            </div>
            <div className="card-body">
              <ul className="list-group">
                <li className="list-group-item d-flex justify-content-between align-items-center">
                  Total Games
                  <span className="badge bg-primary rounded-pill">{analytics.total_games}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      <div className="row">
        <div className="col-md-6">
          <div className="card mb-4">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">Games by Month</h5>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={prepareMonthlyData(analytics)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#8884d8" name="Games" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        
        <div className="col-md-6">
          <div className="card mb-4">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">Games by Day of Week</h5>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={prepareDailyData(analytics)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#82ca9d" name="Games" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamAnalytics;