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
import AdminDashboard from "./pages/AdminDashboard";

// Components
import Header from "./components/Header";
import Footer from "./components/Footer";

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

// Admin Route component
const AdminRoute = ({ children }) => {
  const { currentUser, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
  }
  
  if (!currentUser) {
    return <Navigate to="/" />;
  }
  
  if (currentUser.role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
};

function App() {
  const { currentUser } = useContext(AuthContext);
  
  return (
    <div className="App d-flex flex-column min-vh-100">
      {/* Don't show header on landing page */}
      {window.location.pathname !== "/" || currentUser ? <Header /> : null}
      
      <div className="flex-grow-1">
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
                  <Dashboard />
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
          
          {/* Admin routes */}
          <Route 
            path="/admin" 
            element={
              <AdminRoute>
                <AdminDashboard />
              </AdminRoute>
            } 
          />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
      
      {/* Add Footer to all pages */}
      <Footer />
    </div>
  );
}

export default App;
