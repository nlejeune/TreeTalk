"""
TreeTalk - Main Streamlit Application
Converse with Your Family History

This is the main user interface for the TreeTalk genealogy application.
Built with Streamlit, it provides an intuitive web interface for:

Core Features:
- GEDCOM file upload and management
- Interactive family tree visualization using Plotly
- AI-powered chat about family history
- Person search and selection
- Data exploration with filtering and sorting

Architecture:
- Streamlit web framework for rapid UI development
- RESTful API integration with FastAPI backend
- Plotly + NetworkX for family tree visualization
- Session state management for user interactions
- Responsive design with horizontal navigation

Key Components:
1. Data Exploration Tab: Browse and visualize family data
2. Configuration Tab: API settings and preferences  
3. GEDCOM Management Tab: File upload and deletion
4. Chat Interface: AI conversations about family history
5. Interactive Family Tree: Visual relationship mapping

Performance Optimizations:
- Cached API responses for faster loading
- Optimized NetworkX layouts for large family trees
- Efficient Plotly rendering with reduced iterations
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard library imports
import json
import math
import os
from typing import Dict, List, Optional

# Third-party imports - Streamlit and web
import streamlit as st
import requests

# Third-party imports - data processing and visualization
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

# =============================================================================
# CONFIGURATION
# =============================================================================

# Backend API URL - configurable via environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="TreeTalk - Converse with Your Family History",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background-color: #2c3e50;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .family-member-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 6px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .family-member-card:hover {
        background-color: #e9ecef;
        transform: translateX(2px);
    }
    .family-member-selected {
        background-color: #3498db;
        color: white;
        border-color: #2980b9;
    }
    .chat-message {
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 8px;
    }
    .chat-user {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .chat-ai {
        background-color: #f3e5f5;
        margin-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'selected_gedcom' not in st.session_state:
        st.session_state.selected_gedcom = None
    if 'selected_person' not in st.session_state:
        st.session_state.selected_person = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False

def get_gedcom_files() -> List[Dict]:
    """Get list of uploaded GEDCOM files from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/sources")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching GEDCOM files: {e}")
        return []

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_family_members(gedcom_id: str) -> List[Dict]:
    """Get family members from selected GEDCOM file."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/persons?source_id={gedcom_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching family members: {e}")
        return []

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_family_tree(person_id: str) -> Dict:
    """Get family tree data for visualization."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/persons/{person_id}/family-tree")
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        st.error(f"Error fetching family tree: {e}")
        return {}

@st.cache_data(ttl=600, show_spinner=False)  # Cache for 10 minutes
def create_network_layout(persons_str: str, relationships_str: str):
    """Create NetworkX graph and calculate layout - cached for performance."""
    import json
    
    # Parse the JSON strings back to objects
    persons = json.loads(persons_str)
    relationships = json.loads(relationships_str)
    
    # Create a NetworkX graph for layout calculation
    G = nx.Graph()
    
    # Add nodes
    person_dict = {p['id']: p for p in persons}
    for person in persons:
        G.add_node(person['id'], **person)
    
    # Add edges
    for rel in relationships:
        G.add_edge(rel['person1_id'], rel['person2_id'], type=rel['type'])
    
    # Use faster layout algorithm for better performance
    # Spring layout with fewer iterations for speed
    pos = nx.spring_layout(G, k=1.5, iterations=10)  # Further reduced for performance
    
    return G, pos, person_dict

def send_chat_message(message: str, person_context: Optional[str] = None) -> str:
    """Send message to chat API."""
    try:
        payload = {
            "message": message,
            "person_context": person_context,
            "session_id": st.session_state.get('session_id', 'default')
        }
        response = requests.post(f"{BACKEND_URL}/api/chat/message", json=payload)
        if response.status_code == 200:
            return response.json().get('response', 'No response received.')
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error sending message: {e}"

def render_navigation():
    """Render the main navigation."""
    st.markdown('<div class="main-header"><h1>🌳 TreeTalk - Converse with Your Family History</h1></div>', 
                unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data Exploration", "⚙️ Configuration", "📁 GEDCOM Management"])
    
    return tab1, tab2, tab3

def render_data_exploration_tab(tab):
    """Render the data exploration tab."""
    with tab:
        # GEDCOM File Selector
        gedcom_files = get_gedcom_files()
        gedcom_options = {f"{file['name']}": file['id'] for file in gedcom_files}
        
        if gedcom_options:
            selected_gedcom = st.selectbox(
                "Select GEDCOM File:",
                options=list(gedcom_options.keys()),
                index=0 if gedcom_options else None,
                key="gedcom_selector"
            )
            
            if selected_gedcom:
                st.session_state.selected_gedcom = gedcom_options[selected_gedcom]
        else:
            st.warning("No GEDCOM files found. Please upload a GEDCOM file in the GEDCOM Management tab.")
            return

        # Main content columns
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Family Members")
            
            # Search box
            search_term = st.text_input("Search by name:", key="person_search")
            
            # Get family members
            if st.session_state.selected_gedcom:
                family_members = get_family_members(st.session_state.selected_gedcom)
                
                # Filter members based on search
                if search_term:
                    filtered_members = [
                        member for member in family_members 
                        if search_term.lower() in member.get('name', '').lower()
                    ]
                else:
                    filtered_members = family_members
                
                # Display family members with pagination
                members_per_page = 15  # Reduced for better performance
                total_members = len(filtered_members)
                
                if total_members > members_per_page:
                    st.info(f"Showing first {members_per_page} of {total_members} members")
                
                for member in filtered_members[:members_per_page]:
                    member_name = member.get('name', 'Unknown')
                    birth_year = member.get('birth_date', '')[:4] if member.get('birth_date') else '?'
                    death_year = member.get('death_date', '')[:4] if member.get('death_date') else ('Living' if member.get('is_living') else '?')
                    gender = member.get('gender', 'U')
                    
                    if st.button(
                        f"{member_name} ({birth_year}-{death_year}) • {gender}",
                        key=f"member_{member['id']}",
                        help=f"Click to view family tree for {member_name}"
                    ):
                        st.session_state.selected_person = member['id']
                        # Removed st.rerun() to prevent flickering - Streamlit will refresh naturally
        
        with col2:
            st.subheader("Family Tree Visualization")
            
            if st.session_state.selected_person:
                # Get family tree data
                tree_data = get_family_tree(st.session_state.selected_person)
                
                if tree_data:
                    # Create Plotly network graph visualization
                    try:
                        persons = tree_data.get('persons', [])
                        relationships = tree_data.get('relationships', [])
                        
                        if persons:
                            # Limit family tree size for performance
                            max_persons = 75  # Limit for large family trees
                            if len(persons) > max_persons:
                                st.warning(f"⚠️ Large family tree detected ({len(persons)} people). Showing closest {max_persons} relatives for better performance.")
                                persons = persons[:max_persons]
                                # Filter relationships to only include those between displayed persons
                                person_ids = set(p['id'] for p in persons)
                                relationships = [r for r in relationships 
                                               if r['person1_id'] in person_ids and r['person2_id'] in person_ids]
                            
                            # Convert to JSON strings for caching
                            persons_str = json.dumps(persons, sort_keys=True)
                            relationships_str = json.dumps(relationships, sort_keys=True)
                            
                            # Use cached network layout creation for better performance
                            G, pos, person_dict = create_network_layout(persons_str, relationships_str)
                            
                            # Prepare data for Plotly
                            edge_x = []
                            edge_y = []
                            edge_info = []
                            
                            for edge in G.edges():
                                x0, y0 = pos[edge[0]]
                                x1, y1 = pos[edge[1]]
                                edge_x.extend([x0, x1, None])
                                edge_y.extend([y0, y1, None])
                                
                                # Get relationship type for styling
                                rel_type = G[edge[0]][edge[1]].get('type', 'unknown')
                                edge_info.append(rel_type)
                            
                            # Create edge trace
                            edge_trace = go.Scatter(
                                x=edge_x, y=edge_y,
                                line=dict(width=2, color='#888'),
                                hoverinfo='none',
                                mode='lines'
                            )
                            
                            # Create node traces (separate by gender for coloring)
                            node_traces = []
                            
                            for gender, color in [('M', '#3498db'), ('F', '#e91e63'), ('U', '#27ae60'), (None, '#95a5a6')]:
                                filtered_persons = [p for p in persons if p.get('gender') == gender]
                                
                                if filtered_persons:
                                    node_x = []
                                    node_y = []
                                    node_text = []
                                    node_info = []
                                    
                                    for person in filtered_persons:
                                        x, y = pos[person['id']]
                                        node_x.append(x)
                                        node_y.append(y)
                                        node_text.append(person.get('name', 'Unknown'))
                                        
                                        # Create hover info
                                        birth = person.get('birth_date', 'Unknown')
                                        death = person.get('death_date', 'Living' if person.get('is_living') else 'Unknown')
                                        info = f"Name: {person.get('name', 'Unknown')}<br>Born: {birth}<br>Died: {death}"
                                        node_info.append(info)
                                    
                                    gender_label = {'M': 'Male', 'F': 'Female', 'U': 'Unknown', None: 'Unknown'}[gender]
                                    
                                    node_trace = go.Scatter(
                                        x=node_x, y=node_y,
                                        mode='markers+text',
                                        hoverinfo='text',
                                        text=node_text,
                                        textposition="bottom center",
                                        hovertext=node_info,
                                        marker=dict(
                                            size=20,
                                            color=color,
                                            line=dict(width=2, color='white')
                                        ),
                                        name=gender_label
                                    )
                                    node_traces.append(node_trace)
                            
                            # Create figure with optimized settings
                            fig = go.Figure(data=[edge_trace] + node_traces,
                                          layout=go.Layout(
                                                title=f'Family Tree for {tree_data.get("central_person_name", "Selected Person")}',
                                                titlefont_size=16,
                                                showlegend=True,
                                                hovermode='closest',
                                                margin=dict(b=20,l=5,r=5,t=40),
                                                annotations=[ dict(
                                                    text="Click and drag to explore. Hover over nodes for details.",
                                                    showarrow=False,
                                                    xref="paper", yref="paper",
                                                    x=0.005, y=-0.002,
                                                    xanchor="left", yanchor="bottom",
                                                    font=dict(color="gray", size=12)
                                                )],
                                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                                plot_bgcolor="white",
                                                # Add performance optimizations
                                                dragmode='pan',  # Faster than zoom
                                                uirevision='constant'  # Preserve view state
                                            ))
                            
                            # Display the graph with performance optimizations
                            st.plotly_chart(fig, use_container_width=True, 
                                          config={'displayModeBar': False,  # Hide toolbar for faster rendering
                                                 'staticPlot': False,
                                                 'responsive': True})
                            
                            # Display legend
                            st.markdown("**Legend:** 🔵 Male • 🔴 Female • 🟢 Unknown Gender")
                        
                        else:
                            st.info("No family tree data available for this person.")
                    
                    except Exception as e:
                        st.error(f"Error rendering family tree: {e}")
                        
                        # Fallback: display as a simple table
                        if tree_data.get('persons'):
                            st.subheader("Family Members (Table View)")
                            df = pd.DataFrame(tree_data['persons'])
                            st.dataframe(df)
            else:
                st.info("Select a family member to view their family tree.")
        
        # Chat section at the bottom
        st.subheader("💬 Chat with Your Family History")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message['type'] == 'user':
                    st.markdown(f'<div class="chat-message chat-user"><strong>You:</strong> {message["content"]}</div>', 
                               unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message chat-ai"><strong>AI:</strong> {message["content"]}</div>', 
                               unsafe_allow_html=True)
        
        # Chat input
        chat_input = st.text_input(
            "Ask about your family history:",
            placeholder="e.g., Tell me about John Smith, Who are Mary's children?",
            key="chat_input"
        )
        
        col_send, col_suggestions = st.columns([1, 3])
        
        with col_send:
            if st.button("Send", key="send_chat"):
                if chat_input and st.session_state.api_configured:
                    # Add user message to history
                    st.session_state.chat_history.append({
                        'type': 'user',
                        'content': chat_input
                    })
                    
                    # Send to backend and get response
                    ai_response = send_chat_message(
                        chat_input, 
                        st.session_state.selected_person
                    )
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({
                        'type': 'ai',
                        'content': ai_response
                    })
                    
                    st.rerun()
                elif not st.session_state.api_configured:
                    st.error("Please configure your OpenRouter API key in the Configuration tab.")
        
        with col_suggestions:
            if st.button("Tell me about this person", key="suggest1") and st.session_state.selected_person:
                # Auto-populate with suggestion
                st.session_state.chat_input = "Tell me about the selected person"
            
            if st.button("Who are the children?", key="suggest2"):
                st.session_state.chat_input = "Who are the children of the selected person?"

def render_configuration_tab(tab):
    """Render the configuration tab."""
    with tab:
        st.subheader("API Configuration")
        
        # OpenRouter API Configuration
        st.markdown("### OpenRouter API Settings")
        openrouter_key = st.text_input(
            "OpenRouter API Key:",
            type="password",
            help="Your API key will be encrypted and stored securely."
        )
        
        if st.button("Save OpenRouter Configuration"):
            if openrouter_key:
                # Save configuration to backend
                try:
                    response = requests.post(f"{BACKEND_URL}/api/config/openrouter", 
                                           json={"api_key": openrouter_key})
                    if response.status_code == 200:
                        st.success("✅ OpenRouter API key configured and encrypted!")
                        st.session_state.api_configured = True
                    else:
                        st.error("Failed to save configuration.")
                except Exception as e:
                    st.error(f"Error saving configuration: {e}")
            else:
                st.error("Please enter your OpenRouter API key.")
        
        # FamilySearch API Configuration (Optional)
        st.markdown("### FamilySearch API Settings (Optional)")
        familysearch_client = st.text_input("FamilySearch Client ID:")
        
        if st.button("Save FamilySearch Configuration"):
            if familysearch_client:
                # Save FamilySearch configuration
                try:
                    response = requests.post(f"{BACKEND_URL}/api/config/familysearch", 
                                           json={"client_id": familysearch_client})
                    if response.status_code == 200:
                        st.success("✅ FamilySearch configuration saved!")
                    else:
                        st.error("Failed to save FamilySearch configuration.")
                except Exception as e:
                    st.error(f"Error saving configuration: {e}")
        
        # Configuration Status
        st.markdown("### Configuration Status")
        
        # Check API status
        try:
            response = requests.get(f"{BACKEND_URL}/api/config/status")
            if response.status_code == 200:
                status = response.json()
                openrouter_status = "✅ Configured" if status.get('openrouter_configured') else "❌ Not Configured"
                familysearch_status = "✅ Configured" if status.get('familysearch_configured') else "❌ Not Configured"
                
                st.write(f"**OpenRouter API:** {openrouter_status}")
                st.write(f"**FamilySearch API:** {familysearch_status}")
                
                st.session_state.api_configured = status.get('openrouter_configured', False)
        except Exception as e:
            st.error(f"Unable to check configuration status: {e}")

def render_gedcom_management_tab(tab):
    """Render the GEDCOM management tab."""
    with tab:
        st.subheader("GEDCOM File Management")
        
        # File Upload Section
        st.markdown("### Upload GEDCOM File")
        uploaded_file = st.file_uploader(
            "Choose a GEDCOM file",
            type=['ged', 'gedcom'],
            help="Supported formats: GEDCOM (.ged) • Maximum size: 50MB"
        )
        
        if uploaded_file is not None:
            # Create unique identifier for this file
            file_hash = f"{uploaded_file.name}_{uploaded_file.size}_{uploaded_file.file_id}"
            upload_key = f"upload_in_progress_{file_hash}"
            uploaded_files_key = "uploaded_files_set"
            
            # Initialize uploaded files tracking
            if uploaded_files_key not in st.session_state:
                st.session_state[uploaded_files_key] = set()
            
            # Check if this exact file has already been uploaded in this session
            if file_hash in st.session_state[uploaded_files_key]:
                st.warning(f"⚠️ File '{uploaded_file.name}' has already been uploaded in this session!")
                st.info("Refresh the page if you want to upload it again.")
            
            # Check if upload is in progress
            elif st.session_state.get(upload_key, False):
                st.info("⏳ Upload in progress... Please wait.")
                st.info("Do not click the button again or refresh the page.")
                
            else:
                # Show upload button
                if st.button("Import GEDCOM File", key=f"import_btn_{file_hash}"):
                    # Set upload in progress flag immediately
                    st.session_state[upload_key] = True
                    st.rerun()
                    
            # Handle the actual upload after rerun
            if st.session_state.get(upload_key, False) and file_hash not in st.session_state[uploaded_files_key]:
                # Upload file to backend
                with st.spinner(f"Uploading and processing {uploaded_file.name}..."):
                    try:
                        files = {"file": uploaded_file}
                        response = requests.post(f"{BACKEND_URL}/api/import/gedcom", files=files)
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            if result.get('duplicate', False):
                                st.warning(f"⚠️ File '{uploaded_file.name}' already exists in the database!")
                                st.info("No new data was imported to prevent duplicates.")
                            else:
                                st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
                                st.info(f"Import task ID: {result.get('task_id')}")
                                st.info(f"Individuals imported: {result.get('statistics', {}).get('individuals_imported', 0)}")
                                st.info(f"Relationships imported: {result.get('statistics', {}).get('relationships_imported', 0)}")
                            
                            # Mark file as uploaded and clear progress flag
                            st.session_state[uploaded_files_key].add(file_hash)
                            st.session_state[upload_key] = False
                            
                        else:
                            error_detail = response.json().get('detail', response.text) if response.headers.get('content-type', '').startswith('application/json') else response.text
                            st.error(f"Upload failed: {error_detail}")
                            st.session_state[upload_key] = False
                            
                    except Exception as e:
                        st.error(f"Error uploading file: {e}")
                        st.session_state[upload_key] = False
        
        # Debug/Reset Section
        if st.button("🔄 Reset Upload State", help="Clear upload session state if stuck"):
            # Clear all upload-related session state
            keys_to_remove = [key for key in st.session_state.keys() 
                             if key.startswith('upload_') or key == 'uploaded_files_set']
            for key in keys_to_remove:
                del st.session_state[key]
            st.success("Upload state cleared!")
            st.rerun()
        
        st.divider()
        
        # Cleanup Section
        st.markdown("### Database Cleanup")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("Remove duplicate GEDCOM files (keeps the most recent version of each file)")
        with col2:
            if st.button("🧹 Clean Duplicates", help="Remove duplicate GEDCOM files from database"):
                try:
                    response = requests.post(f"{BACKEND_URL}/api/sources/cleanup-duplicates")
                    if response.status_code == 200:
                        result = response.json()
                        total_removed = result.get('total_removed', 0)
                        if total_removed > 0:
                            st.success(f"✅ Cleaned up {total_removed} duplicate sources!")
                            with st.expander("View removed duplicates"):
                                for removed in result.get('removed_sources', []):
                                    st.write(f"- {removed['name']} (ID: {removed['id']})")
                            st.rerun()
                        else:
                            st.info("✨ No duplicates found - database is clean!")
                    else:
                        st.error(f"Cleanup failed: {response.text}")
                except Exception as e:
                    st.error(f"Error during cleanup: {e}")

        st.divider()
        
        # Imported Files Section
        st.markdown("### Imported GEDCOM Files")
        
        gedcom_files = get_gedcom_files()
        
        if gedcom_files:
            for file in gedcom_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{file.get('name', 'Unknown')}**")
                    st.write(f"Imported: {file.get('imported_at', 'Unknown')}")
                    if file.get('description'):
                        st.write(f"Description: {file.get('description')}")
                
                with col2:
                    if st.button("View Details", key=f"view_{file['id']}"):
                        # Show file details
                        st.info(f"File ID: {file['id']}")
                        if file.get('metadata'):
                            st.json(file['metadata'])
                
                with col3:
                    # Check if this file is in delete confirmation mode
                    delete_confirm_key = f"delete_confirm_{file['id']}"
                    
                    if st.session_state.get(delete_confirm_key, False):
                        # Show confirmation buttons
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✅ Confirm", key=f"confirm_delete_{file['id']}", type="primary"):
                                try:
                                    response = requests.delete(f"{BACKEND_URL}/api/sources/{file['id']}")
                                    if response.status_code == 200:
                                        st.success("File deleted successfully!")
                                        # Clear the confirmation state
                                        st.session_state[delete_confirm_key] = False
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete file: {response.text}")
                                        st.session_state[delete_confirm_key] = False
                                except Exception as e:
                                    st.error(f"Error deleting file: {e}")
                                    st.session_state[delete_confirm_key] = False
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_delete_{file['id']}"):
                                st.session_state[delete_confirm_key] = False
                                st.rerun()
                    else:
                        # Show delete button
                        if st.button("🗑️ Delete", key=f"delete_{file['id']}", 
                                   help="Delete this GEDCOM file and all related data"):
                            # Set confirmation mode
                            st.session_state[delete_confirm_key] = True
                            st.rerun()
                
                st.divider()
        else:
            st.info("No GEDCOM files imported yet.")

def main():
    """Main application function."""
    try:
        initialize_session_state()
        
        # Render navigation
        tab1, tab2, tab3 = render_navigation()
        
        # Render tabs with error handling
        try:
            render_data_exploration_tab(tab1)
        except Exception as e:
            with tab1:
                st.error(f"Error in Data Exploration tab: {str(e)}")
                st.exception(e)
        
        try:
            render_configuration_tab(tab2)
        except Exception as e:
            with tab2:
                st.error(f"Error in Configuration tab: {str(e)}")
                st.exception(e)
        
        try:
            render_gedcom_management_tab(tab3)
        except Exception as e:
            with tab3:
                st.error(f"Error in GEDCOM Management tab: {str(e)}")
                st.exception(e)
                
    except Exception as e:
        st.error(f"Critical error in main function: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()