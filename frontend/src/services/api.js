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
    // Use explicit standard route without risking emergency prefix
    const refreshUrl = '/api/auth/refresh';
    
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
  // Explicitly use standard route without any risk of emergency prefix
  return wrappedPost('/api/auth/login', { email, password });
};

export const register = (email, password) => {
  // Explicitly use standard route without any risk of emergency prefix
  return wrappedPost('/api/auth/register', { email, password });
};

export const getCurrentUser = () => {
  // Explicitly use standard route without any risk of emergency prefix
  return wrappedGet('/api/auth/me');
};

export const refreshToken = () => {
  // Explicitly use standard route without any risk of emergency prefix
  return wrappedPost('/api/auth/refresh');
};

// USER PROFILE API
export const getUserProfile = () => {
  // Explicitly use standard route
  return wrappedGet('/api/user/profile');
};

export const updateUserProfile = (profileData) => {
  // Explicitly use standard route
  return wrappedPut('/api/user/profile', profileData);
};

export const updatePassword = (currentPassword, newPassword) => {
  // Explicitly use standard route
  return wrappedPut('/api/user/password', {
    current_password: currentPassword,
    new_password: newPassword
  });
};

export const getUserSubscription = () => {
  // Explicitly use standard route
  return wrappedGet('/api/user/subscription');
};

// TEAMS API
export const getTeams = () => {
  // Explicitly use standard route
  return wrappedGet('/api/teams');
};

export const getTeam = (teamId) => {
  // Explicitly use standard route
  return wrappedGet(`/api/teams/${teamId}`);
};

export const createTeam = (teamData) => {
  // Explicitly use standard route
  return wrappedPost('/api/teams', teamData);
};

export const updateTeam = (teamId, teamData) => {
  // Explicitly use standard route
  return wrappedPut(`/api/teams/${teamId}`, teamData);
};

export const deleteTeam = (teamId) => {
  // Explicitly use standard route
  return wrappedDelete(`/api/teams/${teamId}`);
};

// PLAYERS API
export const getPlayers = (teamId) => {
  // Explicitly use standard RESTful route
  return wrappedGet(`/api/teams/${teamId}/players`);
};

export const getPlayer = (playerId) => {
  // Explicitly use standard route
  return wrappedGet(`/api/players/${playerId}`);
};

export const createPlayer = (teamId, playerData) => {
  // Explicitly use standard RESTful route
  return wrappedPost(`/api/teams/${teamId}/players`, playerData);
};

export const updatePlayer = (playerId, playerData) => {
  // Explicitly use standard route
  return wrappedPut(`/api/players/${playerId}`, playerData);
};

export const deletePlayer = (playerId) => {
  // Explicitly use standard route
  return wrappedDelete(`/api/players/${playerId}`);
};

// GAMES API
export const getGames = (teamId) => {
  // Explicitly use standard RESTful route
  return wrappedGet(`/api/teams/${teamId}/games`);
};

export const getGame = (gameId) => {
  // Explicitly use standard route
  return wrappedGet(`/api/games/${gameId}`);
};

export const createGame = (teamId, gameData) => {
  // Explicitly use standard RESTful route
  return wrappedPost(`/api/teams/${teamId}/games`, gameData);
};

export const updateGame = (gameId, gameData) => {
  // Explicitly use standard route
  return wrappedPut(`/api/games/${gameId}`, gameData);
};

export const deleteGame = (gameId) => {
  // Explicitly use standard route
  return wrappedDelete(`/api/games/${gameId}`);
};

// ADMIN API
export const getPendingUsers = () => {
  // Explicitly use standard route
  return wrappedGet('/api/admin/pending-users');
};

export const approveUser = (userId) => {
  // Explicitly use standard route
  return wrappedPost(`/api/admin/approve/${userId}`);
};

export const rejectUser = (userId) => {
  // Explicitly use standard route
  return wrappedPost(`/api/admin/reject/${userId}`);
};

export const getPendingCount = () => {
  // Explicitly use standard route
  return wrappedGet('/api/admin/pending-count');
};

// SYSTEM API
export const checkApiHealth = async () => {
  try {
    // Check the root API endpoint with explicit path
    const response = await wrappedGet('/api', { timeout: 5000 });
    return { 
      status: 'ok', 
      message: response.data?.message || 'API is available', 
      data: response.data 
    };
  } catch (error) {
    // Try alternative endpoints if the root fails
    try {
      // Try the teams endpoint which should be available if the user is logged in
      const teamsResponse = await wrappedGet('/api/teams', { timeout: 5000 });
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
  // Explicitly use standard route
  return wrappedGet(`/api/games/${gameId}/batting-order`);
};

export const updateBattingOrder = (gameId, orderData) => {
  // Explicitly use standard route
  return wrappedPut(`/api/games/${gameId}/batting-order`, orderData);
};

export const saveBattingOrder = (gameId, orderData) => {
  // Explicitly use standard route
  return wrappedPost(`/api/games/${gameId}/batting-order`, { order_data: orderData });
};

export const getFieldingRotations = (gameId) => {
  // Explicitly use standard route
  return wrappedGet(`/api/games/${gameId}/fielding-rotations`);
};

export const updateFieldingRotation = (gameId, inning, positionsData) => {
  // Explicitly use standard route
  return wrappedPut(`/api/games/${gameId}/fielding-rotations/${inning}`, positionsData);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  // Explicitly use standard route
  return wrappedPost(`/api/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

export const getPlayerAvailability = (gameId) => {
  // Explicitly use standard route
  return wrappedGet(`/api/games/${gameId}/player-availability`);
};

export const updatePlayerAvailability = (gameId, availabilityData) => {
  // Explicitly use standard route
  return wrappedPut(`/api/games/${gameId}/player-availability`, availabilityData);
};

export const batchSavePlayerAvailability = (gameId, playerAvailabilityArray) => {
  // Explicitly use standard route
  return wrappedPost(`/api/games/${gameId}/player-availability/batch`, playerAvailabilityArray);
};