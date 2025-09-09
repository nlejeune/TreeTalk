# TreeTalk — UX & Layout Specification

## 1) Global Navigation
- **Top horizontal menu** with three items (tabs/pages):
  1. **Data Exploration** (main page)
  2. **Configuration** (API keys & model selection)
  3. **GEDCOM File Management** (import/delete GEDCOM files)

## 2) Data Exploration (Main Page)

### 2.1 GEDCOM Selector
- **Dropdown** at the top of the page to choose the active GEDCOM dataset to explore.

### 2.2 Family Members — Search & Select
- **Text input**: search by person name.  
- **Dynamic results list**: updates as the user types; clicking a person sets them as the **focused person** for the visualization.

### 2.3 Family Tree Visualization
- **Component**: `family-chart (D3.js)`.  
- **Scope**: show **up to 4 layers** (degrees) of relationships from the focused person.  
- **Node colors**:
  - Male: **blue**
  - Female: **pink**
  - Unknown/unspecified sex: **green**

### 2.4 “Chat with Your Family History”
- **Placement**: bottom of the page; width **matches** the Family Tree Visualization section.  
- **UI**: ChatGPT-like interface (message list + input box).  
- **Backend**:
  - Use **OpenRouter API** for LLM responses.
  - Retrieve context from **PostgreSQL** (populated by parsed GEDCOM and any enrichment).

## 3) Configuration Page
- **OpenRouter API key** field (create & later edit).  
- **Model selection** dropdown for chat:
  - Populate by calling **`/api/v1/models`** (OpenRouter).
  - **Sort by increasing price** (free models first).
  - Display model name + pricing metadata.
- **Persistence**: save all configuration values to a **PostgreSQL `configuration` table**.

## 4) GEDCOM File Management Page
- **Upload section**: select and upload **.ged / GEDCOM** files; ingest into the database.  
- **File list**: display all uploaded GEDCOM files (name, size, upload date, status).  
- **Delete action**:
  - Allow deleting a selected file from storage.
  - **Cascade delete**: remove all related database entries ingested from that file.

## 5) Website Mockup (Static)
- Produce a **pure HTML** mockup of the three pages and their key components.  
- **Use components from the framework defined in `1-application_requirements.md`** (naming, classes, and structure should align with that framework).  
- The mockup should include:
  - Top horizontal menu with the three destinations.
  - Data Exploration page with GEDCOM dropdown, search/list, graph placeholder, and chat layout.
  - Configuration page with API fields and model dropdown (mock data ok).
  - GEDCOM management page with upload form, file table, and delete controls.
- No dynamic behavior is required in the mockup; placeholders are acceptable where APIs would be called.

## 6) Data & Interaction Notes
- **Focused person** is the single source of truth for the visualization; changing selection updates the graph and chat context.  
- **Privacy**: avoid storing chat histories containing sensitive personal data unless explicitly required; if stored, tie them to the selected GEDCOM file.  
- **Error states**:
  - If no GEDCOM is selected, disable search/visualization/chat and show a prompt to pick a dataset.
  - If OpenRouter key is missing/invalid, disable chat and show an inline configuration hint.
  - If model list fetch fails, allow manual model entry or retry.

## 7) Visual/UX Constraints
- Responsive layout; top menu remains visible.  
- Chat section height is constrained but scrollable; input is fixed at the bottom of that section.  
- Colors and line styles in the graph adhere strictly to the rules above for quick cognition.
