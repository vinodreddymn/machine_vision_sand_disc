import React, { useState } from 'react';
import {
  Factory,
  Activity,
  Database,
  Settings,
  HeartPulse,
  Shield,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { canAccess } from '../../utils/permissions';

type Tab =
  | 'production'
  | 'training'
  | 'history'
  | 'system'
  | 'admin'
  | 'settings';

interface SidebarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const NAV_ITEMS: {
  id: Tab;
  label: string;
  Icon: React.ElementType;
}[] = [
  { id: 'production', label: 'Production Run', Icon: Factory },
  { id: 'training', label: 'Training & Datasets', Icon: Activity },
  { id: 'history', label: 'Analytics & Logs', Icon: Database },
  { id: 'system', label: 'System Health', Icon: HeartPulse },
  { id: 'admin', label: 'Administration', Icon: Shield },
  { id: 'settings', label: 'Settings', Icon: Settings },
];

export const Sidebar = React.memo(function Sidebar({
  activeTab,
  onTabChange,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  const role =
    localStorage.getItem('diskvision_role') ?? 'OPERATOR';

  const username =
    localStorage.getItem('diskvision_username') ?? '';

  const visibleNavItems = NAV_ITEMS.filter(({ id }) =>
    canAccess(role, id)
  );

  const handleLogout = () => {
    localStorage.removeItem('diskvision_token');
    localStorage.removeItem('diskvision_role');
    localStorage.removeItem('diskvision_username');
    window.location.reload();
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Factory size={28} />

          {!collapsed && (
            <div className="sidebar-brand">
              <h1>ASHTECH</h1>
              <span>Machine Vision Suite</span>
            </div>
          )}
        </div>

        <button
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          aria-label="Toggle Sidebar"
        >
          {collapsed ? (
            <ChevronRight size={18} />
          ) : (
            <ChevronLeft size={18} />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {visibleNavItems.map(({ id, label, Icon }) => (
          <button
            key={id}
            id={`nav-${id}`}
            className={`sidebar-button ${
              activeTab === id ? 'active' : ''
            }`}
            onClick={() => onTabChange(id)}
            title={collapsed ? label : undefined}
            aria-current={activeTab === id ? 'page' : undefined}
          >
            <Icon size={20} />

            {!collapsed && (
              <span className="sidebar-label">
                {label}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        {!collapsed && (
          <>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '12px',
              }}
            >
              <div className="status-indicator online" />
              <span>System Online</span>
            </div>

            <div
              style={{
                marginBottom: '12px',
                padding: '8px',
                borderRadius: '6px',
                background: 'rgba(255,255,255,0.04)',
              }}
            >
              {username && (
                <div
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                  }}
                >
                  {username}
                </div>
              )}

              <div
                style={{
                  fontSize: '12px',
                  opacity: 0.8,
                }}
              >
                Role: {role}
              </div>
            </div>
          </>
        )}

        <button
          className="sidebar-button"
          onClick={handleLogout}
          title="Logout"
          style={{
            width: '100%',
          }}
        >
          <LogOut size={20} />

          {!collapsed && (
            <span className="sidebar-label">
              Logout
            </span>
          )}
        </button>
      </div>
    </aside>
  );
});