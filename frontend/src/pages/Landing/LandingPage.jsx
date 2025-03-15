import React from "react";
import { Link } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../../services/AuthContext";
import "./LandingPage.css";

const LandingPage = () => {
  const { currentUser } = useContext(AuthContext);

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="text-white">Welcome to LineupBoss</h1>
          <p className="text-white mb-3">The ultimate baseball lineup management application</p>
          <div className="hero-buttons">
            {currentUser ? (
              <Link to="/dashboard" className="btn btn-primary btn-lg me-3">
                Go to My Teams
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn btn-primary btn-lg me-3">
                  Login
                </Link>
                <Link to="/register" className="btn btn-outline-light btn-lg">
                  Sign Up Free
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section py-4">
        <div className="container">
          <h2 className="text-center mb-4">Baseball Lineup Management Made Easy</h2>
          <div className="row text-center">
            <div className="col-md-4 mb-4">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="bi bi-people-fill"></i>
                </div>
                <h3>Team Management</h3>
                <p>Create and manage multiple teams with detailed rosters</p>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="bi bi-calendar-check"></i>
                </div>
                <h3>Game Scheduling</h3>
                <p>Organize your season schedule and track game details</p>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="bi bi-list-ol"></i>
                </div>
                <h3>Fair Rotations</h3>
                <p>Create balanced batting orders and field rotations</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="how-it-works-section py-5 bg-light">
        <div className="container">
          <h2 className="text-center mb-5">How LineupBoss Works</h2>
          <div className="row">
            <div className="col-md-3 text-center mb-4">
              <div className="step-circle">1</div>
              <h4>Create Your Team</h4>
              <p>Add your team with players and jersey numbers</p>
            </div>
            <div className="col-md-3 text-center mb-4">
              <div className="step-circle">2</div>
              <h4>Schedule Games</h4>
              <p>Set up your season schedule with dates and times</p>
            </div>
            <div className="col-md-3 text-center mb-4">
              <div className="step-circle">3</div>
              <h4>Manage Lineups</h4>
              <p>Create fair batting orders and field rotations</p>
            </div>
            <div className="col-md-3 text-center mb-4">
              <div className="step-circle">4</div>
              <h4>Game Day</h4>
              <p>Print lineup sheets or access from your phone</p>
            </div>
          </div>
          <div className="text-center mt-4">
            <Link to="/register" className="btn btn-primary btn-lg">
              Get Started Today
            </Link>
          </div>
        </div>
      </div>

      {/* Testimonials Section */}
      <div className="testimonials-section py-5">
        <div className="container">
          <h2 className="text-center mb-5">What Coaches Are Saying</h2>
          <div className="row">
            <div className="col-md-4 mb-4">
              <div className="testimonial-card">
                <div className="testimonial-content">
                  <p>"LineupBoss has saved me hours of work every week. No more juggling spreadsheets and paper lineups!"</p>
                </div>
                <div className="testimonial-author">
                  <p className="mb-0"><strong>Mike Johnson</strong></p>
                  <p className="text-muted">Little League Coach</p>
                </div>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="testimonial-card">
                <div className="testimonial-content">
                  <p>"Parents love that all players get fair playing time. The app makes it easy to track and balance positions."</p>
                </div>
                <div className="testimonial-author">
                  <p className="mb-0"><strong>Sarah Williams</strong></p>
                  <p className="text-muted">Travel Team Coach</p>
                </div>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="testimonial-card">
                <div className="testimonial-content">
                  <p>"The field rotation feature alone is worth it. My assistant coaches can help create lineups together."</p>
                </div>
                <div className="testimonial-author">
                  <p className="mb-0"><strong>David Martinez</strong></p>
                  <p className="text-muted">Youth Baseball Coach</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="cta-section py-5">
        <div className="container text-center">
          <h2 className="text-white mb-4">Ready to Simplify Your Lineup Management?</h2>
          <p className="text-white mb-4">Join thousands of coaches who trust LineupBoss for their team management</p>
          <Link to="/register" className="btn btn-light btn-lg">
            Sign Up For Free
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;