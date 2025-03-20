import axios from 'axios';

// Configure axios with base settings
axios.defaults.baseURL = process.env.REACT_APP_API_URL || '';
if (process.env.NODE_ENV === 'development') {
  console.log(`[API] Base URL: ${axios.defaults.baseURL || '(none)'}`);
}

// Add request interceptor to automatically add token to requests
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      if (process.env.NODE_ENV === 'development') {
        console.log(`[API] Added authentication token to ${config.method.toUpperCase()} ${config.url}`);
      }
    }
    return config;
  },
  error => {
    console.error('[API] Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling and token refresh
axios.interceptors.response.use(
  response => {
    // Check for token_expires_soon flag in /auth/me response
    const url = response.config.url;
    const isAuthMe = url && (url.endsWith('/api/auth/me') || url.endsWith('/auth/me'));
    
    if (isAuthMe && response.data && response.data.token_expires_soon) {
      // Token is about to expire, attempt to refresh it
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] Token expires soon, scheduling refresh');
      }
      
      // Schedule token refresh without blocking the current response
      setTimeout(() => {
        refreshTokenIfNeeded()
          .then(refreshResult => {
            if (process.env.NODE_ENV === 'development') {
              console.log('[API] Token refresh completed:', refreshResult ? 'Success' : 'No refresh needed');
            }
          })
          .catch(error => {
            console.error('[API] Token refresh failed:', error);
          });
      }, 100); // Small delay to avoid impacting current flow
    }
    
    // Return successful response
    return response;
  },
  async error => {
    // Handle error responses
    if (error.response) {
      // Server responded with a status code outside of 2xx range
      const status = error.response.status;
      const data = error.response.data;
      
      if (process.env.NODE_ENV === 'development') {
        console.error(`[API] Error ${status}:`, data);
      }
      
      // Handle authentication errors
      if (status === 401) {
        const token = localStorage.getItem('token');
        if (token) {
          // Try to refresh the token if it exists
          try {
            const isRefreshed = await refreshTokenIfNeeded();
            
            if (isRefreshed) {
              // Successfully refreshed token, retry the original request
              const config = error.config;
              // Update the Authorization header with new token
              config.headers.Authorization = `Bearer ${localStorage.getItem('token')}`;
              // Create new instance to avoid interceptor loops
              return axios(config);
            }
          } catch (refreshError) {
            // Refresh failed, proceed with normal error handling
            console.error('[API] Token refresh failed:', refreshError);
          }
          
          // If we reach here, token refresh failed or wasn't attempted
          localStorage.removeItem('token');
          console.error('[API] Authentication failed. Please log in again.');
          // Consider adding a global notification here
        }
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('[API] No response received:', error.request);
    } else {
      // Something else happened in setting up the request
      console.error('[API] Request error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Token refresh flag to prevent multiple simultaneous refresh requests
let isRefreshing = false;

// Function to refresh token if needed
async function refreshTokenIfNeeded() {
  // Prevent multiple refresh attempts
  if (isRefreshing) return false;
  
  isRefreshing = true;
  
  try {
    // Use properly processed URL
    const refreshUrl = apiPath('/auth/refresh');
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] Attempting token refresh: POST ${refreshUrl}`);
    }
    
    const response = await axios.post(
      refreshUrl,
      {},
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    // Check if token was refreshed
    if (response.data && response.data.access_token) {
      // Update token in storage
      localStorage.setItem('token', response.data.access_token);
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] Token refreshed successfully, expires:', response.data.expires_at);
      }
      isRefreshing = false;
      return true;
    } else {
      // No refresh needed or performed
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] No token refresh needed:', response.data?.message);
      }
      isRefreshing = false;
      return false;
    }
  } catch (error) {
    console.error('[API] Token refresh error:', error);
    isRefreshing = false;
    throw error;
  }
}

// Simplified utility function to handle API paths correctly
const apiPath = (path) => {
  // Handle null or undefined
  if (!path) return '/api';
  
  // Trim leading and trailing whitespace
  const trimmedPath = path.trim();
  
  // Remove any accidental double slashes
  let normalizedPath = trimmedPath.replace(/\/+/g, '/');
  
  // Ensure path starts with a slash
  if (!normalizedPath.startsWith('/')) {
    normalizedPath = `/${normalizedPath}`;
  }
  
  // Convert legacy resource routes to RESTful nested routes
  if (normalizedPath.includes('/games/team/')) {
    const teamId = normalizedPath.split('/games/team/')[1].split('/')[0];
    normalizedPath = normalizedPath.replace(`/games/team/${teamId}`, `/teams/${teamId}/games`);
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] Standardized legacy games route to: ${normalizedPath}`);
    }
  }
  
  if (normalizedPath.includes('/players/team/')) {
    const teamId = normalizedPath.split('/players/team/')[1].split('/')[0];
    normalizedPath = normalizedPath.replace(`/players/team/${teamId}`, `/teams/${teamId}/players`);
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] Standardized legacy players route to: ${normalizedPath}`);
    }
  }
  
  // Detect if path already has the /api prefix
  const hasApiPrefix = normalizedPath.startsWith('/api/') || normalizedPath === '/api';
  
  // Add API prefix if needed - prevent double /api/api
  if (!hasApiPrefix) {
    return `/api${normalizedPath}`;
  }
  
  // Remove any emergency /api/api/ prefix
  if (normalizedPath.startsWith('/api/api/')) {
    normalizedPath = normalizedPath.replace('/api/api/', '/api/');
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] Removed emergency prefix, using: ${normalizedPath}`);
    }
  }
  
  return normalizedPath;
};

// Simplified request handler wrapper
const createSafeRequestMethod = (method, axiosMethod) => {
  return (url, ...args) => {
    const finalPath = apiPath(url);
    
    // Log API calls in development mode
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${method} ${finalPath}`);
    }
    
    // Make the actual request with the standardized path
    return axiosMethod(finalPath, ...args);
  };
};

// Create wrapped API methods that use the enhanced request handler
const wrappedGet = createSafeRequestMethod('GET', axios.get);
const wrappedPost = createSafeRequestMethod('POST', (url, data, config) => axios.post(url, data, config));
const wrappedPut = createSafeRequestMethod('PUT', (url, data, config) => axios.put(url, data, config));
// Fix for DELETE operations - ensure proper config passing
const wrappedDelete = createSafeRequestMethod('DELETE', (url, config) => axios.delete(url, config));

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
  return wrappedPost('/auth/login', { email, password });
};

export const register = (email, password) => {
  return wrappedPost('/auth/register', { email, password });
};

export const getCurrentUser = () => {
  return wrappedGet('/auth/me');
};

export const refreshToken = () => {
  return wrappedPost('/auth/refresh');
};

// USER PROFILE API
export const getUserProfile = () => {
  return wrappedGet('/user/profile');
};

export const updateUserProfile = (profileData) => {
  return wrappedPut('/user/profile', profileData);
};

export const updatePassword = (currentPassword, newPassword) => {
  return wrappedPut('/user/password', {
    current_password: currentPassword,
    new_password: newPassword
  });
};

export const getUserSubscription = () => {
  return wrappedGet('/user/subscription');
};

// TEAMS API
export const getTeams = () => {
  return wrappedGet('/teams');
};

export const getTeam = (teamId) => {
  return wrappedGet(`/teams/${teamId}`);
};

export const createTeam = (teamData) => {
  return wrappedPost('/teams', teamData);
};

export const updateTeam = (teamId, teamData) => {
  return wrappedPut(`/teams/${teamId}`, teamData);
};

export const deleteTeam = (teamId) => {
  return wrappedDelete(`/teams/${teamId}`);
};

// PLAYERS API
export const getPlayers = (teamId) => {
  // Use standardized nested REST route
  return wrappedGet(`/teams/${teamId}/players`);
};

export const getPlayer = (playerId) => {
  return wrappedGet(`/players/${playerId}`);
};

export const createPlayer = (teamId, playerData) => {
  // Use standardized nested REST route
  return wrappedPost(`/teams/${teamId}/players`, playerData);
};

export const updatePlayer = (playerId, playerData) => {
  return wrappedPut(`/players/${playerId}`, playerData);
};

export const deletePlayer = (playerId) => {
  return wrappedDelete(`/players/${playerId}`);
};

// GAMES API
export const getGames = (teamId) => {
  // Use standardized nested REST route
  return wrappedGet(`/teams/${teamId}/games`);
};

export const getGame = (gameId) => {
  return wrappedGet(`/games/${gameId}`);
};

export const createGame = (teamId, gameData) => {
  // Use standardized nested REST route
  console.log(`API: Creating game for team ${teamId} using POST to /teams/${teamId}/games`);
  return wrappedPost(`/teams/${teamId}/games`, gameData);
};

export const updateGame = (gameId, gameData) => {
  return wrappedPut(`/games/${gameId}`, gameData);
};

export const deleteGame = (gameId) => {
  return wrappedDelete(`/games/${gameId}`);
};

// ADMIN API
export const getPendingUsers = () => {
  return wrappedGet('/admin/pending-users');
};

export const approveUser = (userId) => {
  return wrappedPost(`/admin/approve/${userId}`);
};

export const rejectUser = (userId) => {
  return wrappedPost(`/admin/reject/${userId}`);
};

export const getPendingCount = () => {
  return wrappedGet('/admin/pending-count');
};

// SYSTEM API
export const checkApiHealth = async () => {
  try {
    // Check the root API endpoint
    const response = await wrappedGet('/', { timeout: 5000 });
    return { 
      status: 'ok', 
      message: response.data?.message || 'API is available', 
      data: response.data 
    };
  } catch (error) {
    // Try alternative endpoints if the root fails
    try {
      // Try the teams endpoint which should be available if the user is logged in
      const teamsResponse = await wrappedGet('/teams', { timeout: 5000 });
      return {
        status: 'ok',
        message: 'API is available (teams endpoint)',
        data: { teams_available: true }
      };
    } catch (teamsError) {
      // If all attempts fail, return the original error
      return { 
        status: 'error', 
        message: error.message, 
        isNetworkError: !error.response
      };
    }
  }
};

// LINEUP API
export const getBattingOrder = (gameId) => {
  return wrappedGet(`/games/${gameId}/batting-order`);
};

export const updateBattingOrder = (gameId, orderData) => {
  return wrappedPut(`/games/${gameId}/batting-order`, orderData);
};

export const saveBattingOrder = (gameId, orderData) => {
  return wrappedPost(`/games/${gameId}/batting-order`, { order_data: orderData });
};

export const getFieldingRotations = (gameId) => {
  return wrappedGet(`/games/${gameId}/fielding-rotations`);
};

export const updateFieldingRotation = (gameId, inning, positionsData) => {
  return wrappedPut(`/games/${gameId}/fielding-rotations/${inning}`, positionsData);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  return wrappedPost(`/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

export const getPlayerAvailability = (gameId) => {
  return wrappedGet(`/games/${gameId}/player-availability`);
};

export const updatePlayerAvailability = (gameId, availabilityData) => {
  return wrappedPut(`/games/${gameId}/player-availability`, availabilityData);
};

export const batchSavePlayerAvailability = (gameId, playerAvailabilityArray) => {
  return wrappedPost(`/games/${gameId}/player-availability/batch`, playerAvailabilityArray);
};