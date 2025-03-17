import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="footer mt-auto py-3 bg-light">
      <div className="container">
        <div className="text-center">
          <p className="mb-1">© {currentYear} Groupe Bora LLC. All rights reserved.</p>
          <p className="mb-0">
            Need help? Contact <a href="mailto:admin@lineupboss.app">admin@lineupboss.app</a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;