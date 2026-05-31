import React, { useState } from 'react';
import {
  Factory,
  Activity,
  Database,
  Settings,
  HeartPulse,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

type Tab =
  | 'production'
  | 'training'
  | 'history'
  | 'system'
  | 'settings';

interface SidebarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const NAV_ITEMS: { id: Tab; label: string; Icon: React.ElementType }[] = [
  { id: 'production', label: 'Production Run', Icon: Factory },
  { id: 'training', label: 'Training & Datasets', Icon: Activity },
  { id: 'history', label: 'Analytics & Logs', Icon: Database },
  { id: 'system', label: 'System Health', Icon: HeartPulse },
  { id: 'settings', label: 'Settings', Icon: Settings },
];

export const Sidebar = React.memo(function Sidebar({
  activeTab,
  onTabChange,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

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
        {NAV_ITEMS.map(({ id, label, Icon }) => (
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
              <span className="sidebar-label">{label}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="sidebar-footer">
          <div className="status-indicator online" />
          <span>System Online</span>
        </div>
      )}
    </aside>
  );
});