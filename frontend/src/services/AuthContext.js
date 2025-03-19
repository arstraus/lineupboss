import React, { createContext, useState, useEffect } from "react";
import { login, register, getCurrentUser, refreshToken, getPendingCount } from "../services/api";

// Create Auth Context
export const AuthContext = createContext();

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch pending user count for admin users
  const fetchPendingCount = async (userData) => {
    if (userData && userData.role === 'admin') {
      try {
        // Use API client function instead of direct axios call
        const response = await getPendingCount();
        setCurrentUser(prev => ({
          ...prev,
          pendingCount: response.data.pending_count || 0
        }));
      } catch (err) {
        console.error("Error fetching pending count:", err);
      }
    }
  };

  // Check if user is already logged in and handle token management
  useEffect(() => {
    let tokenCheckInterval = null;
    
    const checkAndLoadUser = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const response = await getCurrentUser();
          const userData = response.data;
          setCurrentUser(userData);
          fetchPendingCount(userData);
          
          // Check if token needs refresh (from token_expires_soon flag)
          if (userData.token_expires_soon) {
            console.log("Token expiring soon, refreshing...");
            await handleTokenRefresh();
          }
          
          setLoading(false);
        } catch (err) {
          console.error("Error getting current user:", err);
          localStorage.removeItem("token");
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };
    
    // Initial check
    checkAndLoadUser();
    
    // Set up interval to check token every 15 minutes (900000 ms)
    // This is a background safety mechanism in addition to the API-driven refresh
    tokenCheckInterval = setInterval(() => {
      const token = localStorage.getItem("token");
      if (token && currentUser) {
        // Only do the token check if user is logged in
        getCurrentUser()
          .then(response => {
            if (response.data.token_expires_soon) {
              console.log("Token check interval - refreshing expiring token");
              handleTokenRefresh();
            }
          })
          .catch(err => {
            console.error("Error during token check interval:", err);
            // If the token check fails with 401, clear the token
            if (err.response && err.response.status === 401) {
              localStorage.removeItem("token");
              setCurrentUser(null);
            }
          });
      }
    }, 900000); // 15 minute interval
    
    // Add event listener for browser close/refresh to automatically log out
    // This is a conservative security measure - consider removing if users
    // find it frustrating to log in frequently
    const handleBeforeUnload = () => {
      // Uncomment to enable automatic logout on page refresh/close
      // localStorage.removeItem("token");
    };
    
    window.addEventListener("beforeunload", handleBeforeUnload);
    
    // Clean up the event listener and interval when component unmounts
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      if (tokenCheckInterval) {
        clearInterval(tokenCheckInterval);
      }
    };
  }, []);

  // Login function - simplified and more reliable with error detection
  const handleLogin = async (email, password) => {
    try {
      // Clear any existing token first to prevent session conflicts
      localStorage.removeItem("token");
      
      // Step 1: Attempt to log in and get token
      let response;
      try {
        response = await login(email, password);
      } catch (loginErr) {
        // We shouldn't need special recovery now that all paths are standardized,
        // but keeping a simpler version for robustness
        if (loginErr.response && loginErr.response.status === 405) {
          console.error("LOGIN ERROR: Possible incorrect API path. Check API service configuration.");
          
          // Log more details in development
          if (process.env.NODE_ENV === 'development') {
            console.error("Login request failed with details:", {
              url: loginErr.response.config?.url,
              status: loginErr.response.status,
              data: loginErr.response.data
            });
          }
        }
        throw loginErr;
      }
      
      // Step 2: Validate token
      const token = response.data.access_token;
      if (!token) {
        setError("Authentication failed: No token received");
        throw new Error("Authentication failed: No token received");
      }
      
      // Step 3: Store token in localStorage (our single source of truth)
      localStorage.setItem("token", token);
      
      // Step 4: Try to get current user data with the token
      try {
        const userResponse = await getCurrentUser();
        setCurrentUser(userResponse.data);
        setError(null);
      } catch (userErr) {
        // If we can't get user details, create minimal user object
        // This allows login to succeed even if /me endpoint fails
        console.warn("Couldn't get full user details, using minimal user object");
        setCurrentUser({ 
          id: response.data.user_id, 
          email: email,
          role: response.data.role || 'user',
          status: response.data.status || 'approved'
        });
      }
      
      return response;
    } catch (err) {
      // Clear any potentially saved token on login failure
      localStorage.removeItem("token");
      
      // Set appropriate error message
      const errorMessage = err.response?.data?.error || "Login failed";
      setError(errorMessage);
      
      // Add detailed logging in development mode
      if (process.env.NODE_ENV === 'development') {
        console.error("Login failure details:", {
          status: err.response?.status,
          statusText: err.response?.statusText,
          url: err.response?.config?.url,
          data: err.response?.data,
          message: err.message
        });
      }
      
      // Re-throw the original error to preserve response data
      throw err;
    }
  };

  // Register function - simplified and aligned with login
  const handleRegister = async (email, password) => {
    try {
      // Step 1: Attempt to register and get token
      const response = await register(email, password);
      
      // Step 2: Check if token was received (it won't be if user needs approval)
      const token = response.data.access_token;
      
      // If user is pending and no token, handle as a special case
      if (!token && response.data.status === 'pending') {
        setError(null);
        setCurrentUser(null);
        return response; // Return response so component can handle the pending message
      }
      
      if (!token) {
        setError("Registration failed: No token received");
        throw new Error("Registration failed: No token received");
      }
      
      // Step 3: Store token in localStorage (our single source of truth)
      localStorage.setItem("token", token);
      
      // Step 4: Try to get current user data with the token
      try {
        const userResponse = await getCurrentUser();
        setCurrentUser(userResponse.data);
        setError(null);
      } catch (userErr) {
        // If we can't get user details, create minimal user object
        console.warn("Couldn't get full user details after registration, using minimal user object");
        setCurrentUser({ 
          id: response.data.user_id, 
          email: email,
          role: response.data.role || 'user',
          status: response.data.status || 'pending'
        });
      }
      
      return response;
    } catch (err) {
      // Clear any potentially saved token on registration failure
      localStorage.removeItem("token");
      
      // Set appropriate error message
      const errorMessage = err.response?.data?.error || "Registration failed";
      setError(errorMessage);
      
      // Re-throw the original error to preserve response data
      throw err;
    }
  };

  // Logout function
  const handleLogout = () => {
    localStorage.removeItem("token");
    setCurrentUser(null);
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      const response = await getCurrentUser();
      setCurrentUser(response.data);
      fetchPendingCount(response.data);
      
      // Check if token needs refresh
      if (response.data.token_expires_soon) {
        await handleTokenRefresh();
      }
    } catch (err) {
      console.error("Error refreshing user data:", err);
    }
  };
  
  // Handle token refresh
  const handleTokenRefresh = async () => {
    try {
      const response = await refreshToken();
      
      // Update token in localStorage if refresh succeeded
      if (response.data && response.data.access_token) {
        localStorage.setItem("token", response.data.access_token);
        return true;
      }
      return false;
    } catch (err) {
      console.error("Error refreshing token:", err);
      
      // If refresh fails with 401, token is invalid - log out
      if (err.response && err.response.status === 401) {
        handleLogout();
      }
      return false;
    }
  };

  const value = {
    currentUser,
    loading,
    error,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshUser,
    refreshToken: handleTokenRefresh
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
