import React, { useContext, useState, useEffect } from 'react';
import { Card, Button, Row, Col, Badge, Table, Alert } from 'react-bootstrap';
import { AuthContext } from '../services/AuthContext';
import { getUserSubscription } from '../services/api';

const Billing = () => {
  const { currentUser } = useContext(AuthContext);
  const [subscriptionData, setSubscriptionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Load subscription data
  useEffect(() => {
    const loadSubscriptionData = async () => {
      try {
        const response = await getUserSubscription();
        setSubscriptionData(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error loading subscription data:', err);
        setError('Failed to load subscription information. Please try again later.');
        setLoading(false);
      }
    };
    
    loadSubscriptionData();
  }, []);
  
  // Get current tier from API data or fallback to user context
  const currentTier = 
    subscriptionData?.tier ? 
    subscriptionData.tier.charAt(0).toUpperCase() + 
    subscriptionData.tier.slice(1) : 
    currentUser?.subscription_tier ? 
    currentUser.subscription_tier.charAt(0).toUpperCase() + 
    currentUser.subscription_tier.slice(1) : 
    'Rookie';

  return (
    <div className="container py-4">
      <h1 className="mb-4">Billing & Subscription</h1>
      
      {error && (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      )}
      
      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading subscription information...</p>
        </div>
      ) : (
      
      <Row>
        <Col md={8} className="mb-4">
          <Card className="shadow-sm">
            <Card.Body>
              <h2 className="h4 mb-3">Current Plan</h2>
              <div className="d-flex align-items-center mb-3">
                <Badge bg="info" className="me-2">{currentTier}</Badge>
                <span className="fw-bold">LineupBoss {currentTier}</span>
              </div>
              
              {currentTier === 'Rookie' ? (
                <div className="mb-4">
                  <p>You're currently on our free tier.</p>
                  <div className="d-grid gap-2 mt-4">
                    <Button variant="primary" disabled>
                      Upgrade to Pro (Coming Soon)
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="mb-4">
                  <p>You're subscribed to LineupBoss Pro.</p>
                  <div className="d-grid gap-2 mt-4">
                    <Button variant="outline-danger">
                      Cancel Subscription
                    </Button>
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
          
          <Card className="shadow-sm mt-4">
            <Card.Body>
              <h2 className="h4 mb-3">Payment Methods</h2>
              <p className="text-muted">No payment methods currently on file.</p>
              <Button variant="outline-primary" disabled>
                <i className="bi bi-plus"></i> Add Payment Method
              </Button>
            </Card.Body>
          </Card>
          
          <Card className="shadow-sm mt-4">
            <Card.Body>
              <h2 className="h4 mb-3">Billing History</h2>
              <p className="text-muted">You haven't been charged yet.</p>
              <Table responsive className="mt-3">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan="4" className="text-center">No billing history available</td>
                  </tr>
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={4}>
          <Card className="shadow-sm">
            <Card.Header className="bg-primary text-white">
              <h3 className="h5 mb-0">Plan Comparison</h3>
            </Card.Header>
            <Card.Body>
              <div className="mb-4">
                <h4 className="h6">Rookie (Free)</h4>
                <ul className="list-unstyled">
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Create up to 2 teams</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Roster management</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Batting order management</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Basic fielding rotations</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Gameday lineup summaries and export</li>
                  <li><i className="bi bi-x-circle-fill text-muted me-2"></i> AI-powered features</li>
                  <li><i className="bi bi-x-circle-fill text-muted me-2"></i> Analytics dashboard</li>
                </ul>
              </div>
              
              <div className="mb-3">
                <h4 className="h6">Pro (Coming Soon)</h4>
                <ul className="list-unstyled">
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Unlimited teams</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Multiple coach access</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> AI generated fielding rotations</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> Player and Team analytics</li>
                  <li><i className="bi bi-check-circle-fill text-success me-2"></i> All Rookie features included</li>
                </ul>
              </div>
              
              <div className="d-grid">
                <Button variant="primary" disabled>
                  Upgrade to Pro (Coming Soon)
                </Button>
              </div>
            </Card.Body>
          </Card>
          
          <Card className="shadow-sm mt-4">
            <Card.Body>
              <h4 className="h5 mb-3">Need Help?</h4>
              <p className="text-muted">
                Have questions about billing or your subscription? Contact our support team.
              </p>
              <Button variant="outline-secondary" size="sm">
                <i className="bi bi-question-circle me-2"></i>
                Contact Support
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      )}
    </div>
  );
};

export default Billing;