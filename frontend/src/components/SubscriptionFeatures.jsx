import React from 'react';
import { Container, Row, Col, Card, Table, Button } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';

const SubscriptionFeatures = () => {
  const { currentUser } = useAuth();
  const currentTier = currentUser?.subscription_tier || 'rookie';

  // Feature definitions aligned with backend
  const features = [
    {
      id: 'max_teams',
      name: 'Team Management',
      rookie: '2 teams',
      pro: 'Unlimited teams',
      description: 'Number of teams you can manage in your account'
    },
    {
      id: 'ai_lineup_generation',
      name: 'AI Lineup Generation',
      rookie: '❌',
      pro: '✅',
      description: 'AI-powered fielding rotation generator that builds optimized lineups'
    },
    {
      id: 'advanced_analytics',
      name: 'Advanced Analytics',
      rookie: '❌',
      pro: '✅',
      description: 'Detailed player and team performance metrics and trends'
    },
    {
      id: 'csv_import_export',
      name: 'CSV Import/Export',
      rookie: '✅',
      pro: '✅',
      description: 'Import and export player data using CSV files'
    },
    {
      id: 'batch_availability_management',
      name: 'Batch Availability Management',
      rookie: '✅',
      pro: '✅',
      description: 'Update multiple players' availability at once'
    },
    {
      id: 'export_pdfs',
      name: 'Export Lineup Cards',
      rookie: '✅',
      pro: '✅',
      description: 'Download and print lineup cards and game plans as PDFs'
    }
  ];

  const plans = [
    {
      id: 'rookie',
      name: 'Rookie',
      price: 'Free',
      description: 'Basic lineup management for individual coaches',
      popular: false
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '$9.99/month',
      description: 'Advanced features for serious coaches and teams',
      popular: true
    }
  ];

  return (
    <Container className="py-5">
      <h1 className="text-center mb-5">LineupBoss Subscription Plans</h1>
      
      <Row className="mb-5">
        {plans.map((plan) => (
          <Col key={plan.id} md={6} className="mb-4">
            <Card className={`h-100 ${plan.popular ? 'border-primary' : ''}`}>
              {plan.popular && (
                <div className="ribbon ribbon-top-right"><span>Popular</span></div>
              )}
              <Card.Header as="h3" className={plan.popular ? 'bg-primary text-white' : ''}>
                {plan.name}
              </Card.Header>
              <Card.Body>
                <h2 className="mb-3">{plan.price}</h2>
                <p className="lead">{plan.description}</p>
                {currentTier === plan.id ? (
                  <Button variant="success" disabled>Current Plan</Button>
                ) : (
                  <Button variant={plan.popular ? 'primary' : 'outline-primary'}>
                    {plan.id === 'rookie' ? 'Free Plan' : 'Upgrade'}
                  </Button>
                )}
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="mb-5">
        <Card.Header as="h2" className="bg-light">
          Feature Comparison
        </Card.Header>
        <Card.Body>
          <Table responsive striped>
            <thead>
              <tr>
                <th style={{ width: '40%' }}>Feature</th>
                <th style={{ width: '20%' }}>Rookie</th>
                <th style={{ width: '20%' }}>Pro</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.id}>
                  <td>
                    <strong>{feature.name}</strong>
                    <p className="small text-muted mb-0">{feature.description}</p>
                  </td>
                  <td className="text-center align-middle">{feature.rookie}</td>
                  <td className="text-center align-middle">{feature.pro}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      <div className="text-center">
        <h3>Need more information?</h3>
        <p className="lead">Contact us at <a href="mailto:support@lineupboss.com">support@lineupboss.com</a></p>
      </div>

      <style jsx>{`
        .ribbon {
          position: absolute;
          right: -5px;
          top: -5px;
          z-index: 1;
          overflow: hidden;
          width: 75px;
          height: 75px;
          text-align: right;
        }
        .ribbon span {
          font-size: 10px;
          font-weight: bold;
          color: #FFF;
          text-transform: uppercase;
          text-align: center;
          line-height: 20px;
          transform: rotate(45deg);
          -webkit-transform: rotate(45deg);
          width: 100px;
          display: block;
          background: #007bff;
          box-shadow: 0 3px 10px -5px rgba(0, 0, 0, 1);
          position: absolute;
          top: 19px;
          right: -21px;
        }
      `}</style>
    </Container>
  );
};

export default SubscriptionFeatures;