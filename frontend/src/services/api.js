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

// Direct axios method exports
export const post = axios.post;
export const get = axios.get;
export const put = axios.put;
export const del = axios.delete;

// Export api object for named import
export const api = {
  get: axios.get,
  post: axios.post,
  put: axios.put,
  delete: axios.delete
};

// Default export for backward compatibility
export default api;

// AUTH API
export const login = (email, password) => {
  return axios.post('/api/auth/login', { email, password });
};

export const register = (email, password) => {
  return axios.post('/api/auth/register', { email, password });
};

export const getCurrentUser = () => {
  return axios.get('/api/auth/me');
};

// USER PROFILE API
export const getUserProfile = () => {
  return axios.get('/api/user/profile');
};

export const updateUserProfile = (profileData) => {
  return axios.put('/api/user/profile', profileData);
};

export const updatePassword = (currentPassword, newPassword) => {
  return axios.put('/api/user/password', {
    current_password: currentPassword,
    new_password: newPassword
  });
};

export const getUserSubscription = () => {
  return axios.get('/api/user/subscription');
};

// TEAMS API
export const getTeams = () => {
  return axios.get('/api/teams');
};

export const getTeam = (teamId) => {
  return axios.get(`/api/teams/${teamId}`);
};

export const createTeam = (teamData) => {
  return axios.post('/api/teams', teamData);
};

export const updateTeam = (teamId, teamData) => {
  return axios.put(`/api/teams/${teamId}`, teamData);
};

export const deleteTeam = (teamId) => {
  return axios.delete(`/api/teams/${teamId}`);
};

// PLAYERS API
export const getPlayers = (teamId) => {
  return axios.get(`/api/teams/${teamId}/players`);
};

export const getPlayer = (playerId) => {
  return axios.get(`/api/players/${playerId}`);
};

export const createPlayer = (teamId, playerData) => {
  return axios.post(`/api/teams/${teamId}/players`, playerData);
};

export const updatePlayer = (playerId, playerData) => {
  return axios.put(`/api/players/${playerId}`, playerData);
};

export const deletePlayer = (playerId) => {
  return axios.delete(`/api/players/${playerId}`);
};

// GAMES API
export const getGames = (teamId) => {
  return axios.get(`/api/teams/${teamId}/games`);
};

export const getGame = (gameId) => {
  return axios.get(`/api/games/${gameId}`);
};

export const createGame = (teamId, gameData) => {
  return axios.post(`/api/teams/${teamId}/games`, gameData);
};

export const updateGame = (gameId, gameData) => {
  return axios.put(`/api/games/${gameId}`, gameData);
};

export const deleteGame = (gameId) => {
  return axios.delete(`/api/games/${gameId}`);
};

// ADMIN API
export const getPendingUsers = () => {
  return axios.get('/api/admin/pending-users');
};

export const approveUser = (userId) => {
  return axios.post(`/api/admin/approve/${userId}`);
};

export const rejectUser = (userId) => {
  return axios.post(`/api/admin/reject/${userId}`);
};

export const getPendingCount = () => {
  return axios.get('/api/admin/pending-count');
};

// SYSTEM API
export const checkApiHealth = async () => {
  try {
    const response = await axios.get('/api', { timeout: 5000 });
    return { status: 'ok', message: response.data?.message || 'API is available', data: response.data };
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
  return axios.get(`/api/games/${gameId}/batting-order`);
};

export const updateBattingOrder = (gameId, orderData) => {
  return axios.put(`/api/games/${gameId}/batting-order`, orderData);
};

export const saveBattingOrder = (gameId, orderData) => {
  return axios.post(`/api/games/${gameId}/batting-order`, { order_data: orderData });
};

export const getFieldingRotations = (gameId) => {
  return axios.get(`/api/games/${gameId}/fielding-rotations`);
};

export const updateFieldingRotation = (gameId, inning, positionsData) => {
  return axios.put(`/api/games/${gameId}/fielding-rotations/${inning}`, positionsData);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  return axios.post(`/api/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

export const getPlayerAvailability = (gameId) => {
  return axios.get(`/api/games/${gameId}/player-availability`);
};

export const updatePlayerAvailability = (gameId, availabilityData) => {
  return axios.put(`/api/games/${gameId}/player-availability`, availabilityData);
};

export const batchSavePlayerAvailability = (gameId, playerAvailabilityArray) => {
  return axios.post(`/api/games/${gameId}/player-availability/batch`, { players: playerAvailabilityArray });
};