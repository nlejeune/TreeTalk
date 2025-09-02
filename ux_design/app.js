// TreeTalk UI JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Tab navigation
    initializeTabNavigation();
    
    // Family tree visualization
    initializeFamilyTree();
    
    // Chat functionality
    initializeChat();
    
    // GEDCOM file handling
    initializeGedcomManagement();
    
    // Configuration management
    initializeConfiguration();
    
    // Person search
    initializePersonSearch();
}

// Tab Navigation
function initializeTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and tabs
            navButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            // Add active class to clicked button and corresponding tab
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// Family Tree Visualization
function initializeFamilyTree() {
    const svg = d3.select('#family-tree-svg');
    const container = d3.select('#family-tree-container');
    
    // Sample family data
    const familyData = {
        name: "John Smith",
        birth: "1850",
        death: "1920",
        children: [
            {
                name: "Robert Smith",
                birth: "1875",
                death: "1950",
                children: [
                    { name: "James Smith", birth: "1905", death: "1980" },
                    { name: "William Smith", birth: "1908", death: "1985" }
                ]
            },
            {
                name: "Mary Johnson",
                birth: "1878",
                death: "1955",
                children: [
                    { name: "Elizabeth Johnson", birth: "1902", death: "1975" }
                ]
            }
        ]
    };
    
    // Create tree layout
    const treeLayout = d3.tree().size([400, 300]);
    const root = d3.hierarchy(familyData);
    treeLayout(root);
    
    // Draw tree
    drawFamilyTree(svg, root);
    
    // Zoom and pan functionality
    const zoom = d3.zoom()
        .scaleExtent([0.5, 2])
        .on('zoom', function(event) {
            svg.select('g').attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Tree control buttons
    document.querySelector('.zoom-in').addEventListener('click', function() {
        svg.transition().call(zoom.scaleBy, 1.5);
    });
    
    document.querySelector('.zoom-out').addEventListener('click', function() {
        svg.transition().call(zoom.scaleBy, 1/1.5);
    });
    
    document.querySelector('.center-view').addEventListener('click', function() {
        svg.transition().call(zoom.transform, d3.zoomIdentity);
    });
}

function drawFamilyTree(svg, root) {
    const g = svg.append('g').attr('transform', 'translate(50, 50)');
    
    // Links
    g.selectAll('.link')
        .data(root.links())
        .enter()
        .append('path')
        .attr('class', 'link')
        .attr('d', d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y))
        .attr('fill', 'none')
        .attr('stroke', '#3182ce')
        .attr('stroke-width', 2);
    
    // Nodes
    const nodes = g.selectAll('.node')
        .data(root.descendants())
        .enter()
        .append('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
    
    // Node circles
    nodes.append('circle')
        .attr('r', 20)
        .attr('fill', '#3182ce')
        .attr('stroke', '#2c5282')
        .attr('stroke-width', 2);
    
    // Node labels
    nodes.append('text')
        .attr('dy', 35)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', '#2d3748')
        .text(d => d.data.name);
    
    // Birth/death dates
    nodes.append('text')
        .attr('dy', 50)
        .attr('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('fill', '#718096')
        .text(d => `(${d.data.birth}-${d.data.death})`);
}

// Chat Functionality
function initializeChat() {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');
    
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, 'user');
        
        // Clear input
        chatInput.value = '';
        
        // Simulate AI response
        setTimeout(() => {
            const responses = [
                "John Smith was born in 1850 and passed away in 1920. He had two children: Robert Smith and Mary Johnson.",
                "Based on your family data, I can see that Robert Smith was the son of John and Mary Smith. He lived from 1875 to 1950.",
                "Mary Johnson (née Smith) was born in 1878. She married into the Johnson family and had one daughter, Elizabeth.",
                "The Smith family tree shows 3 generations of descendants from John Smith. Would you like to know more about any specific family member?"
            ];
            
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            addMessage(randomResponse, 'assistant');
        }, 1000);
    }
    
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function addMessage(content, type) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const messageText = document.createElement('p');
    messageText.textContent = content;
    messageDiv.appendChild(messageText);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// GEDCOM File Management
function initializeGedcomManagement() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.querySelector('.browse-btn');
    
    // File upload drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#3182ce';
        this.style.backgroundColor = '#ebf8ff';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = '#cbd5e0';
        this.style.backgroundColor = '#f8f9fa';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        const files = e.dataTransfer.files;
        handleFileUpload(files[0]);
    });
    
    browseBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileUpload(this.files[0]);
        }
    });
    
    // Delete file buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this GEDCOM file? This will also remove all associated family data from the database.')) {
                // Simulate file deletion
                const fileItem = this.closest('.file-item');
                fileItem.style.opacity = '0.5';
                setTimeout(() => {
                    fileItem.remove();
                }, 300);
            }
        });
    });
}

function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith('.ged') && !file.name.toLowerCase().endsWith('.gedcom')) {
        alert('Please upload a valid GEDCOM file (.ged or .gedcom)');
        return;
    }
    
    // Show progress
    const progressDiv = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    progressDiv.style.display = 'block';
    
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress > 100) progress = 100;
        
        progressFill.style.width = progress + '%';
        progressText.textContent = Math.round(progress) + '%';
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                progressDiv.style.display = 'none';
                alert('GEDCOM file uploaded and processed successfully!');
                // In a real app, this would refresh the file list
            }, 1000);
        }
    }, 200);
}

// Configuration Management
function initializeConfiguration() {
    const saveButtons = document.querySelectorAll('.save-config');
    const toggleButtons = document.querySelectorAll('.toggle-visibility');
    
    saveButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Simulate saving configuration
            this.textContent = 'Saving...';
            this.disabled = true;
            
            setTimeout(() => {
                this.textContent = 'Saved!';
                this.style.backgroundColor = '#48bb78';
                
                // Update status indicators
                const statusIndicators = document.querySelectorAll('.status-indicator');
                statusIndicators.forEach(indicator => {
                    if (indicator.textContent === 'Not Configured') {
                        indicator.textContent = 'Configured';
                        indicator.className = 'status-indicator configured';
                    }
                });
                
                setTimeout(() => {
                    this.textContent = 'Save Configuration';
                    this.disabled = false;
                    this.style.backgroundColor = '';
                }, 2000);
            }, 1000);
        });
    });
    
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            
            if (input.type === 'password') {
                input.type = 'text';
                this.textContent = '🙈';
            } else {
                input.type = 'password';
                this.textContent = '👁️';
            }
        });
    });
}

// Person Search
function initializePersonSearch() {
    const searchInput = document.getElementById('person-search');
    const personItems = document.querySelectorAll('.person-item');
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        
        personItems.forEach(item => {
            const personName = item.querySelector('.person-name').textContent.toLowerCase();
            if (personName.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Person selection
    personItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove previous selection
            personItems.forEach(p => p.classList.remove('selected'));
            
            // Add selection to clicked item
            this.classList.add('selected');
            
            // Update family tree (in a real app, this would load the person's tree)
            const personName = this.querySelector('.person-name').textContent;
            console.log(`Selected person: ${personName}`);
            
            // Add visual feedback
            this.style.backgroundColor = '#ebf8ff';
            setTimeout(() => {
                this.style.backgroundColor = '';
            }, 2000);
        });
    });
}

// Add some CSS for selected person
const style = document.createElement('style');
style.textContent = `
    .person-item.selected {
        border-color: #3182ce !important;
        background-color: #ebf8ff !important;
    }
`;
document.head.appendChild(style);