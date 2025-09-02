# TreeChat Demo - Backend

## Architecture

Le backend est une API REST construite avec Flask qui fournit les données familiales et les fonctionnalités de chat conversationnel.

### Structure des fichiers

```
backend/
├── app.py                 # Point d'entrée principal de l'application
├── requirements.txt       # Dépendances Python
├── Dockerfile            # Configuration Docker
└── app/
    ├── __init__.py       # Module Python
    ├── models/           # Modèles de données
    │   ├── __init__.py
    │   └── person.py     # Modèle Person
    ├── services/         # Services métier
    │   ├── __init__.py
    │   ├── family_data.py    # Service de données familiales
    │   └── chat_service.py   # Service de chat conversationnel
    └── routes/           # Routes API
        ├── __init__.py
        └── api.py        # Endpoints REST
```

## API Endpoints

### Health Check
- **GET** `/api/health` - Vérification de l'état du service

### Gestion des Personnes
- **GET** `/api/persons` - Récupère toutes les personnes
- **GET** `/api/persons/<person_id>` - Récupère une personne spécifique
- **GET** `/api/persons/search?q=<query>` - Recherche de personnes par nom
- **GET** `/api/persons/<person_id>/ancestors` - Récupère les ancêtres
- **GET** `/api/persons/<person_id>/descendants` - Récupère les descendants

### Arbre Généalogique
- **GET** `/api/family-tree` - Récupère les données de l'arbre (nodes + links pour D3.js)

### Chat Conversationnel
- **POST** `/api/chat` - Envoie un message et reçoit une réponse
- **GET** `/api/chat/history` - Récupère l'historique des conversations
- **DELETE** `/api/chat/history` - Efface l'historique

### Sources de Données
- **GET** `/api/sources` - Liste les sources de données disponibles
- **POST** `/api/sources/<source_id>/sync` - Déclenche la synchronisation

## Services

### FamilyDataService (`app/services/family_data.py`)
Gère toutes les opérations liées aux données familiales :
- Chargement des données de démonstration
- Recherche et filtrage des personnes
- Construction de l'arbre généalogique pour D3.js
- Navigation dans les relations familiales

### ChatService (`app/services/chat_service.py`)
Fournit les fonctionnalités de chat conversationnel :
- Traitement des messages utilisateur
- Génération de réponses contextuelles
- Gestion de l'historique des conversations
- Suggestions de questions

## Modèles

### Person (`app/models/person.py`)
Représente une personne dans l'arbre généalogique avec :
- Informations personnelles (nom, dates, genre)
- Relations familiales (parents, enfants, conjoints)
- Méthodes de sérialisation JSON

## WebSocket Support

L'application utilise Flask-SocketIO pour la communication temps réel :
- **connect** - Connexion d'un client
- **disconnect** - Déconnexion d'un client  
- **chat_message** - Messages de chat en temps réel

## Configuration

### Variables d'environnement
- `PORT` : Port d'écoute (défaut: 8000)
- `SECRET_KEY` : Clé secrète Flask

### CORS
Configuration CORS pour autoriser les requêtes depuis le frontend (localhost:3000).

## Données de Démonstration

L'application utilise des données de démonstration de la famille Dupont avec :
- 10 personnes sur 4 générations
- Relations parents-enfants et mariages
- Données historiques réalistes (1920-2025)

## Démarrage

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement du serveur
python app.py
```

Le serveur démarre sur http://localhost:8000 avec les endpoints documentés ci-dessus.