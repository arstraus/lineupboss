import { get, post, put, del as deleteMethod } from "./api";

// Player services
export const getTeamPlayers = (teamId) => {
  return get(`/players/team/${teamId}`);
};

export const getPlayer = (id) => {
  return get(`/players/${id}`);
};

export const createPlayer = (teamId, playerData) => {
  return post(`/players/team/${teamId}`, playerData);
};

export const updatePlayer = (id, playerData) => {
  return put(`/players/${id}`, playerData);
};

export const deletePlayer = (id) => {
  return deleteMethod(`/players/${id}`);
};

// Game services
export const getTeamGames = (teamId) => {
  // Use the legacy route that matches games.py implementation
  // This explicitly uses the /api/games/team/{teamId} route from line 18 in games.py
  return get(`/games/team/${teamId}`);
};

export const getGame = (id) => {
  return get(`/games/${id}`);
};

export const createGame = (teamId, gameData) => {
  // Use the route that matches games.py implementation
  // This uses the /api/games/team/{teamId} POST route from line 100 in games.py
  console.log(`Creating game for team ${teamId} with data:`, gameData);
  return post(`/games/team/${teamId}`, gameData);
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
