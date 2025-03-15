import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "./services/AuthContext";

// Pages
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import TeamDetail from "./pages/TeamDetail";
import GameDetail from "./pages/GameDetail";
import NotFound from "./pages/NotFound";
import LandingPage from "./pages/Landing/LandingPage";

// Components
import Header from "./components/Header";

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { currentUser, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
  }
  
  if (!currentUser) {
    return <Navigate to="/" />;
  }
  
  return children;
};

function App() {
  const { currentUser } = useContext(AuthContext);
  
  return (
    <div className="App">
      {/* Don't show header on landing page */}
      {window.location.pathname !== "/" || currentUser ? <Header /> : null}
      
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <div className="container mt-4">
                <Dashboard />
              </div>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/teams/:teamId" 
          element={
            <ProtectedRoute>
              <div className="container mt-4">
                <TeamDetail />
              </div>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/games/:gameId" 
          element={
            <ProtectedRoute>
              <div className="container mt-4">
                <GameDetail />
              </div>
            </ProtectedRoute>
          } 
        />
        
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}

export default App;
