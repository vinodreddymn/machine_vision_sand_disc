import { UserPlus, CheckCircle, Database, Clock, Trash2 } from 'lucide-react';

export type AdminTab = 'users' | 'audit' | 'compliance' | 'config' | 'cleanup' | 'timeline' | 'models';

interface AdminTabsProps {
  activeTab: AdminTab;
  onTabChange: (tab: AdminTab) => void;
}

export function AdminTabs({ activeTab, onTabChange }: AdminTabsProps) {
  return (
    <div className="admin-tabs">
      <button
        className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
        onClick={() => onTabChange('users')}
      >
        <UserPlus size={16} />
        Users &amp; Access
      </button>
      <button
        className={`admin-tab ${activeTab === 'compliance' ? 'active' : ''}`}
        onClick={() => onTabChange('compliance')}
      >
        <CheckCircle size={16} />
        Compliance
      </button>
      <button
        className={`admin-tab ${activeTab === 'config' ? 'active' : ''}`}
        onClick={() => onTabChange('config')}
      >
        <Database size={16} />
        Configuration Audit
      </button>
      <button
        className={`admin-tab ${activeTab === 'audit' ? 'active' : ''}`}
        onClick={() => onTabChange('audit')}
      >
        <Clock size={16} />
        System Audit
      </button>
      <button
        className={`admin-tab ${activeTab === 'cleanup' ? 'active' : ''}`}
        onClick={() => onTabChange('cleanup')}
      >
        <Trash2 size={16} />
        Data Management
      </button>
      <button
        className={`admin-tab ${activeTab === 'timeline' ? 'active' : ''}`}
        onClick={() => onTabChange('timeline')}
      >
        <Clock size={16} />
        Unified Timeline
      </button>
      <button
        className={`admin-tab ${activeTab === 'models' ? 'active' : ''}`}
        onClick={() => onTabChange('models')}
      >
        <Database size={16} />
        Model Registry
      </button>
    </div>
  );
}
