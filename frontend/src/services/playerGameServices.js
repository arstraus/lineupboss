import { get, post, put, del as deleteMethod } from "./api";

// Player services
export const getTeamPlayers = (teamId) => {
  // Use REST-style nested route pattern
  return get(`/teams/${teamId}/players`);
};

export const getPlayer = (id) => {
  return get(`/players/${id}`);
};

export const createPlayer = (teamId, playerData) => {
  // Use RESTful pattern to match the direct route in backend
  return post(`/teams/${teamId}/players`, playerData);
};

export const updatePlayer = (id, playerData) => {
  return put(`/players/${id}`, playerData);
};

export const deletePlayer = (id) => {
  return deleteMethod(`/players/${id}`);
};

// Game services
export const getTeamGames = (teamId) => {
  // Use REST-style nested route pattern
  return get(`/teams/${teamId}/games`);
};

export const getGame = (id) => {
  return get(`/games/${id}`);
};

export const createGame = (teamId, gameData) => {
  // Use RESTful pattern to match the direct route in backend
  console.log(`Creating game for team ${teamId} with data:`, gameData);
  return post(`/teams/${teamId}/games`, gameData);
};

export const updateGame = (id, gameData) => {
  return put(`/games/${id}`, gameData);
};

export const deleteGame = (id) => {
  return deleteMethod(`/games/${id}`);
};

// Batting order services
export const getBattingOrder = (gameId) => {
  return get(`/games/${gameId}/batting-order`);
};

export const saveBattingOrder = (gameId, orderData) => {
  return post(`/games/${gameId}/batting-order`, { order_data: orderData });
};

// Fielding rotation services
export const getFieldingRotations = (gameId) => {
  return get(`/games/${gameId}/fielding-rotations`);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  return post(`/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

// Player availability services
export const getPlayerAvailability = (gameId) => {
  return get(`/games/${gameId}/player-availability`);
};

export const savePlayerAvailability = (gameId, playerId, availabilityData) => {
  return post(`/games/${gameId}/player-availability/${playerId}`, availabilityData);
};
