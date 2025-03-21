import React, { useState } from "react";
import { useParams } from 'react-router-dom';
import PlayerAnalytics from "./PlayerAnalytics";
import TeamAnalytics from "./TeamAnalytics";

const AnalyticsPage = () => {
  const { teamId } = useParams();
  const [activeTab, setActiveTab] = useState("players");
  
  return (
    <div className="container-fluid mt-4">
      <h1 className="mb-4">Season Analytics</h1>
      
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "players" ? "active" : ""}`}
            onClick={() => setActiveTab("players")}
          >
            <i className="bi bi-person-lines-fill me-2"></i>
            Player Analytics
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "team" ? "active" : ""}`}
            onClick={() => setActiveTab("team")}
          >
            <i className="bi bi-bar-chart-line me-2"></i>
            Team Analytics
          </button>
        </li>
      </ul>
      
      {activeTab === "players" ? (
        <PlayerAnalytics teamId={parseInt(teamId)} />
      ) : (
        <TeamAnalytics teamId={parseInt(teamId)} />
      )}
    </div>
  );
};

export default AnalyticsPage;