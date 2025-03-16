import React, { createContext, useState, useEffect } from "react";
import axios from "axios";
import { login, register, getCurrentUser } from "../services/api";

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
        const response = await axios.get('/api/admin/pending-count', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`
          }
        });
        setCurrentUser(prev => ({
          ...prev,
          pendingCount: response.data.pending_count || 0
        }));
      } catch (err) {
        console.error("Error fetching pending count:", err);
      }
    }
  };

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      getCurrentUser()
        .then((response) => {
          const userData = response.data;
          setCurrentUser(userData);
          fetchPendingCount(userData);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error getting current user:", err);
          localStorage.removeItem("token");
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
    
    // Add event listener for browser close/refresh to automatically log out
    const handleBeforeUnload = () => {
      localStorage.removeItem("token");
    };
    
    window.addEventListener("beforeunload", handleBeforeUnload);
    
    // Clean up the event listener when component unmounts
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Login function - simplified and more reliable
  const handleLogin = async (email, password) => {
    try {
      // Clear any existing token first to prevent session conflicts
      localStorage.removeItem("token");
      
      // Step 1: Attempt to log in and get token
      const response = await login(email, password);
      
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

  const value = {
    currentUser,
    loading,
    error,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
