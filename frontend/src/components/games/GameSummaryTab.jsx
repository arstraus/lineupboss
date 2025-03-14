import React, { useState, useEffect, useRef } from "react";
import { getBattingOrder, getFieldingRotations, getPlayerAvailability, getTeam } from "../../services/api";
import html2pdf from "html2pdf.js";

const GameSummaryTab = ({ gameId, players, game, innings }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [battingOrder, setBattingOrder] = useState([]);
  const [fieldingRotations, setFieldingRotations] = useState([]);
  const [playerAvailability, setPlayerAvailability] = useState([]);
  const [teamDetails, setTeamDetails] = useState(null);
  const summaryRef = useRef(null);

  useEffect(() => {
    fetchData();
  }, [gameId, game]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");
      
      // Fetch team details
      const teamResponse = await getTeam(game.team_id);
      setTeamDetails(teamResponse.data);
      
      // Get batting order
      try {
        const battingOrderResponse = await getBattingOrder(gameId);
        const orderData = battingOrderResponse.data.order_data || [];
        
        // Create an array of player objects in batting order
        const playerMap = players.reduce((map, player) => {
          map[player.id] = player;
          return map;
        }, {});
        
        const orderedPlayers = orderData
          .map(playerId => playerMap[playerId])
          .filter(Boolean);
          
        setBattingOrder(orderedPlayers);
      } catch (err) {
        console.error("Failed to load batting order:", err);
        setBattingOrder([]);
      }

      // Get fielding rotations
      try {
        const rotationsResponse = await getFieldingRotations(gameId);
        setFieldingRotations(rotationsResponse.data);
      } catch (err) {
        console.error("Failed to load fielding rotations:", err);
        setFieldingRotations([]);
      }

      // Get player availability
      try {
        const availabilityResponse = await getPlayerAvailability(gameId);
        setPlayerAvailability(availabilityResponse.data);
      } catch (err) {
        console.error("Failed to load player availability:", err);
        setPlayerAvailability([]);
      }
    } catch (err) {
      setError("Failed to load game summary data. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getPlayerPosition = (playerId, inning) => {
    const rotation = fieldingRotations.find(r => r.inning === inning);
    if (!rotation || !rotation.positions) return "";

    for (const [position, posPlayerId] of Object.entries(rotation.positions)) {
      if (posPlayerId === playerId) {
        return position;
      }
    }
    return "";
  };

  const isPlayerAvailable = (playerId) => {
    const availability = playerAvailability.find(a => a.player_id === playerId);
    return availability ? availability.available : false;
  };

  // Removed unused getPlayerById function

  const generatePDF = () => {
    if (!summaryRef.current) return;
    
    const title = `Game_${game.game_number}_vs_${game.opponent.replace(/\s+/g, '_')}`;
    
    // html2pdf options
    const options = {
      margin: 10,
      filename: `${title}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
    };
    
    // Generate PDF from the summary content
    html2pdf().from(summaryRef.current).set(options).save();
  };

  if (loading) {
    return <div className="text-center mt-3"><div className="spinner-border"></div></div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Game Summary</h3>
        <button 
          className="btn btn-primary"
          onClick={generatePDF}
        >
          <i className="bi bi-file-earmark-pdf me-2"></i>Export as PDF
        </button>
      </div>
      
      <div ref={summaryRef}>

      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">Team Information</h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <p><strong>Team:</strong> {teamDetails?.name || 'N/A'}</p>
              <p><strong>League:</strong> {teamDetails?.league || 'N/A'}</p>
            </div>
            <div className="col-md-6">
              <p><strong>Head Coach:</strong> {teamDetails?.head_coach || 'N/A'}</p>
              <p><strong>Assistant Coaches:</strong> {teamDetails?.assistant_coach1 || 'N/A'}, {teamDetails?.assistant_coach2 || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">Game Information</h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <p><strong>Opponent:</strong> {game.opponent}</p>
              <p><strong>Date:</strong> {new Date(game.date).toLocaleDateString()}</p>
            </div>
            <div className="col-md-6">
              <p><strong>Time:</strong> {game.time ? new Date(`2022-01-01T${game.time}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</p>
              <p><strong>Innings:</strong> {game.innings}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="table-responsive">
        <table className="table table-bordered table-striped">
          <thead>
            <tr className="bg-primary text-white">
              <th>Batting Order</th>
              <th>Jersey #</th>
              <th>Player Name</th>
              <th>Available</th>
              {Array.from({ length: innings }).map((_, i) => (
                <th key={i+1}>Inning {i+1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {battingOrder.length > 0 ? (
              battingOrder.map((player, index) => (
                <tr key={player.id}>
                  <td>{index + 1}</td>
                  <td>{player.jersey_number}</td>
                  <td>{player.full_name || `${player.first_name} ${player.last_name}`}</td>
                  <td>{isPlayerAvailable(player.id) ? "Yes" : "No"}</td>
                  {Array.from({ length: innings }).map((_, i) => (
                    <td key={i+1}>{getPlayerPosition(player.id, i+1)}</td>
                  ))}
                </tr>
              ))
            ) : (
              players.map((player) => (
                <tr key={player.id}>
                  <td>-</td>
                  <td>{player.jersey_number}</td>
                  <td>{player.full_name || `${player.first_name} ${player.last_name}`}</td>
                  <td>{isPlayerAvailable(player.id) ? "Yes" : "No"}</td>
                  {Array.from({ length: innings }).map((_, i) => (
                    <td key={i+1}>{getPlayerPosition(player.id, i+1)}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      </div>
      
      <div className="mt-4 mb-4">
        <div className="alert alert-info">
          <i className="bi bi-info-circle-fill me-2"></i>
          Use the Export as PDF button to download a printable version of this game summary.
        </div>
      </div>
    </div>
  );
};

export default GameSummaryTab;