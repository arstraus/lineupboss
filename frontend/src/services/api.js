import axios from "axios";

// Define API URL based on environment
const API_URL = process.env.REACT_APP_API_URL || window.location.origin + "/api";
console.log("API URL:", API_URL);

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    
    // Log the actual URL being requested
    console.log(`Request to: ${config.method?.toUpperCase()} ${config.url}`);
    
    if (token) {
      // Make sure we're setting the Authorization header properly
      const authHeader = `Bearer ${token}`;
      console.log("Authorization header:", authHeader);
      
      // Set headers for this specific request
      config.headers = {
        ...config.headers,
        "Authorization": authHeader,
        "Content-Type": "application/json"
      };
      
      // Also set the default headers for all future requests
      axios.defaults.headers.common["Authorization"] = authHeader;
      api.defaults.headers.common["Authorization"] = authHeader;
    } else {
      console.warn("No token found in localStorage - request will fail if authentication is required");
    }
    
    return config;
  },
  (error) => {
    console.error("Request interceptor error:", error);
    return Promise.reject(error);
  }
);

// Auth services
export const register = (email, password) => {
  return api.post("/auth/register", { email, password });
};

export const login = (email, password) => {
  return api.post("/auth/login", { email, password });
};

export const getCurrentUser = () => {
  return api.get("/auth/me");
};

// Team services
export const getTeams = () => {
  return api.get("/teams");
};

export const getTeam = (id) => {
  return api.get(`/teams/${id}`);
};

export const createTeam = (teamData) => {
  return api.post("/teams", teamData);
};

export const updateTeam = (id, teamData) => {
  return api.put(`/teams/${id}`, teamData);
};

export const deleteTeam = (id) => {
  return api.delete(`/teams/${id}`);
};

// Player services
export const getPlayers = (teamId) => {
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
export const getGames = (teamId) => {
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

export const saveFieldingRotation = (gameId, inning, positionsData) => {
  return api.post(`/games/${gameId}/fielding-rotations/${inning}`, { positions: positionsData });
};

// Player availability services
export const getPlayerAvailability = (gameId) => {
  return api.get(`/games/${gameId}/player-availability`);
};

export const savePlayerAvailability = (gameId, playerId, available, canPlayCatcher = false) => {
  return api.post(`/games/${gameId}/player-availability/${playerId}`, { 
    available, 
    can_play_catcher: canPlayCatcher 
  });
};

export const batchSavePlayerAvailability = (gameId, availabilityData) => {
  return api.post(`/games/${gameId}/player-availability/batch`, availabilityData);
};

export default api;
