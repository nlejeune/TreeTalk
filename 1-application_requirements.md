# TreeTalk Application Requirements

## 1. Functional Requirements

1. The application data source is provided by a manual upload (For the MVP, GEDCOM files only but the application should be architectured to support different type of format later).
2. The application must leverage LLM APIs for the purpose of offering chat functionality (The MVP application will be built with Openrouter API only)

## 2. Technical Requirements

1. The database will be a PostgreSQL database
2. The programming language for the backend is Python
3. The programming language for the frontend is Python with the streamlit framework
4. The application will be deployed on Docker
5. Configurations like API keys should be encrypted and persist when the container is restarted or upgraded

## 3. Backlog (Epics and User Stories)

### Epic 1: Data Source Management - Goal: Allow users to load and connect their genealogical data.
- User story 1.1: **As a user**, I want to be able to upload a GEDCOM file to import my family tree into the application.
- Acceptance criteria:
    - Upload accepts only .ged formats.
    - User is notified in case of success or failure.
    - Data is stored in Postgres database.
    - There is no way to upload multiple time the same .ged fil
    - The database contain no duplicated entries

- User story 1.2: **As a user**, I want to see and manage all my data sources (imported GEDCOM)
- Acceptance criteria:
    - Dashboard listing ged files.
    - Ability to delete a ged file (and all associated tables entries in the SQL database)
    - Visible synchronization status (last update date, success/error).

### Epic 2: Family Data Exploration - Goal: Allow intuitive navigation in the family tree.
- User story 2.1: **As a user**, I want to navigate my family tree to explore my ancestors and descendants.
- Acceptance criteria:
    - Interactive graphical display (zoom, movement).
    - Each person clickable with detailed profile.

- User story 2.2: **As a user**, I want to search for an ancestor by name to find them quickly.
- Acceptance criteria:
    - Search field with autocomplete.
    - Results listing exact and close matches.

### Epic 3: Chat with Family Data (TreeTalk) - Goal: Offer a natural conversation experience with family history.
- User story 3.1: **As a user**, I want to ask questions in natural language to explore my family tree.
- Acceptance criteria:
    - ChatGPT-type chat interface.
    - Conversation history preserved.

- User story 3.2: **As a user**, I want the chatbot responses to be based only on my imported family data.
- Acceptance criteria:
    - The backend transmits only relevant data to the LLM.
    - Responses cite sources (GEDCOM).
    - Guided exploration

- User story 3.3: **As a user**, I want the chatbot to suggest related questions (e.g., "Would you like to know more about Jean Dupont's descendants?").
- Acceptance criteria:
    - Automatic suggestions displayed under each response.

### Epic 4: Infrastructure and Integration - Goal: Make TreeTalk extensible and compatible with LLMs.
- User story 4.1: **As a developer**, I want the application to expose its data so that an external LLM can connect to it.
- Acceptance criteria:
    - Documented REST/WS endpoints.
    - Secure authentication.

- User story 4.2: **As an administrator**, I want the application to be deployable with Docker to simplify installation and portability.
- Acceptance criteria:
    - Dockerfile for backend and frontend.
    - docker-compose.yaml to orchestrate Postgres, backend, frontend.
    - PostgreSQL database

- User story 4.3: **As a developer**, I want to store all genealogical data in PostgreSQL to have a robust and relational database.
- Acceptance criteria:
    - Documented schema (persons, relationships, sources).
    - Migration scripts included.