# TreeTalk

## Summary
TreeTalk - Converse with Your Family History
TreeTalk is an innovative genealogy application that transforms how you explore and interact with your family history. 
By combining the power of conversational AI with comprehensive genealogical data management, TreeTalk creates an intelligent, interactive experience that makes family tree exploration feel as natural as having a conversation with a knowledgeable family historian.

## Instructions
As a solution architect, your role is to analyze the requirements and design a comprehensive solution. Follow these guidelines :

1. Carefully analyse the business needs and technical requirements
2. Design a scalable an maintainable solution focusing on implementation simplicity
3. Document your analysis, decisions, and recommandations in a clear, structured manner
4. Provide detailed specifications that can guide the implementation team
5. Consider security, privacy and ethical implications
6. Follow the methodology steps marked as enabled in sequence, completing each documentation components
7. Reference specific instructions within each document to ensure comprehensive coverage
8. Propose innovative approaches while remaining practical and feasible
9. Highlight potential risks, limitations, and mitigation strategies
10. **Keep documentation detailed but concise** - provide sufficient detail while being brief and to the point
11. **Do not invent content** - If information for a section is not available, note this gap rather than creating fictional details

## Github repository structure
Github Folder Structure
- src Folder: The source code folder! However, in languages that use headers (or if you have a framework for your application) don’t put those files in here.
- test Folder: Unit tests, integration tests… go here.
- .config Folder: It should local configuration related to setup on local machine.
- .build Folder: This folder should contain all scripts related to build process (PowerShell, Docker, Docker compose...).
- dep Folder: This is the directory where all your dependencies should be stored.
- doc Folder: The documentation folder
- res Folder: For all static resources in your project. For example, images.
- tools Folder: Convenience directory for your use. Should contain scripts to automate tasks in the project, for example, build scripts, rename scripts. Usually contains .sh, .cmd files for example.

## Methodology
Follow this structured approach to analyze and document the project :

1. **Requirements analysis** [ENABLE=TRUE]
   - Gather and analyze requirements
   - Define success criteria and metrics
   - Documentation exist in the document number 1
  
2. **High level architecture documentation** [ENABLE=FALSE]
   - Define target high level architecture
   - Document High level architecture in the document number 2 (replace the existing one)

3. **User experience** [ENABLE=FALSE]
   - Gather and analyse UX and UI requirements
   - UI and UX requirement are described in the document number 3
   - Generated an HTML prototype of the UI in the ux_design folder (replace the existing one)

4. **First Code generation** [ENABLE=TRUE]
   - If the folder src does not exist, create it and build the first version of the application in it
   - Technical and functional requirements are described in the document number 1
   - High level architecture is described in the document number 2
   - Use the HTML protype in ux_design folder as the UI template
   - Document properly the code to make it easily understandable by a human (Comment block before each class and function)
   - For each function, create and maintain unit tests
   - Run all unit test at the end to validate the code works properly

5. **Database schema documentation** [ENABLE=TRUE]
   - Document or update if required the database schema in the document number 5