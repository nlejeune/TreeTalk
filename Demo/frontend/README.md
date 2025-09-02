# TreeChat Demo - Frontend

## Architecture

Interface utilisateur React moderne avec visualisation D3.js pour l'exploration interactive d'arbres généalogiques et chat conversationnel.

### Structure des fichiers

```
frontend/
├── public/               # Fichiers statiques
├── src/
│   ├── index.js         # Point d'entrée React
│   ├── index.css        # Styles globaux
│   ├── App.js           # Composant principal
│   └── components/      # Composants React
│       ├── FamilyTree.js    # Visualisation D3.js de l'arbre
│       ├── Chat.js          # Interface de chat
│       ├── PersonSearch.js  # Recherche de personnes
│       └── DataSources.js   # Gestion des sources
├── package.json         # Configuration npm
└── Dockerfile          # Configuration Docker
```

## Composants Principaux

### App.js
**Responsabilités :**
- Gestion de l'état global de l'application
- Chargement initial des données familiales
- Coordination entre les composants
- Gestion des erreurs et du loading

**États clés :**
- `familyData` : Données de l'arbre (nodes + links)
- `selectedPerson` : Personne actuellement sélectionnée
- `loading` : État de chargement
- `error` : Messages d'erreur

### FamilyTree.js (`/components/FamilyTree.js`)
**Visualisation interactive D3.js de l'arbre généalogique**

**Fonctionnalités :**
- Rendu force-directed graph avec D3.js
- Zoom et pan interactifs
- Drag & drop des nœuds
- Couleurs différenciées par genre
- Tooltips informatifs au survol
- Légende explicative
- Sélection de personnes par clic

**Props :**
- `data` : Données de l'arbre (nodes + links)
- `onPersonSelect` : Callback de sélection
- `selectedPerson` : Personne sélectionnée

**Types de liens :**
- `parent-child` : Relations de filiation (gris)
- `spouse` : Relations matrimoniales (rouge, pointillés)

### Chat.js (`/components/Chat.js`)
**Interface de chat conversationnel pour explorer l'histoire familiale**

**Fonctionnalités :**
- Messages utilisateur et assistant
- Suggestions de questions
- Auto-scroll vers les nouveaux messages
- Intégration avec la sélection de personnes
- Historique des conversations
- Effacer l'historique

**États :**
- `messages` : Historique des messages
- `inputValue` : Message en cours de saisie
- `isLoading` : Indicateur de traitement

**API :**
- POST `/api/chat` : Envoie des messages
- WebSocket support pour temps réel

### PersonSearch.js (`/components/PersonSearch.js`)
**Recherche et navigation dans les membres de la famille**

**Fonctionnalités :**
- Recherche en temps réel par nom
- Affichage de tous les membres
- Informations détaillées (dates, lieux)
- Icônes par genre
- Sélection interactive

**API :**
- GET `/api/persons` : Liste complète
- GET `/api/persons/search?q=<query>` : Recherche

### DataSources.js (`/components/DataSources.js`)
**Gestion des sources de données genealogiques**

**Fonctionnalités :**
- Affichage des sources connectées
- Statuts de synchronisation
- Déclenchement de syncs manuelles
- Gestion des connexions

**Types de sources :**
- GEDCOM (📄) : Fichiers genealogiques
- FamilySearch (🌐) : Service en ligne

## Styles et Design

### Design System
- **Couleurs principales :**
  - Hommes : `#4299e1` (bleu)
  - Femmes : `#ed64a6` (rose)
  - Sélection : `#667eea` (violet)
  - Texte : `#2d3748` (gris foncé)

- **Layout :**
  - Sidebar : Recherche + Sources (300px)
  - Main panel : Arbre + Chat (flex)
  - Responsive design

### CSS Classes principales
- `.app` : Container principal
- `.sidebar` : Panneau latéral
- `.main-panel` : Zone principale
- `.panel` : Cartes individuelles
- `.tree-container` : Container SVG
- `.chat-container` : Interface chat

## Configuration API

### Environnements
```javascript
// Development (Docker)
const apiUrl = 'http://localhost:8000/api/endpoint'

// Production
const apiUrl = '/api/endpoint' // Via proxy
```

### Proxy Configuration
```json
// package.json
{
  "proxy": "http://localhost:8000"
}
```

## Intégrations

### D3.js
- Force simulation pour le layout automatique
- Gestion des interactions (zoom, drag, hover)
- Rendu SVG performant
- Animations fluides

### API Calls
Toutes les requêtes API utilisent `fetch()` avec gestion d'erreurs et états de chargement.

## Scripts disponibles

```bash
# Développement
npm start           # Démarre sur http://localhost:3000

# Production
npm run build       # Build optimisé
npm test            # Tests unitaires
npm run eject       # Éjecte la configuration
```

## Fonctionnalités Avancées

### Interactions
- **Click** : Sélectionne une personne
- **Drag** : Déplace les nœuds
- **Scroll** : Zoom in/out
- **Hover** : Affiche tooltip

### Navigation
- Sélection depuis l'arbre → Met à jour le chat
- Sélection depuis la recherche → Met à jour l'arbre
- Messages du chat → Suggère des actions

### Performance
- Nettoyage automatique des tooltips
- Gestion optimisée des re-renders React
- Simulation D3.js avec contrôle du cycle de vie