import React, { useState, useRef } from "react";
import axios from "axios";
import { getApiUrl } from "../../services/api";

const CSVUploadForm = ({ teamId, onUploadComplete, onCancel, hasExistingGames }) => {
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
      
      // Get template download URL
      const url = getApiUrl(`teams/${teamId}/games/csv-template`);
      
      // Use axios for blob download
      const response = await axios.get(url, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `games_template.csv`);
      
      // Append to html
      document.body.appendChild(link);
      
      // Start download
      link.click();
      
      // Clean up and remove the link
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError("Failed to download template. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    // If there are existing games and override is checked but not confirmed
    if (hasExistingGames && overrideExisting && !confirmOverride) {
      setConfirmOverride(true);
      return;
    }
    
    try {
      setLoading(true);
      setError("");
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('overrideExisting', overrideExisting);
      
      // Get API URL
      const url = getApiUrl(`teams/${teamId}/games`);
      
      // Use axios to make the request
      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const data = response.data;
      
      // Handle response (could have partial success)
      if (response.status === 207) {
        // Some rows had errors
        setError(`Imported ${data.imported_count} games with ${data.errors.length} errors: ${data.errors.join(', ')}`);
      }
      
      // Signal completion to parent component
      onUploadComplete();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || "Failed to upload games. Please check your file format.");
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
        <h4 className="mb-0">Upload Games from CSV</h4>
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
            <p><strong>Warning:</strong> This will delete all existing games for this team and replace them with the games from your CSV file.</p>
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
                Yes, Replace All Games
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
                CSV file must include game_number and opponent columns. date (YYYY-MM-DD), time (HH:MM), and innings are optional.
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
            
            {hasExistingGames && (
              <div className="mb-3 form-check">
                <input
                  type="checkbox"
                  className="form-check-input"
                  id="overrideExisting"
                  checked={overrideExisting}
                  onChange={(e) => setOverrideExisting(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="overrideExisting">
                  Replace all existing games with CSV data
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
                {loading ? "Uploading..." : "Upload Games"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default CSVUploadForm;