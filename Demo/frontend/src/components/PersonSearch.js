import React, { useState, useEffect } from 'react';

const PersonSearch = ({ onPersonSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [allPersons, setAllPersons] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAllPersons();
  }, []);

  useEffect(() => {
    if (searchTerm.trim()) {
      performSearch(searchTerm);
    } else {
      setSearchResults(allPersons);
    }
  }, [searchTerm, allPersons]);

  const fetchAllPersons = async () => {
    try {
      setIsLoading(true);
      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/persons'
        : '/api/persons';
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch persons');
      }
      const data = await response.json();
      setAllPersons(data.persons);
      setSearchResults(data.persons);
    } catch (error) {
      console.error('Error fetching persons:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const performSearch = async (query) => {
    if (!query.trim()) return;

    try {
      const baseUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000'
        : '';
      const response = await fetch(`${baseUrl}/api/persons/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error('Search failed');
      }
      const data = await response.json();
      setSearchResults(data.results);
    } catch (error) {
      console.error('Search error:', error);
      // Fallback to local search
      const localResults = allPersons.filter(person => 
        person.firstName.toLowerCase().includes(query.toLowerCase()) ||
        person.lastName.toLowerCase().includes(query.toLowerCase()) ||
        person.fullName.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(localResults);
    }
  };

  const handlePersonClick = (person) => {
    if (onPersonSelect) {
      onPersonSelect(person);
    }
  };

  const formatDates = (person) => {
    const birth = person.birthDate ? new Date(person.birthDate).getFullYear() : '?';
    const death = person.deathDate ? new Date(person.deathDate).getFullYear() : (person.isAlive ? 'Present' : '?');
    return `${birth} - ${death}`;
  };

  const getPersonIcon = (person) => {
    return person.gender === 'M' ? '👨' : '👩';
  };

  if (isLoading) {
    return (
      <div>
        <h2>Family Members</h2>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <h2>Family Members</h2>
      
      <input
        type="text"
        className="search-input"
        placeholder="Search by name..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      
      <div className="person-list">
        {searchResults.length > 0 ? (
          searchResults.map(person => (
            <div
              key={person.id}
              className="person-item"
              onClick={() => handlePersonClick(person)}
            >
              <div className="person-name">
                {getPersonIcon(person)} {person.fullName}
              </div>
              <div className="person-dates">
                {formatDates(person)}
              </div>
              {person.birthPlace && (
                <div style={{ fontSize: '0.75rem', color: '#a0aec0', marginTop: '2px' }}>
                  📍 {person.birthPlace}
                </div>
              )}
            </div>
          ))
        ) : (
          <div style={{ 
            textAlign: 'center', 
            color: '#718096', 
            padding: '2rem',
            fontSize: '0.9rem'
          }}>
            {searchTerm ? 'No matching family members found' : 'No family members available'}
          </div>
        )}
      </div>
      
      {searchResults.length > 0 && (
        <div style={{ 
          marginTop: '1rem', 
          fontSize: '0.8rem', 
          color: '#718096',
          textAlign: 'center'
        }}>
          {searchResults.length} member{searchResults.length !== 1 ? 's' : ''} found
        </div>
      )}
      
      {searchTerm && (
        <button
          className="btn btn-secondary"
          style={{ width: '100%', marginTop: '0.5rem' }}
          onClick={() => setSearchTerm('')}
        >
          Show All Members
        </button>
      )}
    </div>
  );
};

export default PersonSearch;