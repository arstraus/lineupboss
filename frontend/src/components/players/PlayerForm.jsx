import React, { useState, useEffect } from "react";

const PlayerForm = ({ player, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    jersey_number: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (player) {
      setFormData({
        first_name: player.first_name || "",
        last_name: player.last_name || "",
        jersey_number: player.jersey_number || ""
      });
    }
  }, [player]);

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
      await onSubmit(formData);
      setFormData({
        first_name: "",
        last_name: "",
        jersey_number: ""
      });
    } catch (err) {
      setError("Error saving player. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="mb-3">
        <label htmlFor="first_name" className="form-label">First Name *</label>
        <input
          type="text"
          className="form-control"
          id="first_name"
          name="first_name"
          value={formData.first_name}
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3">
        <label htmlFor="last_name" className="form-label">Last Name *</label>
        <input
          type="text"
          className="form-control"
          id="last_name"
          name="last_name"
          value={formData.last_name}
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3">
        <label htmlFor="jersey_number" className="form-label">Jersey Number *</label>
        <input
          type="text"
          className="form-control"
          id="jersey_number"
          name="jersey_number"
          value={formData.jersey_number}
          onChange={handleChange}
          required
        />
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
          {loading ? "Saving..." : (player ? "Update Player" : "Add Player")}
        </button>
      </div>
    </form>
  );
};

export default PlayerForm;