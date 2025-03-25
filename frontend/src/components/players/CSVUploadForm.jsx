import React, { useState, useRef } from "react";
import axios from "axios";
import { getAuthToken } from "../../services/auth";

const CSVUploadForm = ({ teamId, onUploadComplete, onCancel, hasExistingPlayers }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [overrideExisting, setOverrideExisting] = useState(false);
  const [confirmOverride, setConfirmOverride] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError("Selected file must be a CSV file");
        setFile(null);
        e.target.value = ''; // Reset file input
        return;
      }
      
      setFile(selectedFile);
      setError("");
    }
  };

  const downloadTemplate = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      
      // Use XMLHttpRequest for blob download
      const xhr = new XMLHttpRequest();
      xhr.open('GET', `${process.env.REACT_APP_API_URL || ''}/teams/${teamId}/players/csv-template`, true);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.responseType = 'blob';
      
      xhr.onload = function() {
        if (xhr.status === 200) {
          // Create blob link to download
          const url = window.URL.createObjectURL(new Blob([xhr.response]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `players_template.csv`);
          
          // Append to html
          document.body.appendChild(link);
          
          // Start download
          link.click();
          
          // Clean up and remove the link
          link.parentNode.removeChild(link);
          window.URL.revokeObjectURL(url);
        } else {
          setError("Failed to download template");
        }
        setLoading(false);
      };
      
      xhr.onerror = function() {
        setError("Network error occurred while downloading template");
        setLoading(false);
      };
      
      xhr.send();
    } catch (err) {
      setError("Failed to download template. Please try again.");
      console.error(err);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    // If there are existing players and override is checked but not confirmed
    if (hasExistingPlayers && overrideExisting && !confirmOverride) {
      setConfirmOverride(true);
      return;
    }
    
    try {
      setLoading(true);
      setError("");
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('overrideExisting', overrideExisting);
      
      const token = getAuthToken();
      
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || ''}/teams/${teamId}/players`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // Handle response (could have partial success)
      if (response.status === 207) {
        // Some rows had errors
        setError(`Imported ${response.data.imported_count} players with ${response.data.errors.length} errors: ${response.data.errors.join(', ')}`);
      }
      
      // Signal completion to parent component
      onUploadComplete();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || "Failed to upload players. Please check your file format.");
    } finally {
      setLoading(false);
      setConfirmOverride(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setError("");
    setOverrideExisting(false);
    setConfirmOverride(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="card mb-3">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h4 className="mb-0">Upload Players from CSV</h4>
        <button 
          type="button" 
          className="btn-close" 
          onClick={onCancel}
          aria-label="Close"
        ></button>
      </div>
      <div className="card-body">
        {error && <div className="alert alert-danger">{error}</div>}
        
        {confirmOverride ? (
          <div className="alert alert-warning">
            <p><strong>Warning:</strong> This will delete all existing players for this team and replace them with the players from your CSV file.</p>
            <p>Are you sure you want to continue?</p>
            <div className="d-flex mt-3">
              <button 
                className="btn btn-secondary me-2" 
                onClick={() => setConfirmOverride(false)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-danger" 
                onClick={handleSubmit}
              >
                Yes, Replace All Players
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="csvFile" className="form-label">Select CSV File</label>
              <input
                type="file"
                className="form-control"
                id="csvFile"
                accept=".csv"
                onChange={handleFileChange}
                ref={fileInputRef}
                required
              />
              <div className="form-text">
                CSV file must include first_name, last_name, and jersey_number columns.
                <button 
                  type="button" 
                  className="btn btn-link p-0 ms-1"
                  onClick={downloadTemplate}
                  disabled={loading}
                >
                  Download template
                </button>
              </div>
            </div>
            
            {hasExistingPlayers && (
              <div className="mb-3 form-check">
                <input
                  type="checkbox"
                  className="form-check-input"
                  id="overrideExisting"
                  checked={overrideExisting}
                  onChange={(e) => setOverrideExisting(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="overrideExisting">
                  Replace all existing players with CSV data
                </label>
              </div>
            )}
            
            <div className="d-flex justify-content-between">
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => {
                  resetForm();
                  onCancel();
                }}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !file}
              >
                {loading ? "Uploading..." : "Upload Players"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default CSVUploadForm;