import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../services/AuthContext";
import { Dropdown } from "react-bootstrap";
import { PersonCircle } from "react-bootstrap-icons";

const Header = () => {
  const { currentUser, logout } = useContext(AuthContext);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Function to format user name
  const getUserDisplayName = () => {
    if (currentUser.first_name && currentUser.last_name) {
      return `${currentUser.first_name} ${currentUser.last_name}`;
    } else if (currentUser.first_name) {
      return currentUser.first_name;
    } else {
      return currentUser.email.split('@')[0];
    }
  };

  // Get subscription tier display name
  const getSubscriptionTier = () => {
    return currentUser.subscription_tier ? 
      currentUser.subscription_tier.charAt(0).toUpperCase() + 
      currentUser.subscription_tier.slice(1) : 
      'Rookie';
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container">
        <Link className="navbar-brand" to={currentUser ? "/dashboard" : "/"}>
          LineupBoss
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            {currentUser && (
              <>
                <li className="nav-item">
                  <Link className="nav-link" to="/dashboard">
                    Dashboard
                  </Link>
                </li>
                {currentUser.role === 'admin' && (
                  <li className="nav-item">
                    <Link className="nav-link" to="/admin">
                      <i className="bi bi-shield-lock me-1"></i>
                      Admin
                      {currentUser.pendingCount > 0 && (
                        <span className="badge rounded-pill bg-danger ms-2">{currentUser.pendingCount}</span>
                      )}
                    </Link>
                  </li>
                )}
              </>
            )}
          </ul>
          <ul className="navbar-nav">
            {currentUser ? (
              <Dropdown>
                <Dropdown.Toggle 
                  variant="link" 
                  id="user-dropdown"
                  className="nav-link text-white d-flex align-items-center"
                  style={{ textDecoration: 'none' }}
                >
                  <PersonCircle size={24} className="me-2" />
                </Dropdown.Toggle>

                <Dropdown.Menu align="end" className="mt-2 shadow-sm">
                  <div className="px-3 py-2 border-bottom">
                    <div className="fw-bold">{getUserDisplayName()}</div>
                    <div className="small text-muted">{currentUser.email}</div>
                    <div className="small mt-1">
                      <span className="badge bg-info">{getSubscriptionTier()}</span>
                    </div>
                  </div>
                  <Dropdown.Item as={Link} to="/account">
                    <i className="bi bi-person me-2"></i>
                    Account Settings
                  </Dropdown.Item>
                  <Dropdown.Item as={Link} to="/billing">
                    <i className="bi bi-credit-card me-2"></i>
                    Billing
                  </Dropdown.Item>
                  <Dropdown.Divider />
                  <Dropdown.Item onClick={logout}>
                    <i className="bi bi-box-arrow-right me-2"></i>
                    Logout
                  </Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            ) : (
              <>
                <li className="nav-item">
                  <Link className="nav-link" to="/login">
                    Login
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" to="/register">
                    Register
                  </Link>
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Header;
