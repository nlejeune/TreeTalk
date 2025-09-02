# TreeTalk UX Design

## UX

### Menu
The menu is horizontal at the top of the screen, here is the structure
- Data exploration tab (main page)
- Configuration tab (configuration of APIs key)
- GEDCOM files management section (page to import Gedcom files into the database and delete Gedcom files from the database)

### Main page - Data exploration
A Drop down menu to select the Gedcom file to explore (top of screen)

#### Family members section - Search and select family member
- A search by name text box
- A dynamic list of family members matching the research, when you click on a family member in this section, it will adjust the Family Tree Visualization section

#### Family Tree Visualization section where you can visualize the family member and relationships with other members. 
- Use streamlit-d3graph component
- Show only 4 layers of relations
- Color visuals in blue for men, pink for women and green for undefined sex
- parents-children relation are plain lines
- mariage relation are doted lines
- 

#### 'Chat with Your Family History' section
- positionned at the botom of the screen
- A ChatGPT like interface to discuss with your date (leverage Openrouter API and the postgresql data)

### Configuration
- A screen to configure the Openrouter API. It will store the key in an encrypted file.
- The screen should enable the modification of the API key

### GEDCOM files management section
- A section to enable the upload of GEDCOM files
- A section to see the list of gedcom files already uploaded
- In the UI, allow the user to delete an already uploaded file (it will also delete all related entries in the database)

## Website mockup
Generate the website mockup in pure HTML but based on component from the framework described in 1-application_requirements.md