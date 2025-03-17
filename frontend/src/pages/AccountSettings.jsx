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
    city: '',
    state: '',
    country: 'USA',
    zipCode: '',
  });
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [loadingSubscription, setLoadingSubscription] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [subscriptionError, setSubscriptionError] = useState('');
  const [subscription, setSubscription] = useState({ tier: 'rookie' });

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
          city: userData.city || '',
          state: userData.state || '',
          country: userData.country || 'USA',
          zipCode: userData.zip_code || '',
        });
        
        // Get subscription details
        setLoadingSubscription(true);
        setSubscriptionError('');
        try {
          console.log('Fetching subscription details');
          const subscriptionResponse = await getUserSubscription();
          console.log('Subscription response:', subscriptionResponse);
          setSubscription(subscriptionResponse.data);
        } catch (subscriptionError) {
          console.error('Failed to load subscription data:', subscriptionError);
          setSubscriptionError('Failed to load subscription information. Please try again later.');
          // Set default subscription
          setSubscription({ tier: currentUser?.subscription_tier || 'rookie' });
        } finally {
          setLoadingSubscription(false);
        }
      } catch (error) {
        console.error('Failed to load user data:', error);
        // Fallback to using context data
        if (currentUser) {
          setFormData({
            firstName: currentUser.first_name || '',
            lastName: currentUser.last_name || '',
            email: currentUser.email || '',
            city: currentUser.city || '',
            state: currentUser.state || '',
            country: currentUser.country || 'USA',
            zipCode: currentUser.zip_code || '',
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

    console.log('Submitting profile update with data:', {
      first_name: formData.firstName,
      last_name: formData.lastName,
      email: formData.email,
      city: formData.city,
      state: formData.state,
      country: formData.country,
      zip_code: formData.zipCode,
    });

    try {
      const response = await updateUserProfile({
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        city: formData.city,
        state: formData.state,
        country: formData.country,
        zip_code: formData.zipCode,
      });
      
      console.log('Profile update response:', response);
      setSuccessMessage('Profile updated successfully!');
      
      // Refresh user data in the auth context
      if (refreshUser) {
        console.log('Refreshing user data');
        refreshUser();
      }
    } catch (error) {
      console.error('Profile update error:', error);
      
      // Detailed error logging
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
        console.error('Error response headers:', error.response.headers);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('Error request:', error.request);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error message:', error.message);
      }
      
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

                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>City</Form.Label>
                      <Form.Control
                        type="text"
                        name="city"
                        value={formData.city}
                        onChange={handleInputChange}
                        placeholder="City"
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>State</Form.Label>
                      <Form.Control
                        type="text"
                        name="state"
                        value={formData.state}
                        onChange={handleInputChange}
                        placeholder="State"
                      />
                    </Form.Group>
                  </Col>
                </Row>

                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Country</Form.Label>
                      <Form.Control
                        type="text"
                        name="country"
                        value={formData.country}
                        onChange={handleInputChange}
                        placeholder="Country"
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Zip Code</Form.Label>
                      <Form.Control
                        type="text"
                        name="zipCode"
                        value={formData.zipCode}
                        onChange={handleInputChange}
                        placeholder="Zip Code"
                      />
                    </Form.Group>
                  </Col>
                </Row>

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
              
              {subscriptionError && (
                <Alert variant="warning" onClose={() => setSubscriptionError('')} dismissible>
                  {subscriptionError}
                </Alert>
              )}
              
              {loadingSubscription ? (
                <div className="text-center py-3">
                  <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className="mt-2">Loading subscription details...</p>
                </div>
              ) : (
                <>
                  <div className="d-flex align-items-center mb-3">
                    <span className="badge bg-info me-2">
                      {subscription?.tier ? subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1) : 
                       currentUser?.subscription_tier ? currentUser.subscription_tier.charAt(0).toUpperCase() + currentUser.subscription_tier.slice(1) : 
                       'Rookie'}
                    </span>
                    <span>Current Plan</span>
                  </div>
                  <p className="text-muted small">
                    You are currently on the {subscription?.tier?.charAt(0).toUpperCase() + subscription?.tier?.slice(1) || 'Rookie'} plan. 
                    Manage your subscription in the Billing section.
                  </p>
                  <div className="d-grid gap-2 mt-4">
                    <Button as="a" href="/billing" variant="outline-secondary">
                      <i className="bi bi-credit-card me-2"></i>
                      Manage Billing
                    </Button>
                  </div>
                </>
              )}
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