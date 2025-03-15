import React, { useState, useEffect, useCallback } from "react";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import { getBattingOrder, saveBattingOrder, getPlayerAvailability } from "../../services/api";

const BattingOrderTab = ({ gameId, players }) => {
  const [battingOrder, setBattingOrder] = useState([]);
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Get player availability
      const availabilityResponse = await getPlayerAvailability(gameId);
      const availabilityMap = {};
      availabilityResponse.data.forEach(item => {
        availabilityMap[item.player_id] = item.available;
      });
      
      // Filter available players
      const availablePlayers = players.filter(player => 
        availabilityMap[player.id] !== false
      ).map(player => ({
        id: player.id,
        name: player.full_name,
        jersey_number: player.jersey_number
      }));
      
      // Get batting order
      try {
        const orderResponse = await getBattingOrder(gameId);
        
        // Extract player order from the response
        const savedOrder = orderResponse.data.order_data || [];
        
        // Create an array of available players not in the batting order
        const playerMap = availablePlayers.reduce((map, player) => {
          map[player.id] = player;
          return map;
        }, {});
        
        // Convert order to player objects
        const orderWithDetails = savedOrder.map(playerId => playerMap[playerId]).filter(Boolean);
        
        // Remove ordered players from available list
        const remainingPlayers = availablePlayers.filter(player => 
          !savedOrder.includes(player.id)
        );
        
        setBattingOrder(orderWithDetails);
        setAvailablePlayers(remainingPlayers);
      } catch (err) {
        // If no batting order exists yet, just use all available players
        setAvailablePlayers(availablePlayers);
        setBattingOrder([]);
      }
      
      setError("");
    } catch (err) {
      setError("Failed to load batting order data. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [gameId, players]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSaveOrder = async () => {
    try {
      setSaving(true);
      setSuccess("");
      setError("");
      
      // Extract player IDs for the API
      const orderData = battingOrder.map(player => player.id);
      
      await saveBattingOrder(gameId, orderData);
      setSuccess("Batting order saved successfully.");
    } catch (err) {
      setError("Failed to save batting order. Please try again.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDragEnd = (result) => {
    const { source, destination } = result;
    
    // Dropped outside a droppable area
    if (!destination) return;
    
    // Same container, reordering
    if (source.droppableId === destination.droppableId) {
      if (source.droppableId === "battingOrder") {
        const items = Array.from(battingOrder);
        const [reorderedItem] = items.splice(source.index, 1);
        items.splice(destination.index, 0, reorderedItem);
        setBattingOrder(items);
      } else if (source.droppableId === "availablePlayers") {
        const items = Array.from(availablePlayers);
        const [reorderedItem] = items.splice(source.index, 1);
        items.splice(destination.index, 0, reorderedItem);
        setAvailablePlayers(items);
      }
    } else {
      // Moving between lists
      if (source.droppableId === "battingOrder" && destination.droppableId === "availablePlayers") {
        // Remove from batting order, add to available
        const battingItems = Array.from(battingOrder);
        const availableItems = Array.from(availablePlayers);
        const [movedItem] = battingItems.splice(source.index, 1);
        availableItems.splice(destination.index, 0, movedItem);
        
        setBattingOrder(battingItems);
        setAvailablePlayers(availableItems);
      } else if (source.droppableId === "availablePlayers" && destination.droppableId === "battingOrder") {
        // Remove from available, add to batting order
        const battingItems = Array.from(battingOrder);
        const availableItems = Array.from(availablePlayers);
        const [movedItem] = availableItems.splice(source.index, 1);
        battingItems.splice(destination.index, 0, movedItem);
        
        setBattingOrder(battingItems);
        setAvailablePlayers(availableItems);
      }
    }
  };

  if (loading) {
    return <div className="text-center mt-3"><div className="spinner-border"></div></div>;
  }

  // If there are no available players
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
        <h3>Batting Order</h3>
        <button 
          className="btn btn-primary"
          onClick={handleSaveOrder}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Batting Order"}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="row">
        <DragDropContext onDragEnd={handleDragEnd}>
          {/* Available Players Column */}
          <div className="col-md-6 mb-4">
            <div className="card h-100">
              <div className="card-header bg-secondary text-white">
                <h5 className="mb-0">Available Players</h5>
              </div>
              <Droppable droppableId="availablePlayers">
                {(provided) => (
                  <div 
                    className="card-body" 
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    style={{ minHeight: "400px" }}
                  >
                    {availablePlayers.length === 0 ? (
                      <div className="text-center text-muted my-5">
                        <p>All available players have been added to the batting order</p>
                      </div>
                    ) : (
                      availablePlayers.map((player, index) => (
                        <Draggable 
                          key={player.id.toString()} 
                          draggableId={player.id.toString()} 
                          index={index}
                        >
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className="card mb-2"
                            >
                              <div className="card-body py-2 d-flex align-items-center">
                                <div className="me-2">#{player.jersey_number}</div>
                                <div>{player.name}</div>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          </div>

          {/* Batting Order Column */}
          <div className="col-md-6 mb-4">
            <div className="card h-100">
              <div className="card-header bg-primary text-white">
                <h5 className="mb-0">Batting Order</h5>
              </div>
              <Droppable droppableId="battingOrder">
                {(provided) => (
                  <div 
                    className="card-body" 
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    style={{ minHeight: "400px" }}
                  >
                    {battingOrder.length === 0 ? (
                      <div className="text-center text-muted my-5">
                        <p>Drag players here to set the batting order</p>
                      </div>
                    ) : (
                      battingOrder.map((player, index) => (
                        <Draggable 
                          key={player.id.toString()} 
                          draggableId={player.id.toString()} 
                          index={index}
                        >
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className="card mb-2"
                            >
                              <div className="card-body py-2 d-flex align-items-center">
                                <div className="me-2 fw-bold">{index + 1}.</div>
                                <div className="me-2">#{player.jersey_number}</div>
                                <div>{player.name}</div>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          </div>
        </DragDropContext>
      </div>
    </div>
  );
};

export default BattingOrderTab;