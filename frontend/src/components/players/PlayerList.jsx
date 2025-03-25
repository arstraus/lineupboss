import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { get, post, put, del as deleteMethod } from "../../services/api";
import axios from "axios";
import PlayerForm from "./PlayerForm";
import CSVUploadForm from "./CSVUploadForm";

const PlayerList = ({ teamId }) => {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [showCSVUpload, setShowCSVUpload] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState(null);

  useEffect(() => {
    fetchPlayers();
  }, [teamId]);

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      const response = await get(`/teams/${teamId}/players`);
      setPlayers(response.data);
      setError("");
    } catch (err) {
      setError("Failed to load players. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPlayer = async (playerData) => {
    try {
      await post(`/players/team/${teamId}`, playerData);
      setShowAddForm(false);
      fetchPlayers();
    } catch (err) {
      setError("Failed to add player. Please try again.");
      console.error(err);
      throw err;
    }
  };

  const handleUpdatePlayer = async (playerId, playerData) => {
    try {
      await put(`/players/${playerId}`, playerData);
      setEditingPlayer(null);
      fetchPlayers();
    } catch (err) {
      setError("Failed to update player. Please try again.");
      console.error(err);
      throw err;
    }
  };

  const handleDeletePlayer = async (playerId) => {
    if (window.confirm("Are you sure you want to delete this player? This action cannot be undone.")) {
      try {
        await deleteMethod(`/players/${playerId}`);
        fetchPlayers();
      } catch (err) {
        setError("Failed to delete player. Please try again.");
        console.error(err);
      }
    }
  };

  if (loading) {
    return <div className="text-center mt-3"><div className="spinner-border"></div></div>;
  }

  const handleCSVUploadComplete = () => {
    setShowCSVUpload(false);
    fetchPlayers();
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Players</h3>
        <div className="btn-group">
          <button 
            className="btn btn-success" 
            onClick={() => {
              setShowAddForm(!showAddForm);
              setShowCSVUpload(false);
            }}
          >
            {showAddForm ? "Cancel" : "Add Player"}
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
            <h4 className="mb-0">Add New Player</h4>
          </div>
          <div className="card-body">
            <PlayerForm 
              onSubmit={handleAddPlayer} 
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
          hasExistingPlayers={players.length > 0}
        />
      )}

      {players.length === 0 ? (
        <div className="alert alert-info">
          No players added yet. Click "Add Player" to get started.
        </div>
      ) : (
        <div className="table-responsive">
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Jersey #</th>
                <th>Name</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {players.map(player => (
                <tr key={player.id}>
                  <td>{player.jersey_number}</td>
                  <td>{player.full_name}</td>
                  <td>
                    <div className="btn-group">
                      <button 
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => setEditingPlayer(player)}
                      >
                        Edit
                      </button>
                      <button 
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => handleDeletePlayer(player.id)}
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
      )}

      {editingPlayer && (
        <div className="modal-overlay" onClick={() => setEditingPlayer(null)}>
          <div className="modal" style={{display: 'block'}}>
            <div className="modal-dialog" onClick={e => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Edit Player: {editingPlayer.full_name}</h5>
                  <button 
                    type="button" 
                    className="btn-close" 
                    onClick={() => setEditingPlayer(null)}
                  ></button>
                </div>
                <div className="modal-body">
                  <PlayerForm 
                    player={editingPlayer} 
                    onSubmit={(data) => handleUpdatePlayer(editingPlayer.id, data)}
                    onCancel={() => setEditingPlayer(null)}
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

export default PlayerList;