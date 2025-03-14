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

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      getCurrentUser()
        .then((response) => {
          setCurrentUser(response.data);
          setLoading(false);
        })
        .catch((err) => {
          localStorage.removeItem("token");
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // Login function - simplified and more reliable
  const handleLogin = async (email, password) => {
    try {
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
          email: email 
        });
      }
      
      return response;
    } catch (err) {
      // Clear any potentially saved token on login failure
      localStorage.removeItem("token");
      
      // Set appropriate error message
      const errorMessage = err.response?.data?.error || "Login failed";
      setError(errorMessage);
      
      // Re-throw for component handling
      throw new Error(errorMessage);
    }
  };

  // Register function - simplified and aligned with login
  const handleRegister = async (email, password) => {
    try {
      // Step 1: Attempt to register and get token
      const response = await register(email, password);
      
      // Step 2: Validate token
      const token = response.data.access_token;
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
          email: email 
        });
      }
      
      return response;
    } catch (err) {
      // Clear any potentially saved token on registration failure
      localStorage.removeItem("token");
      
      // Set appropriate error message
      const errorMessage = err.response?.data?.error || "Registration failed";
      setError(errorMessage);
      
      // Re-throw for component handling
      throw new Error(errorMessage);
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
