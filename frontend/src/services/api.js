import axios from 'axios';

// Configure axios with base settings
axios.defaults.baseURL = process.env.REACT_APP_API_URL || '';

// Add request interceptor to automatically add token to requests
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Utility function to handle API paths correctly
const apiPath = (path) => {
  // If baseURL already includes /api, remove the leading /api from the path
  if (axios.defaults.baseURL && axios.defaults.baseURL.endsWith('/api')) {
    // Remove leading /api if present to avoid double prefix
    return path.startsWith('/api/') ? path.substring(4) : path;
  }
  return path;
};

// Create wrapped API methods that use apiPath
const wrappedGet = (url, config) => axios.get(apiPath(url), config);
const wrappedPost = (url, data, config) => axios.post(apiPath(url), data, config);
const wrappedPut = (url, data, config) => axios.put(apiPath(url), data, config);
const wrappedDelete = (url, config) => axios.delete(apiPath(url), config);

// Export api object for named import
export const api = {
  get: wrappedGet,
  post: wrappedPost,
  put: wrappedPut,
  delete: wrappedDelete
};

// Export wrapped methods
export const get = wrappedGet;
export const post = wrappedPost;
export const put = wrappedPut;
export const del = wrappedDelete;

// Default export for backward compatibility
export default api;

// AUTH API
export const login = (email, password) => {
  return wrappedPost('/api/auth/login', { email, password });
};

export const register = (email, password) => {
  return wrappedPost('/api/auth/register', { email, password });
};

export const getCurrentUser = () => {
  return wrappedGet('/api/auth/me');
};

// USER PROFILE API
export const getUserProfile = () => {
  return wrappedGet('/api/user/profile');
};

export const updateUserProfile = (profileData) => {
  return wrappedPut('/api/user/profile', profileData);
};

export const updatePassword = (currentPassword, newPassword) => {
  return wrappedPut('/api/user/password', {
    current_password: currentPassword,
    new_password: newPassword
  });
};

export const getUserSubscription = () => {
  return wrappedGet('/api/user/subscription');
};

// TEAMS API
export const getTeams = () => {
  return wrappedGet('/api/teams');
};

export const getTeam = (teamId) => {
  return wrappedGet(`/api/teams/${teamId}`);
};

export const createTeam = (teamData) => {
  return wrappedPost('/api/teams', teamData);
};

export const updateTeam = (teamId, teamData) => {
  return wrappedPut(`/api/teams/${teamId}`, teamData);
};

export const deleteTeam = (teamId) => {
  return wrappedDelete(`/api/teams/${teamId}`);
};

// PLAYERS API
export const getPlayers = (teamId) => {
  return wrappedGet(`/api/teams/${teamId}/players`);
};

export const getPlayer = (playerId) => {
  return wrappedGet(`/api/players/${playerId}`);
};

export const createPlayer = (teamId, playerData) => {
  return wrappedPost(`/api/teams/${teamId}/players`, playerData);
};

export const updatePlayer = (playerId, playerData) => {
  return wrappedPut(`/api/players/${playerId}`, playerData);
};

export const deletePlayer = (playerId) => {
  return wrappedDelete(`/api/players/${playerId}`);
};

// GAMES API
export const getGames = (teamId) => {
  return wrappedGet(`/api/teams/${teamId}/games`);
};

export const getGame = (gameId) => {
  return wrappedGet(`/api/games/${gameId}`);
};

export const createGame = (teamId, gameData) => {
  return wrappedPost(`/api/teams/${teamId}/games`, gameData);
};

export const updateGame = (gameId, gameData) => {
  return wrappedPut(`/api/games/${gameId}`, gameData);
};

export const deleteGame = (gameId) => {
  return wrappedDelete(`/api/games/${gameId}`);
};

// ADMIN API
export const getPendingUsers = () => {
  return wrappedGet('/api/admin/pending-users');
};

export const approveUser = (userId) => {
  return wrappedPost(`/api/admin/approve/${userId}`);
};

export const rejectUser = (userId) => {
  return wrappedPost(`/api/admin/reject/${userId}`);
};

export const getPendingCount = () => {
  return wrappedGet('/api/admin/pending-count');
};

// SYSTEM API
export const checkApiHealth = async () => {
  try {
    const response = await wrappedGet('/api', { timeout: 5000 });
    return { 
      status: 'ok', 
      message: response.data?.message || 'API is available', 
      data: response.data 
    };
  } catch (error) {
    return { 
      status: 'error', 
      message: error.message, 
      isNetworkError: !error.response
    };
  }
};

// LINEUP API
export const getBattingOrder = (gameId) => {
  return wrappedGet(`/api/games/${gameId}/batting-order`);
};

export const updateBattingOrder = (gameId, orderData) => {
  return wrappedPut(`/api/games/${gameId}/batting-order`, orderData);
};

export const saveBattingOrder = (gameId, orderData) => {
  return wrappedPost(`/api/games/${gameId}/batting-order`, { order_data: orderData });
};

export const getFieldingRotations = (gameId) => {
  return wrappedGet(`/api/games/${gameId}/fielding-rotations`);
};

export const updateFieldingRotation = (gameId, inning, positionsData) => {
  return wrappedPut(`/api/games/${gameId}/fielding-rotations/${inning}`, positionsData);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  return wrappedPost(`/api/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

export const getPlayerAvailability = (gameId) => {
  return wrappedGet(`/api/games/${gameId}/player-availability`);
};

export const updatePlayerAvailability = (gameId, availabilityData) => {
  return wrappedPut(`/api/games/${gameId}/player-availability`, availabilityData);
};

export const batchSavePlayerAvailability = (gameId, playerAvailabilityArray) => {
  return wrappedPost(`/api/games/${gameId}/player-availability/batch`, { players: playerAvailabilityArray });
};