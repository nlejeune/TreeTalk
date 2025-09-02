# TreeChat Demo

This demo showcases the core functionality of TreeChat with fake genealogical data to demonstrate the visual interface and chat capabilities.

## Demo Components

### Frontend (React)
- Interactive family tree visualization
- ChatGPT-like chat interface
- Data management dashboard

### Backend (Python)
- Mock genealogical data
- Basic MCP server simulation
- REST API endpoints

### Database
- Sample PostgreSQL schema
- Fake family data

## Quick Start

1. Install dependencies:
   ```bash
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   ```

2. Run the demo:
   ```bash
   # Terminal 1: Backend
   cd backend && python app.py
   
   # Terminal 2: Frontend
   cd frontend && npm start
   ```

3. Open http://localhost:3000 to view the demo

## Demo Features

- Explore the Dupont family tree (3 generations)
- Chat with family data using simulated responses
- Upload/manage data sources interface
- Interactive tree navigation with zoom and pan

## Fake Data

The demo includes a fictional French family:
- Jean Dupont (1920-1995) & Marie Durand (1925-2010)
- Their children: Pierre (1950) & Isabelle (1952)
- Grandchildren: Thomas, Sophie, Lucas, Emma (born 1975-1985)