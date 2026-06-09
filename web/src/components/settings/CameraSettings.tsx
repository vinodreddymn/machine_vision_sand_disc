import React, { useState, useEffect } from 'react';
import { API } from '../../utils/constants';

export function CameraSettings() {
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [settings, setSettings] = useState({
    type: 'GigE Vision',
    make: 'Basler',
    ipAddress: '192.168.1.100',
    serialNo: 'BA-98231',
    username: 'admin',
    password: '',
    frameRate: '60',
    zoom: '1.0',
    focus: 'auto',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: value }));
    setSuccess(false);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    // Mock API call to save settings
    setTimeout(() => {
      setSaving(false);
      setSuccess(true);
    }, 800);
  };

  // Re-mount feed on render to ensure it refreshes if disconnected
  const [feedKey, setFeedKey] = useState(Date.now());
  useEffect(() => {
    const interval = setInterval(() => {
      // Periodically refresh the feed key if an error occurs, but for now we just load it once.
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid-production" style={{ padding: 0 }}>
      {/* Left Column: Form */}
      <div className="panel" style={{ padding: '24px' }}>
        <h2 style={{ marginBottom: '20px' }}>Hardware Configuration</h2>
        
        <form onSubmit={handleSave} style={{ display: 'grid', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Camera Make</label>
              <input 
                name="make"
                value={settings.make} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
              />
            </div>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Camera Type</label>
              <select 
                name="type"
                value={settings.type} 
                onChange={handleChange}
                className="select-input" 
                style={{ width: '100%' }}
              >
                <option value="GigE Vision">GigE Vision</option>
                <option value="USB3 Vision">USB3 Vision</option>
                <option value="Webcam">Webcam / DirectShow</option>
                <option value="RTSP Stream">RTSP IP Stream</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>IP Address</label>
              <input 
                name="ipAddress"
                value={settings.ipAddress} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
                placeholder="192.168.1.x"
              />
            </div>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Serial Number</label>
              <input 
                name="serialNo"
                value={settings.serialNo} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Auth Username</label>
              <input 
                name="username"
                value={settings.username} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
              />
            </div>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Auth Password</label>
              <input 
                type="password"
                name="password"
                value={settings.password} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
              />
            </div>
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid #2d3748', margin: '8px 0' }} />

          <h3 style={{ fontSize: '15px', marginTop: 0, marginBottom: '8px' }}>Optics & Stream</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Frame Rate (FPS)</label>
              <input 
                type="number"
                name="frameRate"
                value={settings.frameRate} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
              />
            </div>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Zoom Level</label>
              <input 
                type="number"
                step="0.1"
                name="zoom"
                value={settings.zoom} 
                onChange={handleChange}
                className="search-input" 
                style={{ width: '100%' }} 
              />
            </div>
            <div className="field-group">
              <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Focus Mode</label>
              <select 
                name="focus"
                value={settings.focus} 
                onChange={handleChange}
                className="select-input" 
                style={{ width: '100%' }}
              >
                <option value="auto">Auto Focus</option>
                <option value="manual">Manual</option>
                <option value="infinity">Infinity</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button 
              type="submit" 
              className="button good" 
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
            {success && <span style={{ color: '#10b981', fontSize: '14px', fontWeight: 600 }}>Settings applied successfully!</span>}
          </div>
        </form>
      </div>

      {/* Right Column: Live Feed */}
      <div className="production-feed-viewer">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', fontWeight: 600 }}>Live Hardware Feed</span>
          <div className="oee-badge">
            <div className="status-indicator online"></div>
            Online
          </div>
        </div>
        
        <div className="feed-box" style={{ flex: 1, display: 'flex' }}>
          <img 
            key={feedKey}
            src={API.STREAM_STATION1} 
            alt="Live Camera Feed" 
            style={{ 
              width: '100%', 
              height: '100%', 
              objectFit: 'contain', 
              background: '#090b0f',
              border: '1px solid #2d3748',
              borderRadius: '8px'
            }}
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiMwOTBiMGYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9ImFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjQ3NDhiIiBkeT0iLjNlbSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TGl2ZSBGZWVkIE9mZmxpbmU8L3RleHQ+PC9zdmc+';
            }}
          />
        </div>
        <div style={{ textAlign: 'center', fontSize: '12px', color: '#64748b' }}>
          Real-time MJPEG Stream directly from engine processor.
        </div>
      </div>
    </div>
  );
}
