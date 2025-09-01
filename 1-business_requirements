# Requis de l'application TreeChat


## Sommaire executif
TreeChat est un serveur généalogique innovant basé sur le protocole MCP (Model Context Protocol) qui transforme la façon dont vous explorez et interagissez avec votre histoire familiale. 
En combinant la puissance de l’intelligence artificielle conversationnelle avec une gestion complète des données généalogiques, TreeChat crée une expérience intelligente et interactive qui rend la recherche familiale aussi naturelle qu’une conversation avec un historien familial expérimenté.

## 1. Requis fonctionnels

1. L'application pourra avoir pour source de données différents intrants :
    - Upload manuel de fichier GEDCOM
    - API du site FamilySearch
2. L'application doit avoir un serveur MCP interne pour exposer ses informations à des LLM externes dans le but d'offrir une fonctionnalité de chat
3. L'application est bâtie en plusieurs sections :
    Section 1 : Gestion des sources de données : Import local de données (GEDCOM), Connectivité avec des sources externes (exemple : API FamilySearch)
    Section 2 : Fenêtre de chat type ChatGPT pour discuter avec ses données

## 2. Requis techniques

1. La base de donnée sera une base de donnée Postgresql
2. Le language de programmation pour le backend est python
3. Le language de programmation pour le frontend est Javascript avec le framework React
4. L'application sera déployée sur docker

## 3. Backlog (Epic et user stories)

### Épique 1 : Gestion des sources de données - But : Permettre à l’utilisateur de charger et connecter ses données généalogiques.
- User story 1.1 : **En tant qu’utilisateur**, je veux pouvoir uploader un fichier GEDCOM afin d’importer mon arbre généalogique dans l’application.
- Critères d’acceptation :
    - L’upload accepte uniquement les formats .ged.
    - L’utilisateur est notifié en cas de succès ou d’échec.
    - Les données sont stockées en base Postgres.
    - Connexion à FamilySearch

- User story 1.2 : **En tant qu’utilisateur**, je veux connecter mon compte FamilySearch via leur API pour synchroniser mes données familiales.
- Critères d’acceptation :
    - Authentification OAuth sécurisée.
    - Synchronisation initiale des données.
    - Possibilité de lancer une resynchronisation manuelle.

- User story 1.3 : **En tant qu’utilisateur**, je veux voir et gérer toutes mes sources de données (GEDCOM importés, API connectées) depuis une interface unique.
- Critères d’acceptation :
    - Tableau de bord listant les sources.
    - Possibilité de supprimer une source.
    - Statut de synchronisation visible (date du dernier update, succès/erreur).

### Épique 2 : Exploration des données familiales - But : Permettre une navigation intuitive dans l’arbre généalogique.
- User story 2.1 : **En tant qu’utilisateur**, je veux naviguer dans mon arbre familial pour explorer mes ancêtres et descendants.
- Critères d’acceptation :
    - Affichage graphique interactif (zoom, déplacement).
    - Chaque personne cliquable avec fiche détaillée.
    - Recherche de personnes

- User story 2.1 : **En tant qu’utilisateur**, je veux chercher un ancêtre par nom afin de le retrouver rapidement.
- Critères d’acceptation :
    - Champ de recherche avec autocomplétion.
    - Résultats listant les correspondances exactes et proches.

### Épique 3 : Chat avec ses données familiales (TreeChat) - But : Offrir une expérience de conversation naturelle avec l’histoire familiale.
- User story 3.1 : **En tant qu’utilisateur**, je veux poser des questions en langage naturel pour explorer mon arbre généalogique.
- Critères d’acceptation :
    - Interface de chat type ChatGPT.
    - Historique des conversations conservé.

- User story 3.2 : **En tant qu’utilisateur**, je veux que les réponses du chatbot soient basées uniquement sur mes données familiales importées.
- Critères d’acceptation :
    - Le MCP interne transmet uniquement les données pertinentes au LLM.
    - Les réponses citent les sources (GEDCOM, FamilySearch).
    - Exploration guidée

- User story 3.3 : **En tant qu’utilisateur**, je veux que le chatbot me propose des questions connexes (ex. "Voulez-vous en savoir plus sur les descendants de Jean Dupont ?").
- Critères d’acceptation :
    - Suggestions automatiques affichées sous chaque réponse.

### Épique 4 : Infrastructure et intégration MCP - But : Rendre TreeChat extensible et compatible avec d’autres LLM.
- User story 4.1 : **En tant que développeur**, je veux que l’application expose ses données via un serveur MCP interne afin qu’un LLM externe puisse s’y connecter.
- Critères d’acceptation :
    - Endpoints REST/WS documentés.
    - Authentification sécurisée.

- User story 4.2 : **En tant qu’administrateur**, je veux que l’application soit déployable avec Docker pour simplifier l’installation et la portabilité.
- Critères d’acceptation :
    - Dockerfile pour backend et frontend.
    - docker-compose.yaml pour orchestrer Postgres, backend, frontend.
    - Base de données PostgreSQL

- User story 4.3 : **En tant que développeur**, je veux stocker toutes les données généalogiques dans PostgreSQL afin d’avoir une base robuste et relationnelle.
- Critères d’acceptation :
    - Schéma documenté (personnes, relations, sources).
    - Scripts de migration inclus.