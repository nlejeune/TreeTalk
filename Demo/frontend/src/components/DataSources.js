import React, { useState, useEffect } from 'react';

const DataSources = () => {
  const [sources, setSources] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [syncingSource, setSyncingSource] = useState(null);

  useEffect(() => {
    fetchDataSources();
  }, []);

  const fetchDataSources = async () => {
    try {
      setIsLoading(true);
      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/sources'
        : '/api/sources';
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch data sources');
      }
      const data = await response.json();
      setSources(data.sources);
    } catch (error) {
      console.error('Error fetching data sources:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async (sourceId) => {
    setSyncingSource(sourceId);
    try {
      const baseUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000'
        : '';
      const response = await fetch(`${baseUrl}/api/sources/${sourceId}/sync`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Sync failed');
      }
      const data = await response.json();
      
      // Update the source status
      setSources(prev => prev.map(source => 
        source.id === sourceId 
          ? { ...source, status: 'syncing', lastSync: new Date().toISOString() }
          : source
      ));
      
      // Simulate sync completion after 2 seconds
      setTimeout(() => {
        setSources(prev => prev.map(source => 
          source.id === sourceId 
            ? { ...source, status: 'active' }
            : source
        ));
        setSyncingSource(null);
      }, 2000);
      
    } catch (error) {
      console.error('Sync error:', error);
      setSyncingSource(null);
    }
  };

  const getSourceIcon = (type) => {
    switch (type) {
      case 'gedcom':
        return '📄';
      case 'familysearch':
        return '🌐';
      default:
        return '📊';
    }
  };

  const getStatusBadge = (source) => {
    const isCurrentlysyncing = syncingSource === source.id;
    
    if (isCurrentlysyncing || source.status === 'syncing') {
      return (
        <span style={{
          background: '#fef08a',
          color: '#92400e',
          padding: '2px 8px',
          borderRadius: '12px',
          fontSize: '0.7rem',
          fontWeight: '500',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            border: '1px solid #92400e',
            borderTop: '1px solid transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          Syncing
        </span>
      );
    }
    
    switch (source.status) {
      case 'active':
        return (
          <span style={{
            background: '#d1fae5',
            color: '#065f46',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '0.7rem',
            fontWeight: '500'
          }}>
            ✓ Active
          </span>
        );
      case 'disconnected':
        return (
          <span style={{
            background: '#fee2e2',
            color: '#991b1b',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '0.7rem',
            fontWeight: '500'
          }}>
            ⚠ Disconnected
          </span>
        );
      default:
        return (
          <span style={{
            background: '#f3f4f6',
            color: '#6b7280',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '0.7rem',
            fontWeight: '500'
          }}>
            Unknown
          </span>
        );
    }
  };

  const formatLastSync = (lastSync) => {
    if (!lastSync) return 'Never';
    
    const date = new Date(lastSync);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div>
        <h2>Data Sources</h2>
        <div className="loading">Loading sources...</div>
      </div>
    );
  }

  return (
    <div>
      <h2>Data Sources</h2>
      
      {sources.length > 0 ? (
        <div>
          {sources.map(source => (
            <div
              key={source.id}
              style={{
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '0.75rem',
                background: '#fafafa'
              }}
            >
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'flex-start',
                marginBottom: '0.5rem'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem',
                    marginBottom: '0.25rem'
                  }}>
                    <span style={{ fontSize: '1.1rem' }}>
                      {getSourceIcon(source.type)}
                    </span>
                    <strong style={{ fontSize: '0.9rem', color: '#2d3748' }}>
                      {source.name}
                    </strong>
                  </div>
                  {getStatusBadge(source)}
                </div>
              </div>
              
              <div style={{ 
                fontSize: '0.8rem', 
                color: '#718096',
                marginBottom: '0.5rem'
              }}>
                {source.description}
              </div>
              
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.75rem',
                color: '#a0aec0'
              }}>
                <span>
                  {source.personCount} persons • Last sync: {formatLastSync(source.lastSync)}
                </span>
                
                {source.status === 'active' && (
                  <button
                    className="btn btn-secondary"
                    style={{ 
                      fontSize: '0.7rem', 
                      padding: '0.25rem 0.5rem',
                      minHeight: 'auto'
                    }}
                    onClick={() => handleSync(source.id)}
                    disabled={syncingSource === source.id}
                  >
                    {syncingSource === source.id ? 'Syncing...' : '🔄 Sync'}
                  </button>
                )}
                
                {source.status === 'disconnected' && (
                  <button
                    className="btn btn-primary"
                    style={{ 
                      fontSize: '0.7rem', 
                      padding: '0.25rem 0.5rem',
                      minHeight: 'auto'
                    }}
                    onClick={() => alert('Demo: Connection setup would open here')}
                  >
                    🔗 Connect
                  </button>
                )}
              </div>
            </div>
          ))}
          
          <button
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem' }}
            onClick={() => alert('Demo: Add new data source dialog would open here')}
          >
            ➕ Add Data Source
          </button>
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          color: '#718096', 
          padding: '2rem',
          fontSize: '0.9rem'
        }}>
          <div style={{ marginBottom: '1rem', fontSize: '2rem' }}>📊</div>
          <div>No data sources configured</div>
          <button
            className="btn btn-primary"
            style={{ marginTop: '1rem' }}
            onClick={() => alert('Demo: Add data source dialog would open here')}
          >
            Add First Source
          </button>
        </div>
      )}
      
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default DataSources;