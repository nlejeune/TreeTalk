import React, { useState, useEffect } from 'react';
import FamilyTree from './components/FamilyTree';
import Chat from './components/Chat';
import PersonSearch from './components/PersonSearch';
import DataSources from './components/DataSources';
import './index.css';

function App() {
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [familyData, setFamilyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFamilyData();
  }, []);

  const fetchFamilyData = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/family-tree'
        : '/api/family-tree';
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch family data');
      }
      const data = await response.json();
      setFamilyData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePersonSelect = (person) => {
    setSelectedPerson(person);
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading TreeChat Demo...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🌳 TreeChat Demo</h1>
        <p>Explore the Dupont family history through conversation and visualization</p>
      </header>
      
      <div className="main-content">
        <aside className="sidebar">
          <div className="panel">
            <PersonSearch onPersonSelect={handlePersonSelect} />
          </div>
          
          <div className="panel" style={{ marginTop: '1rem' }}>
            <DataSources />
          </div>
        </aside>
        
        <main className="main-panel">
          <div className="panel">
            <h2>Family Tree Visualization</h2>
            {familyData && (
              <FamilyTree 
                data={familyData} 
                onPersonSelect={handlePersonSelect}
                selectedPerson={selectedPerson}
              />
            )}
          </div>
          
          <div className="panel">
            <h2>Chat with Your Family History</h2>
            <Chat selectedPerson={selectedPerson} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;