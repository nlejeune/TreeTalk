# TreeTalk

## Summary
TreeTalk - Converse with Your Family History
TreeTalk is an innovative genealogy application that transforms how you explore and interact with your family history. 
By combining the power of conversational AI with comprehensive genealogical data management, TreeTalk creates an intelligent, interactive experience that makes family research feel as natural as having a conversation with a knowledgeable family historian.

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
Basic Folder Structure
- src Folder: The source code folder! However, in languages that use headers (or if you have a framework for your application) don’t put those files in here.
- test Folder: Unit tests, integration tests… go here.
- .config Folder: It should local configuration related to setup on local machine.
- .build Folder: This folder should contain all scripts related to build process (PowerShell, Docker compose…).
- dep Folder: This is the directory where all your dependencies should be stored.
- doc Folder: The documentation folder
- res Folder: For all static resources in your project. For example, images.
- samples Folder: Providing “Hello World” & Co code that supports the documentation.
- tools Folder: Convenience directory for your use. Should contain scripts to automate tasks in the project, for example, build scripts, rename scripts. Usually contains .sh, .cmd files for example.

README File: README.md is a file that answer the What, Why and How of the project.
LICENSE File: LICENSE is a file that explains the legal licensing, This project should be under GNU GPLv3 license.
CHANGELOG File: CHANGELOG.md is a file that describes what's happening in the repo. Version number increases, software updates, bug fixes… are examples of the file’s content.

## Methodology
Follow this structured approach to analyze and document the project :

1. **Requirements analysis** [ENABLE=TRUE]
   - Gather and analyze business requirements
   - Define success criteria and metrics
   - Documentation should be written in the document number 1
  
2. **High level architecture documentation** [ENABLE=TRUE]
   - Define target high level architecture
   - High level architecture  should be written in the document number 2 (replace the existing one)

3. **User experience** [ENABLE=TRUE]
   - Gather and analyse UX and UI requirements
   - UI and UX requirement are described in the document number 3
   - Generated an HTML prototype of the UI in the ux_design folder

4. **Code generation** [ENABLE=FALSE]
   - If the folder src exist, use it as your code base and adjust
   - If the folder src does not exist, create it and build the first version of the application in it

5. **Database schema documentation** [ENABLE=FALSE]
   - Document or update if required the database schema in the document number 5
