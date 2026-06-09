
import React from 'react';
import {
  Activity,
  Database,
  Server,
  ShieldCheck
} from 'lucide-react';

const APP_VERSION = '2.0.1';
const ENVIRONMENT = 'PRODUCTION';

export const Footer = React.memo(function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="workspace-footer">

      {/* Left Section */}
      <div className="footer-content">
        <div className="footer-brand-section">
          <span className="footer-brand">
            DiskVision Inspector
          </span>

          <span className="footer-copyright">
            © {currentYear} AI Industrial Solutions. All Rights Reserved.
          </span>
        </div>
      </div>

      {/* Center Section */}
      <div className="footer-status">

        <div className="footer-badge online">
          <Server size={12} />
          <span>API Online</span>
        </div>

        <div className="footer-badge online">
          <Database size={12} />
          <span>Database Connected</span>
        </div>

        <div className="footer-badge online">
          <Activity size={12} />
          <span>Monitoring Active</span>
        </div>

        <div className="footer-environment">
          {ENVIRONMENT}
        </div>

      </div>

      {/* Right Section */}
      <div className="footer-links">

        <a href="#help" className="footer-link">
          Help Center
        </a>

        <a href="#support" className="footer-link">
          Support
        </a>

        <a href="#documentation" className="footer-link">
          Documentation
        </a>

        <div className="footer-version">
          <ShieldCheck size={12} />
          <span>v{APP_VERSION}</span>
        </div>

      </div>

    </footer>
  );
});

Footer.displayName = 'Footer';
