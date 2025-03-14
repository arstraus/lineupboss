import api from "./api";

// Player services
export const getTeamPlayers = (teamId) => {
  return api.get(`/players/team/${teamId}`);
};

export const getPlayer = (id) => {
  return api.get(`/players/${id}`);
};

export const createPlayer = (teamId, playerData) => {
  return api.post(`/players/team/${teamId}`, playerData);
};

export const updatePlayer = (id, playerData) => {
  return api.put(`/players/${id}`, playerData);
};

export const deletePlayer = (id) => {
  return api.delete(`/players/${id}`);
};

// Game services
export const getTeamGames = (teamId) => {
  return api.get(`/games/team/${teamId}`);
};

export const getGame = (id) => {
  return api.get(`/games/${id}`);
};

export const createGame = (teamId, gameData) => {
  return api.post(`/games/team/${teamId}`, gameData);
};

export const updateGame = (id, gameData) => {
  return api.put(`/games/${id}`, gameData);
};

export const deleteGame = (id) => {
  return api.delete(`/games/${id}`);
};

// Batting order services
export const getBattingOrder = (gameId) => {
  return api.get(`/games/${gameId}/batting-order`);
};

export const saveBattingOrder = (gameId, orderData) => {
  return api.post(`/games/${gameId}/batting-order`, { order_data: orderData });
};

// Fielding rotation services
export const getFieldingRotations = (gameId) => {
  return api.get(`/games/${gameId}/fielding-rotations`);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  return api.post(`/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

// Player availability services
export const getPlayerAvailability = (gameId) => {
  return api.get(`/games/${gameId}/player-availability`);
};

export const savePlayerAvailability = (gameId, playerId, availabilityData) => {
  return api.post(`/games/${gameId}/player-availability/${playerId}`, availabilityData);
};
