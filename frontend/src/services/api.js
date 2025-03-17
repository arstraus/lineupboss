import axios from "axios";

// Define API URL based on environment with better fallback mechanism
let API_URL = '';
try {
  // First try environment variable
  if (process.env.REACT_APP_API_URL) {
    // Check if it's a relative path (starting with /)
    if (process.env.REACT_APP_API_URL.startsWith('/')) {
      // Use the current domain with the relative path
      API_URL = process.env.REACT_APP_API_URL;
    } else {
      // Use absolute URL as provided
      API_URL = process.env.REACT_APP_API_URL;
    }
  } 
  // Then try window.location as fallback
  else if (window.location && window.location.origin) {
    API_URL = window.location.origin + "/api";
  }
  // Last resort fallback
  else {
    API_URL = "/api";  // Relative path fallback
  }
} catch (e) {
  API_URL = "/api";  // Absolute minimum fallback
}

// Set for debugging but not in production
if (process.env.NODE_ENV !== 'production') {
  console.log("API URL:", API_URL);
}

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Export for direct use in components
export { api };

// Add request interceptor to include auth token - simplified and more reliable approach
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage for each request (always fresh)
    const token = localStorage.getItem("token");
    
    // Enhanced logging in development and production for troubleshooting
    console.log(`Request to: ${config.method?.toUpperCase()} ${config.url}`);
    console.log(`API Base URL: ${config.baseURL}`);
    console.log(`Full URL: ${config.baseURL}${config.url}`);
    
    // If we have a token, add it to this specific request only
    if (token) {
      // Set Authorization header for this request only
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`Using token: ${token.substring(0, 10)}...`);
    } else {
      console.warn("No authentication token found!");
    }
    
    return config;
  },
  (error) => {
    // Log the error and reject the promise
    console.error("API request preparation failed:", error.message);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`Response from ${response.config.url}: Status ${response.status}`);
    return response;
  },
  (error) => {
    console.error("API request failed:", error.message);
    if (error.response) {
      console.error(`Status: ${error.response.status}`);
      console.error("Response data:", error.response.data);
    }
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
  // Try without trailing slash
  return api.get("/teams"); 
};

export const getTeam = (id) => {
  return api.get(`/teams/${id}`); 
};

export const createTeam = (teamData) => {
  // Try without trailing slash
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
  // Ensure consistent URL format without trailing slashes
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

// AI Fielding Rotation Generation
export const generateAIFieldingRotation = (gameId, rotationData) => {
  return api.post(`/games/${gameId}/ai-fielding-rotation`, rotationData);
};

export default api;
