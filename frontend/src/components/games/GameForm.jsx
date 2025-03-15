import React, { useState, useEffect } from "react";

const GameForm = ({ game, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    game_number: "",
    opponent: "",
    date: "",
    time: "",
    innings: 6
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (game) {
      // Format the date for the input field if it exists
      let formattedDate = "";
      if (game.date) {
        if (game.date.includes("T")) {
          formattedDate = game.date.split("T")[0];
        } else {
          // Prevent timezone issues: ensure date is interpreted in local timezone
          formattedDate = game.date;
        }
      }
      
      // Format the time for the input field if it exists
      let formattedTime = "";
      if (game.time) {
        // Handle time in HH:MM:SS format
        if (game.time.includes(":")) {
          formattedTime = game.time.substring(0, 5); // Get just HH:MM
        }
        // Handle ISO datetime or other formats
        else if (game.time.includes("T")) {
          const timeObj = new Date(game.time);
          formattedTime = timeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        }
      }
      
      setFormData({
        game_number: game.game_number || "",
        opponent: game.opponent || "",
        date: formattedDate,
        time: formattedTime,
        innings: game.innings || 6
      });
    }
  }, [game]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // Prepare the data with the proper format for the API
      const gameData = {
        ...formData,
        // Ensure we're sending the date in the proper ISO format
        // but without time component to avoid timezone issues
        date: formData.date || null,
        innings: parseInt(formData.innings, 10)
      };

      await onSubmit(gameData);
      // Reset form if not updating
      if (!game) {
        setFormData({
          game_number: "",
          opponent: "",
          date: "",
          time: "",
          innings: 6
        });
      }
    } catch (err) {
      setError("Error saving game. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="mb-3">
        <label htmlFor="game_number" className="form-label">Game Number *</label>
        <input
          type="number"
          className="form-control"
          id="game_number"
          name="game_number"
          value={formData.game_number}
          onChange={handleChange}
          required
          min="1"
        />
      </div>

      <div className="mb-3">
        <label htmlFor="opponent" className="form-label">Opponent *</label>
        <input
          type="text"
          className="form-control"
          id="opponent"
          name="opponent"
          value={formData.opponent}
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3">
        <label htmlFor="date" className="form-label">Date</label>
        <input
          type="date"
          className="form-control"
          id="date"
          name="date"
          value={formData.date}
          onChange={handleChange}
        />
      </div>

      <div className="mb-3">
        <label htmlFor="time" className="form-label">Time</label>
        <input
          type="time"
          className="form-control"
          id="time"
          name="time"
          value={formData.time}
          onChange={handleChange}
        />
      </div>

      <div className="mb-3">
        <label htmlFor="innings" className="form-label">Innings</label>
        <select
          className="form-select"
          id="innings"
          name="innings"
          value={formData.innings}
          onChange={handleChange}
        >
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5</option>
          <option value="6">6</option>
          <option value="7">7</option>
          <option value="8">8</option>
          <option value="9">9</option>
        </select>
      </div>

      <div className="d-flex justify-content-between">
        <button 
          type="button" 
          className="btn btn-secondary"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? "Saving..." : (game ? "Update Game" : "Add Game")}
        </button>
      </div>
    </form>
  );
};

export default GameForm;