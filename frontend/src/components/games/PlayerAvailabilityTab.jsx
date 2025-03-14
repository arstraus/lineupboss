import React, { useState, useEffect } from "react";
import { getPlayerAvailability, batchSavePlayerAvailability } from "../../services/api";

const PlayerAvailabilityTab = ({ gameId, players, refreshPlayers }) => {
  const [availabilityData, setAvailabilityData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchPlayerAvailability();
  }, [gameId, players]);

  const fetchPlayerAvailability = async () => {
    try {
      setLoading(true);
      const response = await getPlayerAvailability(gameId);
      
      // Create a map of player availability
      const availabilityMap = {};
      response.data.forEach(item => {
        availabilityMap[item.player_id] = {
          available: item.available,
          can_play_catcher: item.can_play_catcher
        };
      });
      
      // Merge with player list
      const mergedData = players.map(player => ({
        player_id: player.id,
        name: player.full_name,
        jersey_number: player.jersey_number,
        available: availabilityMap[player.id]?.available ?? true,
        can_play_catcher: availabilityMap[player.id]?.can_play_catcher ?? false
      }));
      
      setAvailabilityData(mergedData);
      setError("");
    } catch (err) {
      setError("Failed to load player availability. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAvailabilityChange = (playerId, available) => {
    setAvailabilityData(prevData => 
      prevData.map(item => 
        item.player_id === playerId 
          ? { ...item, available } 
          : item
      )
    );
  };

  const handleCatcherChange = (playerId, canPlayCatcher) => {
    setAvailabilityData(prevData => 
      prevData.map(item => 
        item.player_id === playerId 
          ? { ...item, can_play_catcher: canPlayCatcher } 
          : item
      )
    );
  };

  const handleSaveAvailability = async () => {
    try {
      setSaving(true);
      setSuccess("");
      setError("");
      
      // Format data for API
      const apiData = availabilityData.map(item => ({
        player_id: item.player_id,
        available: item.available,
        can_play_catcher: item.can_play_catcher
      }));
      
      await batchSavePlayerAvailability(gameId, apiData);
      setSuccess("Player availability saved successfully.");
    } catch (err) {
      setError("Failed to save player availability. Please try again.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const toggleAllAvailability = (available) => {
    setAvailabilityData(prevData => 
      prevData.map(item => ({ ...item, available }))
    );
  };

  if (loading) {
    return <div className="text-center mt-3"><div className="spinner-border"></div></div>;
  }

  if (players.length === 0) {
    return (
      <div className="alert alert-info">
        No players have been added to this team yet. Add players from the team page first.
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Player Availability</h3>
        <div>
          <button 
            className="btn btn-outline-success me-2"
            onClick={() => toggleAllAvailability(true)}
          >
            All Available
          </button>
          <button 
            className="btn btn-outline-danger me-2"
            onClick={() => toggleAllAvailability(false)}
          >
            All Unavailable
          </button>
          <button 
            className="btn btn-primary"
            onClick={handleSaveAvailability}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Availability"}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="table-responsive">
        <table className="table table-striped">
          <thead>
            <tr>
              <th>Jersey #</th>
              <th>Name</th>
              <th className="text-center">Available</th>
              <th className="text-center">Can Play Catcher</th>
            </tr>
          </thead>
          <tbody>
            {availabilityData.map(player => (
              <tr key={player.player_id}>
                <td>{player.jersey_number}</td>
                <td>{player.name}</td>
                <td className="text-center">
                  <div className="form-check d-flex justify-content-center">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={`available-${player.player_id}`}
                      checked={player.available}
                      onChange={(e) => handleAvailabilityChange(player.player_id, e.target.checked)}
                    />
                  </div>
                </td>
                <td className="text-center">
                  <div className="form-check d-flex justify-content-center">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={`catcher-${player.player_id}`}
                      checked={player.can_play_catcher}
                      onChange={(e) => handleCatcherChange(player.player_id, e.target.checked)}
                      disabled={!player.available}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PlayerAvailabilityTab;