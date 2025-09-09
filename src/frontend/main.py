"""
TreeTalk Frontend - Streamlit Application

This is the main Streamlit application providing the user interface for TreeTalk.
It implements the three-tab design specified in the UI requirements with
family tree exploration, chat functionality, and configuration management.

Key Features:
- Three-tab navigation: Data Exploration, Configuration, GEDCOM Management
- Interactive family tree visualization
- ChatGPT-style conversational interface
- GEDCOM file upload and management
- OpenRouter API integration configuration
"""

import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = 30

# Page configuration
st.set_page_config(
    page_title="🌳 TreeTalk - Converse with Your Family History",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff4b4b, #ff6b6b);
        padding: 1rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 10px 10px;
        color: white;
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .family-tree-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


class TreeTalkAPI:
    """API client for TreeTalk backend communication."""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to backend API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error ({response.status_code}): {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            logger.error(f"API request failed: {e}")
            return None
    
    def get_sources(self) -> List[Dict]:
        """Get list of GEDCOM sources."""
        result = self._make_request("GET", "/api/gedcom/sources")
        return result if result else []
    
    def upload_gedcom(self, file_bytes: bytes, filename: str, source_name: str = None) -> Optional[Dict]:
        """Upload GEDCOM file."""
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        data = {"source_name": source_name} if source_name else {}
        
        return self._make_request("POST", "/api/gedcom/upload", files=files, data=data)
    
    def search_persons(self, query: str, source_id: str = None, limit: int = 50) -> List[Dict]:
        """Search for persons."""
        params = {"q": query, "limit": limit}
        if source_id:
            params["source_id"] = source_id
            
        result = self._make_request("GET", "/api/persons/search", params=params)
        return result if result else []
    
    def get_family_tree(self, person_id: str, max_generations: int = 4, source_id: str = None) -> Optional[Dict]:
        """Get family tree data."""
        params = {"max_generations": max_generations}
        if source_id:
            params["source_id"] = source_id
            
        return self._make_request("GET", f"/api/persons/{person_id}/family-tree", params=params)
    
    def send_chat_message(self, message: str, session_id: str = None, model_name: str = None) -> Optional[Dict]:
        """Send chat message."""
        data = {
            "message": message,
            "session_id": session_id,
            "model_name": model_name
        }
        return self._make_request("POST", "/api/chat/message", json=data)
    
    def get_available_models(self) -> List[Dict]:
        """Get available AI models."""
        result = self._make_request("GET", "/api/chat/models")
        return result if result else []
    
    def set_api_configuration(self, openrouter_api_key: str = None, default_model: str = None) -> Optional[Dict]:
        """Set API configuration."""
        data = {}
        if openrouter_api_key:
            data["openrouter_api_key"] = openrouter_api_key
        if default_model:
            data["default_model"] = default_model
            
        return self._make_request("POST", "/api/config/api-key", json=data)
    
    def get_api_key_status(self) -> Dict:
        """Get API key configuration status."""
        result = self._make_request("GET", "/api/config/api-key/status")
        return result if result else {}


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = TreeTalkAPI()
    
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'selected_person' not in st.session_state:
        st.session_state.selected_person = None
    
    if 'selected_source' not in st.session_state:
        st.session_state.selected_source = None
    
    if 'family_tree_data' not in st.session_state:
        st.session_state.family_tree_data = None


def render_header():
    """Render the main application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🌳 TreeTalk</h1>
        <p style="margin: 0; opacity: 0.9;">Converse with Your Family History</p>
    </div>
    """, unsafe_allow_html=True)


def render_data_exploration_tab():
    """Render the Data Exploration tab content."""
    st.header("Data Exploration")
    
    # GEDCOM Source Selector
    st.subheader("📚 Select GEDCOM Dataset")
    sources = st.session_state.api_client.get_sources()
    
    if not sources:
        st.info("No GEDCOM files uploaded yet. Go to the GEDCOM Management tab to upload your family data.")
        return
    
    source_options = {f"{s['name']} ({s['persons_count']} persons)": s['id'] for s in sources}
    selected_source_display = st.selectbox(
        "Choose a dataset to explore:",
        options=list(source_options.keys()),
        index=0
    )
    
    if selected_source_display:
        selected_source_id = source_options[selected_source_display]
        st.session_state.selected_source = selected_source_id
        
        # Two-column layout for search and visualization
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Person Search
            st.subheader("👥 Family Members - Search & Select")
            search_query = st.text_input("Search by person name:", placeholder="Enter name to search...")
            
            if search_query and len(search_query) >= 2:
                search_results = st.session_state.api_client.search_persons(
                    query=search_query,
                    source_id=selected_source_id,
                    limit=10
                )
                
                if search_results:
                    st.write("**Search Results:**")
                    for person in search_results:
                        if st.button(
                            f"{person['display_name']} ({person['life_span']})",
                            key=f"person_{person['id']}",
                            help=f"Click to focus family tree on {person['display_name']}"
                        ):
                            st.session_state.selected_person = person
                            # Get family tree data
                            family_tree = st.session_state.api_client.get_family_tree(
                                person_id=person['id'],
                                max_generations=4,
                                source_id=selected_source_id
                            )
                            st.session_state.family_tree_data = family_tree
                            st.rerun()
                else:
                    st.info("No persons found matching your search.")
        
        with col2:
            # Family Tree Visualization
            st.subheader("🌳 Family Tree Visualization")
            
            if st.session_state.selected_person and st.session_state.family_tree_data:
                render_family_tree(st.session_state.family_tree_data)
            else:
                st.info("Search for and select a person to view their family tree.")
        
        # Chat Section (full width)
        st.markdown("---")
        render_chat_interface()


def render_family_tree(family_tree_data: Dict):
    """Render interactive family tree visualization."""
    try:
        persons = family_tree_data.get('persons', [])
        relationships = family_tree_data.get('relationships', [])
        focal_person = family_tree_data.get('focal_person', {})
        
        if not persons:
            st.info("No family tree data available.")
            return
        
        # Create network graph using Plotly
        fig = create_family_tree_plot(persons, relationships, focal_person)
        
        st.plotly_chart(fig, use_container_width=True, key="family_tree_plot")
        
        # Display statistics
        metadata = family_tree_data.get('metadata', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Persons", metadata.get('total_persons', len(persons)))
        
        with col2:
            st.metric("Relationships", metadata.get('total_relationships', len(relationships)))
        
        with col3:
            st.metric("Generations", metadata.get('max_generations', 4))
            
    except Exception as e:
        st.error(f"Error rendering family tree: {str(e)}")
        logger.error(f"Family tree rendering error: {e}")


def create_family_tree_plot(persons: List[Dict], relationships: List[Dict], focal_person: Dict) -> go.Figure:
    """Create Plotly network graph for family tree visualization."""
    import networkx as nx
    import numpy as np
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add nodes (persons)
    for person in persons:
        G.add_node(
            person['id'],
            name=person.get('display_name', 'Unknown'),
            gender=person.get('gender', 'U'),
            birth_year=person.get('birth_date', '').split('-')[0] if person.get('birth_date') else '',
            death_year=person.get('death_date', '').split('-')[0] if person.get('death_date') else '',
            is_focal=person['id'] == focal_person.get('id')
        )
    
    # Add edges (relationships)
    for rel in relationships:
        if rel['person1_id'] in G.nodes and rel['person2_id'] in G.nodes:
            G.add_edge(
                rel['person1_id'], 
                rel['person2_id'],
                relationship_type=rel.get('relationship_type', 'unknown')
            )
    
    # Calculate layout
    try:
        pos = nx.spring_layout(G, k=3, iterations=50)
    except:
        pos = nx.random_layout(G)
    
    # Extract node and edge data
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    
    node_info = []
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        node_data = G.nodes[node]
        
        # Color by gender
        if node_data['gender'] == 'M':
            color = '#007bff'  # Blue for male
        elif node_data['gender'] == 'F':
            color = '#e91e63'  # Pink for female
        else:
            color = '#28a745'  # Green for unknown
        
        # Size by importance (focal person larger)
        size = 20 if node_data.get('is_focal') else 15
        
        node_colors.append(color)
        node_sizes.append(size)
        
        # Hover info
        life_span = ""
        if node_data['birth_year']:
            life_span = f"({node_data['birth_year']}"
            if node_data['death_year']:
                life_span += f"-{node_data['death_year']})"
            else:
                life_span += "-present)"
        
        node_info.append(f"{node_data['name']}<br>{life_span}")
    
    # Edge traces
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#999'),
        hoverinfo='none',
        mode='lines',
        showlegend=False
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_info,
        text=[G.nodes[node]['name'].split()[0] for node in G.nodes()],  # First name only
        textposition="middle center",
        textfont=dict(color="white", size=10),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='white')
        ),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Family Tree - {focal_person.get('display_name', 'Unknown')}",
        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[ dict(
            text="🔵 Male&nbsp;&nbsp;&nbsp;🩷 Female&nbsp;&nbsp;&nbsp;🟢 Unknown",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002,
            xanchor='left', yanchor='bottom',
            font=dict(size=12)
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        height=500
    )
    
    return fig


def render_chat_interface():
    """Render the chat interface for conversing with family history."""
    st.subheader("💬 Chat with Your Family History")
    
    # Check if API is configured
    api_status = st.session_state.api_client.get_api_key_status()
    
    if not api_status.get('openrouter_api_key_configured', False):
        st.warning("⚠️ OpenRouter API key not configured. Please configure it in the Configuration tab to enable chat functionality.")
        return
    
    # Chat history display
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for i, message in enumerate(st.session_state.chat_history):
                message_class = "user-message" if message['type'] == 'user' else "assistant-message"
                
                st.markdown(f"""
                <div class="chat-message {message_class}">
                    <strong>{'You' if message['type'] == 'user' else '🤖 TreeTalk'}:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="chat-message assistant-message">
                <strong>🤖 TreeTalk:</strong><br>
                Hello! I'm here to help you explore your family history. Ask me anything about your ancestors, family relationships, or genealogical data!
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_message = st.text_area(
                "Ask about your family history...",
                placeholder="e.g., Tell me about John Smith's children, or Who are the oldest ancestors in my tree?",
                height=80,
                label_visibility="collapsed"
            )
        
        with col2:
            st.write("")  # Spacing
            send_button = st.form_submit_button("Send 📤", use_container_width=True)
    
    # Process chat message
    if send_button and user_message.strip():
        # Add user message to history
        st.session_state.chat_history.append({
            'type': 'user',
            'content': user_message,
            'timestamp': datetime.now()
        })
        
        # Show thinking indicator
        with st.spinner("🤔 TreeTalk is thinking..."):
            # Send to AI
            response = st.session_state.api_client.send_chat_message(
                message=user_message,
                session_id=st.session_state.chat_session_id
            )
        
        if response and response.get('ai_message'):
            ai_content = response['ai_message']['content']
            
            # Add AI response to history
            st.session_state.chat_history.append({
                'type': 'assistant',
                'content': ai_content,
                'timestamp': datetime.now()
            })
        else:
            # Add error message
            st.session_state.chat_history.append({
                'type': 'assistant',
                'content': "I apologize, but I encountered an error processing your request. Please try again or check your API configuration.",
                'timestamp': datetime.now()
            })
        
        st.rerun()


def render_configuration_tab():
    """Render the Configuration tab content."""
    st.header("Configuration")
    
    # API Configuration Section
    st.subheader("🔑 OpenRouter API Configuration")
    
    # Get current status
    api_status = st.session_state.api_client.get_api_key_status()
    
    # Status display
    col1, col2 = st.columns(2)
    with col1:
        status_text = "✅ Configured" if api_status.get('openrouter_api_key_configured') else "❌ Not Configured"
        status_class = "status-success" if api_status.get('openrouter_api_key_configured') else "status-error"
        st.markdown(f'<p class="{status_class}">API Key Status: {status_text}</p>', unsafe_allow_html=True)
    
    with col2:
        chat_status = "✅ Available" if api_status.get('chat_available') else "❌ Unavailable"
        chat_class = "status-success" if api_status.get('chat_available') else "status-error"
        st.markdown(f'<p class="{chat_class}">Chat Functionality: {chat_status}</p>', unsafe_allow_html=True)
    
    # Configuration form
    with st.form("api_config_form"):
        st.write("**OpenRouter API Key**")
        api_key_input = st.text_input(
            "Enter your OpenRouter API key:",
            type="password",
            help="Get your API key from https://openrouter.ai/keys"
        )
        
        st.write("**Chat Model Selection**")
        
        # Get available models
        available_models = st.session_state.api_client.get_available_models()
        
        if available_models:
            model_options = {}
            for model in available_models:
                cost_info = f" (${model.get('cost_per_1k_tokens', 0):.3f}/1K tokens)" if model.get('cost_per_1k_tokens') else ""
                display_name = f"{model.get('name', model.get('id'))}{cost_info}"
                model_options[display_name] = model.get('id')
            
            selected_model_display = st.selectbox(
                "Select AI model for chat:",
                options=list(model_options.keys()),
                help="Models are sorted by cost (free/cheaper models first)"
            )
            selected_model = model_options.get(selected_model_display)
        else:
            selected_model = st.text_input(
                "Model name:",
                value="openai/gpt-3.5-turbo",
                help="Enter model name (e.g., openai/gpt-3.5-turbo, anthropic/claude-3-haiku)"
            )
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Configuration", use_container_width=True)
        
        if submitted:
            if api_key_input.strip() or selected_model:
                with st.spinner("Saving configuration..."):
                    result = st.session_state.api_client.set_api_configuration(
                        openrouter_api_key=api_key_input.strip() if api_key_input.strip() else None,
                        default_model=selected_model if selected_model else None
                    )
                
                if result and result.get('success'):
                    st.success("✅ Configuration saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save configuration. Please check your inputs.")
            else:
                st.warning("Please provide at least an API key or model selection.")
    
    # Information section
    st.markdown("---")
    st.subheader("ℹ️ About OpenRouter")
    st.info("""
    **OpenRouter** provides access to multiple AI models through a single API. 
    
    - **Sign up**: Visit [openrouter.ai](https://openrouter.ai) to create an account
    - **Get API key**: Go to [openrouter.ai/keys](https://openrouter.ai/keys) to generate your key
    - **Pricing**: Many models offer free tiers, with pay-per-use pricing for premium models
    - **Models**: Choose from GPT-3.5/4, Claude, Llama, and many other models
    
    Your API key is stored securely and encrypted in the local database.
    """)


def render_gedcom_management_tab():
    """Render the GEDCOM Management tab content."""
    st.header("GEDCOM File Management")
    
    # Upload Section
    st.subheader("📤 Upload New GEDCOM File")
    
    with st.form("gedcom_upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Select a GEDCOM (.ged) file to upload:",
            type=['ged'],
            help="Upload your family tree data in GEDCOM format (maximum 50MB)"
        )
        
        source_name = st.text_input(
            "Source Name (optional):",
            placeholder="e.g., Smith Family Tree, Johnson Lineage",
            help="Give your family tree a descriptive name"
        )
        
        upload_submitted = st.form_submit_button("🚀 Upload & Process", use_container_width=True)
        
        if upload_submitted and uploaded_file:
            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB
                st.error("File size exceeds 50MB limit.")
            else:
                with st.spinner(f"Processing {uploaded_file.name}... This may take a few minutes for large files."):
                    file_bytes = uploaded_file.read()
                    
                    result = st.session_state.api_client.upload_gedcom(
                        file_bytes=file_bytes,
                        filename=uploaded_file.name,
                        source_name=source_name if source_name.strip() else None
                    )
                
                if result and result.get('success'):
                    st.success(f"✅ {result['message']}")
                    
                    # Display import statistics
                    stats = result.get('import_statistics', {})
                    if stats:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Persons Imported", stats.get('persons_imported', 0))
                        with col2:
                            st.metric("Relationships", stats.get('relationships_imported', 0))
                        with col3:
                            st.metric("Errors", len(stats.get('errors', [])))
                        
                        if stats.get('errors'):
                            with st.expander("View Import Errors"):
                                for error in stats['errors']:
                                    st.text(error)
                    
                    st.rerun()
                else:
                    st.error("❌ Failed to upload GEDCOM file. Please check the file format and try again.")
        elif upload_submitted:
            st.warning("Please select a GEDCOM file to upload.")
    
    # Files List Section
    st.markdown("---")
    st.subheader("📋 Uploaded GEDCOM Files")
    
    sources = st.session_state.api_client.get_sources()
    
    if sources:
        # Create DataFrame for better display
        display_data = []
        for source in sources:
            display_data.append({
                'Name': source['name'],
                'Filename': source.get('filename', 'N/A'),
                'Size': f"{source.get('file_size', 0) / (1024*1024):.1f} MB" if source.get('file_size') else 'N/A',
                'Upload Date': source.get('import_date', '').split('T')[0] if source.get('import_date') else 'N/A',
                'Status': source['status'].title(),
                'Persons': source.get('persons_count', 0),
                'ID': source['id']
            })
        
        df = pd.DataFrame(display_data)
        
        # Display table
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1, 1, 1, 1, 1])
            
            with col1:
                st.text(row['Name'])
            with col2:
                st.text(row['Filename'])
            with col3:
                st.text(row['Size'])
            with col4:
                st.text(row['Upload Date'])
            with col5:
                status_class = "status-success" if row['Status'] == 'Completed' else "status-error"
                st.markdown(f'<span class="{status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
            with col6:
                st.text(str(row['Persons']))
            with col7:
                if st.button("🗑️", key=f"delete_{row['ID']}", help=f"Delete {row['Name']}"):
                    # Confirm deletion
                    st.session_state[f"confirm_delete_{row['ID']}"] = True
                    st.rerun()
            
            # Handle deletion confirmation
            if st.session_state.get(f"confirm_delete_{row['ID']}", False):
                st.warning(f"⚠️ Are you sure you want to delete '{row['Name']}' and all associated data?")
                col_yes, col_no = st.columns(2)
                
                with col_yes:
                    if st.button("Yes, Delete", key=f"confirm_yes_{row['ID']}"):
                        # Perform deletion
                        with st.spinner("Deleting..."):
                            try:
                                response = requests.delete(f"{BACKEND_URL}/api/gedcom/sources/{row['ID']}")
                                if response.status_code == 200:
                                    st.success(f"✅ Deleted '{row['Name']}' successfully")
                                    st.session_state[f"confirm_delete_{row['ID']}"] = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete '{row['Name']}': {response.text}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"❌ Error connecting to server: {e}")
                
                with col_no:
                    if st.button("Cancel", key=f"confirm_no_{row['ID']}"):
                        st.session_state[f"confirm_delete_{row['ID']}"] = False
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("No GEDCOM files uploaded yet. Upload your first family tree file above to get started!")


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs([
        "🔍 Data Exploration", 
        "⚙️ Configuration", 
        "📁 GEDCOM Management"
    ])
    
    with tab1:
        render_data_exploration_tab()
    
    with tab2:
        render_configuration_tab()
    
    with tab3:
        render_gedcom_management_tab()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; opacity: 0.6;">
        🌳 TreeTalk v1.0.0 | Built with Streamlit & FastAPI | 
        <a href="https://github.com/your-repo/treetalk" target="_blank">GitHub</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()