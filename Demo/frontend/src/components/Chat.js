import React, { useState, useRef, useEffect } from 'react';

const Chat = ({ selectedPerson }) => {
  const [messages, setMessages] = useState([
    {
      type: 'assistant',
      content: "Hello! I'm here to help you explore the Dupont family history. What would you like to know?",
      suggestions: [
        "Tell me about Jean Dupont",
        "Who are Pierre's children?", 
        "Show me the family tree"
      ]
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (selectedPerson) {
      const message = `Tell me about ${selectedPerson.name}`;
      handleSendMessage(message);
    }
  }, [selectedPerson]);

  const handleSendMessage = async (message = inputValue) => {
    if (!message.trim()) return;

    const userMessage = {
      type: 'user',
      content: message
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/chat'
        : '/api/chat';
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      const assistantMessage = {
        type: 'assistant',
        content: data.response,
        suggestions: data.suggestions || []
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        suggestions: [
          "Tell me about Jean Dupont",
          "Who are the grandchildren?",
          "Search for Marie"
        ]
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion);
  };

  const clearChat = () => {
    setMessages([
      {
        type: 'assistant',
        content: "Chat cleared. How can I help you explore the family history?",
        suggestions: [
          "Tell me about Jean Dupont",
          "Who are Pierre's children?",
          "Show me the family tree"
        ]
      }
    ]);
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index}>
            <div className={`message ${message.type}`}>
              {message.content}
            </div>
            
            {message.suggestions && message.suggestions.length > 0 && (
              <div className="suggestions">
                <h4>💡 Try asking:</h4>
                {message.suggestions.map((suggestion, suggestionIndex) => (
                  <button
                    key={suggestionIndex}
                    className="suggestion-btn"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant">
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              color: '#718096'
            }}>
              <div style={{
                width: '16px',
                height: '16px',
                border: '2px solid #e2e8f0',
                borderTop: '2px solid #667eea',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
              Thinking...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Ask about the family history..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button
          className="btn btn-primary"
          onClick={() => handleSendMessage()}
          disabled={isLoading || !inputValue.trim()}
        >
          Send
        </button>
        <button
          className="btn btn-secondary"
          onClick={clearChat}
          title="Clear chat"
        >
          🗑️
        </button>
      </div>
      
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Chat;