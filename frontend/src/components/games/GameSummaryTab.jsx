import React, { useState, useEffect, useRef } from "react";
import { getBattingOrder, getFieldingRotations, getPlayerAvailability, getTeam } from "../../services/api";
import html2pdf from "html2pdf.js";

// Helper function to format date properly without timezone issues
const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  
  // Fix for timezone issue: parse date parts directly to avoid timezone offset
  const [year, month, day] = dateString.split('-').map(num => parseInt(num, 10));
  // Month is 0-indexed in JavaScript Date
  const date = new Date(year, month - 1, day);
  
  return date.toLocaleDateString(undefined, options);
};

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
    
    // Check if player is available for this game before showing "Bench"
    if (isPlayerAvailable(playerId)) {
      return "Bench";
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
    
    // html2pdf options with smaller margins and optimized scaling
    const options = {
      margin: [5, 5, 5, 5], // [top, right, bottom, left]
      filename: `${title}.pdf`,
      image: { type: 'jpeg', quality: 0.95 },
      html2canvas: { 
        scale: 1.5, 
        useCORS: true,
        letterRendering: true,
      },
      jsPDF: { 
        unit: 'mm', 
        format: 'a4', 
        orientation: 'landscape',
        compress: true
      },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
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
      
      <div ref={summaryRef} className="pdf-content" style={{ maxWidth: '1050px', margin: '0 auto', fontSize: '0.9em' }}>

      <div className="card mb-3">
        <div className="card-header bg-primary text-white py-1">
          <h5 className="mb-0">Game #{game.game_number}: {teamDetails?.name || 'Team'} vs {game.opponent}</h5>
        </div>
        <div className="card-body py-2">
          <div className="row">
            <div className="col-md-3">
              <p className="mb-1"><small><strong>Team:</strong> {teamDetails?.name || 'N/A'}</small></p>
              <p className="mb-1"><small><strong>League:</strong> {teamDetails?.league || 'N/A'}</small></p>
            </div>
            <div className="col-md-3">
              <p className="mb-1"><small><strong>Head Coach:</strong> {teamDetails?.head_coach || 'N/A'}</small></p>
              <p className="mb-1"><small><strong>Asst1:</strong> {teamDetails?.assistant_coach1 || 'N/A'}</small></p>
              <p className="mb-1"><small><strong>Asst2:</strong> {teamDetails?.assistant_coach2 || 'N/A'}</small></p>
            </div>
            <div className="col-md-3">
              <p className="mb-1"><small><strong>Date:</strong> {game.date ? formatDate(game.date) : 'N/A'}</small></p>
              <p className="mb-1"><small><strong>Time:</strong> {game.time ? new Date(`2022-01-01T${game.time}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</small></p>
            </div>
            <div className="col-md-3">
              <p className="mb-1"><small><strong>Opponent:</strong> {game.opponent}</small></p>
              <p className="mb-1"><small><strong>Innings:</strong> {game.innings}</small></p>
            </div>
          </div>
        </div>
      </div>

      <div className="table-responsive">
        <table className="table table-bordered table-striped table-sm small">
          <thead>
            <tr className="bg-primary text-white">
              <th className="py-1">Bat</th>
              <th className="py-1">#</th>
              <th className="py-1">Player</th>
              <th className="py-1">Avail</th>
              {Array.from({ length: innings }).map((_, i) => (
                <th key={i+1} className="py-1">Inn {i+1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {battingOrder.length > 0 ? (
              battingOrder.map((player, index) => (
                <tr key={player.id}>
                  <td className="py-1">{index + 1}</td>
                  <td className="py-1">{player.jersey_number}</td>
                  <td className="py-1">{player.full_name || `${player.first_name} ${player.last_name}`}</td>
                  <td className="py-1">{isPlayerAvailable(player.id) ? "Y" : "N"}</td>
                  {Array.from({ length: innings }).map((_, i) => {
                    const position = getPlayerPosition(player.id, i+1);
                    return (
                      <td key={i+1} className={`py-1 ${position === 'Bench' ? 'text-muted fst-italic' : ''}`}>
                        {position}
                      </td>
                    );
                  })}
                </tr>
              ))
            ) : (
              players.map((player) => (
                <tr key={player.id}>
                  <td className="py-1">-</td>
                  <td className="py-1">{player.jersey_number}</td>
                  <td className="py-1">{player.full_name || `${player.first_name} ${player.last_name}`}</td>
                  <td className="py-1">{isPlayerAvailable(player.id) ? "Y" : "N"}</td>
                  {Array.from({ length: innings }).map((_, i) => {
                    const position = getPlayerPosition(player.id, i+1);
                    return (
                      <td key={i+1} className={`py-1 ${position === 'Bench' ? 'text-muted fst-italic' : ''}`}>
                        {position}
                      </td>
                    );
                  })}
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