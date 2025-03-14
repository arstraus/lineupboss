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

  // Login function
  const handleLogin = async (email, password) => {
    try {
      const response = await login(email, password);
      
      // Store the token and log it for debugging
      const token = response.data.access_token;
      console.log("Login successful, token received:", token ? "Yes" : "No");
      
      if (!token) {
        console.error("No token received from server");
        throw new Error("Authentication failed: No token received");
      }
      
      // Clear any existing token first
      localStorage.removeItem("token");
      // Then store the new token
      localStorage.setItem("token", token);
      
      // Set the token in axios headers immediately
      const authHeader = `Bearer ${token}`;
      axios.defaults.headers.common["Authorization"] = authHeader;
      
      // Wait a moment for storage and header setting to complete
      await new Promise(resolve => setTimeout(resolve, 300));
      
      try {
        // Log headers before making the request
        console.log("Making getCurrentUser request with token");
        
        const userResponse = await getCurrentUser();
        console.log("User data received:", userResponse.data);
        setCurrentUser(userResponse.data);
        setError(null);
      } catch (userErr) {
        console.error("Error getting user after login:", userErr);
        console.error("Response:", userErr.response);
        
        // Even if getting the user fails, consider login successful with minimal data
        setCurrentUser({ id: response.data.user_id, email });
      }
      
      return response;
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.error || "Login failed");
      throw err;
    }
  };

  // Register function
  const handleRegister = async (email, password) => {
    try {
      const response = await register(email, password);
      // Store the token and log it for debugging
      console.log("Registration successful, token:", response.data.access_token);
      localStorage.setItem("token", response.data.access_token);
      
      // Small delay to ensure token is stored before making the next request
      await new Promise(resolve => setTimeout(resolve, 100));
      
      try {
        const userResponse = await getCurrentUser();
        setCurrentUser(userResponse.data);
        setError(null);
      } catch (userErr) {
        console.error("Error getting user after registration:", userErr);
        // Even if getting the user fails, consider registration successful
        setCurrentUser({ id: response.data.user_id, email });
      }
      
      return response;
    } catch (err) {
      console.error("Registration error:", err);
      setError(err.response?.data?.error || "Registration failed");
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
