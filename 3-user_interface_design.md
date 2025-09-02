# TreeTalk UX Design

## Menu
The menu is horizontal at the top of the screen, here is the structure
- Data exploration tab (main page)
- Configuration tab (configuration of APIs key)
- GEDCOM files management section (page to import Gedcom files into the database and delete Gedcom files from the database)

## Main page - Data exploration
- A Drop down menu to select the Gedcom file to explore (top of screen)
- A family members section with a search by name text box and the lis of family members matching the research, when you click on a family member in this section, it will adjust the Family Tree Visualization section
- Family Tree Visualization section where you can visualize the family member and relationships with other members. Show only 4 layers of relations
- A Chat with Your Family History section at the botom of the screen, A ChatGPT like interface to discuss with Openrouter API based on the postgresql data

## Configuration
- A screen to configure the Openrouter API. It will store the key in an encrypted file.
- The screen should enable the modification of the API key

## GEDCOM files management section
- A section to enable the upload of GEDCOM files
- A section to see the list of gedcom files already uploaded
- In the UI, allow the user to delete an already uploaded file (it will also delete all related entries in the database)
