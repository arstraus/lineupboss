import axios from 'axios';

// Configure axios with base settings
// Make sure we never have a double /api prefix
let apiBaseUrl = process.env.REACT_APP_API_URL || '';
// Strip any trailing slashes
apiBaseUrl = apiBaseUrl.replace(/\/+$/, '');

// Helper function to ensure consistent API URL formatting
export const getApiUrl = (path) => {
  // If path starts with a slash, remove it
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  
  // If the baseURL already has /api, don't add it again
  if (apiBaseUrl.includes('/api')) {
    return `${apiBaseUrl}/${cleanPath}`;
  }
  
  // Otherwise add /api prefix
  return `${apiBaseUrl}/api/${cleanPath}`;
};

// Remove any trailing slashes from baseURL
axios.defaults.baseURL = apiBaseUrl.replace(/\/+$/, '');
if (process.env.NODE_ENV === 'development') {
  console.log(`[API] Base URL: ${axios.defaults.baseURL || '(none)'}`);
}

// Add request interceptor to automatically add token to requests
axios.interceptors.request.use(
  config => {
    // IMPORTANT: Log full request details for auth-related issues
    console.log(`[API] Request: ${config.method?.toUpperCase()} ${config.url}`, { 
      headers: config.headers,
      hasToken: !!localStorage.getItem('token')
    });
    
    // Fix URL path to avoid /api/api prefix
    if (config.url && !config.url.startsWith('http')) {
      // For relative URLs, ensure correct formatting
      config.url = config.url.replace(/^\/+api\/*/, '');
      
      // Keep trailing slashes intact, but remove leading slash
      if (config.url.startsWith('/')) {
        config.url = config.url.substring(1);
      }
      
      // Make sure we have the correct prefix
      if (!axios.defaults.baseURL.includes('/api') && !config.url.startsWith('api/')) {
        config.url = `api/${config.url}`;
      }
      
      // Ensure trailing slash for POST endpoints (backend expects it)
      if ((config.method === 'post' || config.method === 'delete') && 
          !config.url.endsWith('/') && 
          !config.url.includes('?') &&
          !config.url.includes('refresh')) {
        config.url = `${config.url}/`;
      }
      
      // Log the final URL in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`[API] Final URL: ${config.method.toUpperCase()} ${axios.defaults.baseURL}/${config.url}`);
      }
    }
    
    const token = localStorage.getItem('token');
    if (token) {
      // Always set Authorization header for all requests
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`
      };
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`[API] Added token to ${config.method.toUpperCase()} ${config.url}`, token.substring(0, 10) + '...');
      }
    } else {
      console.warn(`[API] No authentication token available for ${config.method.toUpperCase()} ${config.url}`);
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
    // Don't duplicate the /api prefix that's already in baseURL
    const refreshUrl = '/auth/refresh';
    
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

// Export api object for named import
export const api = {
  get: axios.get,
  post: axios.post,
  put: axios.put,
  delete: axios.delete
};

// Export direct axios methods for convenience
export const get = axios.get;
export const post = axios.post;
export const put = axios.put;
export const del = axios.delete;

// Default export for backward compatibility
export default api;

// AUTH API
export const login = (email, password) => {
  // Use the auth endpoints without duplicating the /api prefix
  return axios.post('/auth/login', { email, password });
};

export const register = (email, password) => {
  // Use the auth endpoints without duplicating the /api prefix
  return axios.post('/auth/register', { email, password });
};

export const getCurrentUser = () => {
  // Use the auth endpoints without duplicating the /api prefix
  return axios.get('/auth/me');
};

export const refreshToken = () => {
  // Use the auth endpoints without duplicating the /api prefix
  return axios.post('/auth/refresh');
};

// USER PROFILE API
export const getUserProfile = () => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get('/user/profile');
};

export const updateUserProfile = (profileData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put('/user/profile', profileData);
};

export const updatePassword = (currentPassword, newPassword) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put('/user/password', {
    current_password: currentPassword,
    new_password: newPassword
  });
};

export const getUserSubscription = () => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get('/user/subscription');
};

// TEAMS API
export const getTeams = () => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get('/teams');
};

export const getTeam = (teamId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/teams/${teamId}`);
};

export const createTeam = (teamData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  // Ensure we include the trailing slash to match backend routing
  const token = localStorage.getItem('token');
  if (!token) {
    console.error('[API] Unable to create team - no authentication token available');
    return Promise.reject(new Error('Authentication required'));
  }
  
  // Always use trailing slash and explicit headers for reliability
  return axios({
    method: 'post',
    url: '/teams/',
    data: teamData,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });
};

export const updateTeam = (teamId, teamData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put(`/teams/${teamId}`, teamData);
};

export const deleteTeam = (teamId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  // Ensure we include proper auth headers and URL formatting
  const token = localStorage.getItem('token');
  return axios.delete(`/teams/${teamId}/`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
};

// PLAYERS API
export const getPlayers = (teamId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/teams/${teamId}/players`);
};

export const getPlayer = (playerId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/players/${playerId}`);
};

export const createPlayer = (teamId, playerData) => {
  // Use RESTful URL pattern
  return axios.post(`/teams/${teamId}/players`, playerData);
};

export const updatePlayer = (playerId, playerData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put(`/players/${playerId}`, playerData);
};

export const deletePlayer = (playerId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.delete(`/players/${playerId}`);
};

// GAMES API
export const getGames = (teamId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/teams/${teamId}/games`);
};

export const getGame = (gameId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/games/${gameId}`);
};

export const createGame = (teamId, gameData) => {
  // Use RESTful URL pattern
  return axios.post(`/teams/${teamId}/games`, gameData);
};

export const updateGame = (gameId, gameData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put(`/games/${gameId}`, gameData);
};

export const deleteGame = (gameId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.delete(`/games/${gameId}`);
};

// ADMIN API
export const getPendingUsers = () => {
  // Use RESTful URL pattern with query parameter
  return axios.get('/admin/users?status=pending');
};

export const approveUser = (userId) => {
  // Use RESTful URL pattern
  return axios.post(`/admin/users/${userId}/approve`);
};

export const rejectUser = (userId) => {
  // Use RESTful URL pattern
  return axios.post(`/admin/users/${userId}/reject`);
};

export const getPendingCount = () => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get('/admin/pending-count');
};

// SYSTEM API
export const checkApiHealth = async () => {
  try {
    // Use direct axios call to avoid duplicating the /api prefix from baseURL
    const response = await axios.get('/', { timeout: 5000 });
    return { 
      status: 'ok', 
      message: response.data?.message || 'API is available', 
      data: response.data 
    };
  } catch (error) {
    // Try alternative endpoints if the root fails
    try {
      // Try the teams endpoint which should be available if the user is logged in
      const teamsResponse = await axios.get('/teams', { timeout: 5000 });
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
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/games/${gameId}/batting-order`);
};

export const updateBattingOrder = (gameId, orderData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put(`/games/${gameId}/batting-order`, orderData);
};

export const saveBattingOrder = (gameId, orderData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.post(`/games/${gameId}/batting-order`, { order_data: orderData });
};

export const getFieldingRotations = (gameId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/games/${gameId}/fielding-rotations`);
};

export const updateFieldingRotation = (gameId, inning, positionsData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put(`/games/${gameId}/fielding-rotations/${inning}`, positionsData);
};

export const saveFieldingRotation = (gameId, inning, positions) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.post(`/games/${gameId}/fielding-rotations/${inning}`, { positions });
};

export const getPlayerAvailability = (gameId) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.get(`/games/${gameId}/player-availability`);
};

export const updatePlayerAvailability = (gameId, availabilityData) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.put(`/games/${gameId}/player-availability`, availabilityData);
};

export const batchSavePlayerAvailability = (gameId, playerAvailabilityArray) => {
  // Use direct axios call to avoid duplicating the /api prefix from baseURL
  return axios.post(`/games/${gameId}/player-availability/batch`, playerAvailabilityArray);
};

// ANALYTICS API
export const getBattingAnalytics = (teamId) => {
  // Use RESTful URL pattern to separate team and player analytics
  return axios.get(`/analytics/teams/${teamId}/players/batting`);
};

export const getFieldingAnalytics = (teamId) => {
  // Use RESTful URL pattern to separate team and player analytics
  return axios.get(`/analytics/teams/${teamId}/players/fielding`);
};

export const getTeamAnalytics = (teamId) => {
  // Use more concise RESTful URL pattern
  return axios.get(`/analytics/teams/${teamId}`);
};