import React, { useState, useContext, useEffect } from 'react';
import { Form, Button, Card, Alert, Row, Col } from 'react-bootstrap';
import { AuthContext } from '../services/AuthContext';
import { getUserProfile, updateUserProfile, updatePassword, getUserSubscription } from '../services/api';

const AccountSettings = () => {
  const { currentUser, refreshUser } = useContext(AuthContext);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    location: '',
  });
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [subscription, setSubscription] = useState({});

  // Load user data when component mounts
  useEffect(() => {
    const loadUserData = async () => {
      try {
        // Get full user profile from API
        const profileResponse = await getUserProfile();
        const userData = profileResponse.data;
        
        setFormData({
          firstName: userData.first_name || '',
          lastName: userData.last_name || '',
          email: userData.email || '',
          location: userData.location || '',
        });
        
        // Get subscription details
        const subscriptionResponse = await getUserSubscription();
        setSubscription(subscriptionResponse.data);
      } catch (error) {
        console.error('Failed to load user data:', error);
        // Fallback to using context data
        if (currentUser) {
          setFormData({
            firstName: currentUser.first_name || '',
            lastName: currentUser.last_name || '',
            email: currentUser.email || '',
            location: currentUser.location || '',
          });
        }
      }
    };
    
    loadUserData();
  }, [currentUser]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };
  
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData({
      ...passwordData,
      [name]: value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMessage('');
    setErrorMessage('');

    try {
      const response = await updateUserProfile({
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        location: formData.location,
      });
      
      setSuccessMessage('Profile updated successfully!');
      
      // Refresh user data in the auth context
      if (refreshUser) {
        refreshUser();
      }
    } catch (error) {
      setErrorMessage(
        error.response?.data?.error || 
        'An error occurred while updating your profile. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };
  
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    // Validate passwords match
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    
    setLoadingPassword(true);
    setPasswordSuccess('');
    setPasswordError('');
    
    try {
      await updatePassword(passwordData.currentPassword, passwordData.newPassword);
      setPasswordSuccess('Password updated successfully!');
      
      // Clear password fields
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (error) {
      setPasswordError(
        error.response?.data?.error || 
        'An error occurred while updating your password. Please try again.'
      );
    } finally {
      setLoadingPassword(false);
    }
  };

  return (
    <div className="container py-4">
      <h1 className="mb-4">Account Settings</h1>
      
      {successMessage && (
        <Alert variant="success" onClose={() => setSuccessMessage('')} dismissible>
          {successMessage}
        </Alert>
      )}
      
      {errorMessage && (
        <Alert variant="danger" onClose={() => setErrorMessage('')} dismissible>
          {errorMessage}
        </Alert>
      )}
      
      <Row>
        <Col md={8}>
          <Card className="shadow-sm">
            <Card.Body>
              <h2 className="h4 mb-3">Personal Information</h2>
              <Form onSubmit={handleSubmit}>
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>First Name</Form.Label>
                      <Form.Control
                        type="text"
                        name="firstName"
                        value={formData.firstName}
                        onChange={handleInputChange}
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Last Name</Form.Label>
                      <Form.Control
                        type="text"
                        name="lastName"
                        value={formData.lastName}
                        onChange={handleInputChange}
                      />
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <Form.Label>Email</Form.Label>
                  <Form.Control
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Location</Form.Label>
                  <Form.Control
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    placeholder="City, State"
                  />
                </Form.Group>

                <div className="d-grid gap-2 mt-4">
                  <Button 
                    variant="primary" 
                    type="submit" 
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>

          <Card className="shadow-sm mt-4">
            <Card.Body>
              <h2 className="h4 mb-3">Change Password</h2>
              
              {passwordSuccess && (
                <Alert variant="success" onClose={() => setPasswordSuccess('')} dismissible>
                  {passwordSuccess}
                </Alert>
              )}
              
              {passwordError && (
                <Alert variant="danger" onClose={() => setPasswordError('')} dismissible>
                  {passwordError}
                </Alert>
              )}
              
              <Form onSubmit={handlePasswordSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Current Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="currentPassword"
                    value={passwordData.currentPassword}
                    onChange={handlePasswordChange}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>New Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="newPassword"
                    value={passwordData.newPassword}
                    onChange={handlePasswordChange}
                    required
                    minLength={8}
                  />
                  <Form.Text className="text-muted">
                    Password must be at least 8 characters long
                  </Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Confirm New Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="confirmPassword"
                    value={passwordData.confirmPassword}
                    onChange={handlePasswordChange}
                    required
                  />
                </Form.Group>

                <div className="d-grid gap-2 mt-4">
                  <Button 
                    variant="outline-primary" 
                    type="submit"
                    disabled={loadingPassword}
                  >
                    {loadingPassword ? 'Updating...' : 'Update Password'}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={4}>
          <Card className="shadow-sm">
            <Card.Body>
              <h2 className="h4 mb-3">Subscription Details</h2>
              <div className="d-flex align-items-center mb-3">
                <span className="badge bg-info me-2">
                  {currentUser?.subscription_tier ? currentUser.subscription_tier.charAt(0).toUpperCase() + currentUser.subscription_tier.slice(1) : 'Rookie'}
                </span>
                <span>Current Plan</span>
              </div>
              <p className="text-muted small">
                You are currently on the Rookie plan. Manage your subscription in the Billing section.
              </p>
              <div className="d-grid gap-2 mt-4">
                <Button as="a" href="/billing" variant="outline-secondary">
                  <i className="bi bi-credit-card me-2"></i>
                  Manage Billing
                </Button>
              </div>
            </Card.Body>
          </Card>

          <Card className="shadow-sm mt-4">
            <Card.Body>
              <h2 className="h4 mb-3">Account</h2>
              <p className="text-muted small">
                Member since: {new Date(currentUser?.created_at || Date.now()).toLocaleDateString()}
              </p>
              <div className="d-grid gap-2 mt-4">
                <Button variant="outline-danger">
                  Delete Account
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AccountSettings;