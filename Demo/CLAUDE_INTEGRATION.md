# 🤖 Intégration IA - TreeChat Demo
## Claude API & OpenRouter Support

## Configuration

### 1. Obtenir une clé API Claude
1. Créez un compte sur [Anthropic Console](https://console.anthropic.com/)
2. Générez une clé API
3. La clé commence par `sk-ant-api03-...`

### 2. Configuration Locale

#### Créer le fichier .env
```bash
cd Demo
cp .env.example .env
```

#### Éditer .env avec votre clé API
```bash
# Claude API Configuration
CLAUDE_API_KEY=sk-ant-api03-votre-vraie-clé-ici

# Database Configuration (Docker defaults)
POSTGRES_USER=treechat
POSTGRES_PASSWORD=treechat123
POSTGRES_DB=treechat_demo

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=1
PORT=8000
```

### 3. Redémarrer l'Application
```bash
# Reconstruire avec les nouvelles dépendances
docker-compose build backend

# Redémarrer avec les variables d'environnement
docker-compose up -d
```

## Fonctionnement

### Mode Hybride
L'application fonctionne en **mode hybride** :
- ✅ **Avec clé API** : Utilise Claude pour des réponses intelligentes
- 🔄 **Sans clé API** : Utilise les réponses programmées (mode demo)

### Vérification du Statut
Consultez les logs du backend pour voir le statut :
```bash
docker-compose logs backend | grep Claude
```

**Messages possibles :**
- `✅ Claude API initialized successfully` → API active
- `ℹ️  No Claude API key found, using fallback responses` → Mode demo

## Fonctionnalités Claude

### 1. Contexte Familial Intelligent
Claude reçoit automatiquement :
- **Tous les membres** de la famille Dupont
- **Relations familiales** (parents, enfants, conjoints)
- **Dates importantes** (naissances, décès)
- **Historique de conversation** (10 derniers messages)

### 2. Réponses Contextuelles
- **Questions précises** : "Qui sont les enfants de Pierre ?"
- **Navigation temporelle** : "Parle-moi de la génération née dans les années 1950"
- **Relations complexes** : "Comment Emma et Thomas sont-ils liés ?"
- **Histoire familiale** : "Raconte-moi l'histoire de Jean Dupont"

### 3. Suggestions Intelligentes
Claude peut proposer des questions de suivi pertinentes basées sur le contexte.

## Exemples de Requêtes

### Questions Directes
```
"Qui est Jean Dupont ?"
"Combien d'enfants avait Marie Durand ?"
"Qui sont les petits-enfants de Jean ?"
```

### Questions Complexes
```
"Raconte-moi l'histoire de cette famille sur 4 générations"
"Qui a vécu le plus longtemps dans cette famille ?"
"Y a-t-il des membres de la famille encore vivants ?"
```

### Navigation Relationnelle
```
"Comment Pierre et Isabelle sont-ils liés ?"
"Qui sont les beaux-parents d'Anne Martin ?"
"Montre-moi toute la descendance de Jean Dupont"
```

## Architecture Technique

### Système de Prompts
```python
system_prompt = """
Tu es un assistant spécialisé dans l'exploration d'histoires familiales.
Tu aides les utilisateurs à découvrir et comprendre leur arbre 
généalogique de manière conversationnelle et engageante.

CONTEXTE FAMILIAL:
[Données familiales complètes]

INSTRUCTIONS:
1. Réponds en français de manière naturelle
2. Utilise les données familiales pour répondre précisément
3. Suggère des questions alternatives si pas d'info
4. Sois enthousiaste et aide à explorer
5. Formate les dates lisiblement
6. Mentionne les relations familiales
"""
```

### Gestion des Erreurs
- **Fallback automatique** vers les réponses programmées
- **Logging détaillé** des erreurs API
- **Continuation transparente** du service

### Limitation des Tokens
- **Max 1000 tokens** par réponse
- **Contexte optimisé** (10 derniers messages)
- **Données essentielles** seulement

## Coûts et Usage

### Estimation des Coûts Claude API
- **Modèle** : Claude-3-Sonnet
- **Coût approximatif** : ~$0.003 par requête moyenne
- **Usage demo** : Très faible coût

### Monitoring
Surveillez votre usage sur [Anthropic Console](https://console.anthropic.com/usage)

## Développement et Debug

### Tester l'API
```bash
# Vérifier les logs
docker-compose logs backend -f

# Tester une requête
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qui est Jean Dupont ?"}'
```

### Variables d'Environnement Debug
```bash
# Afficher les variables dans le conteneur
docker-compose exec backend env | grep CLAUDE

# Tester l'import Python
docker-compose exec backend python -c "import anthropic; print('OK')"
```

### Mode Développement
Pour développer localement sans Docker :
```bash
cd backend
pip install -r requirements.txt
export CLAUDE_API_KEY="your-key"
python app.py
```

## Sécurité

### Protection de la Clé API
- ✅ **Fichier .env** non versionné (.gitignore)
- ✅ **Variables d'environnement** Docker
- ✅ **Pas de clé hardcodée** dans le code
- ⚠️  **Ne jamais committer** la vraie clé

### Bonnes Pratiques
```bash
# Mauvais ❌
CLAUDE_API_KEY=sk-ant-api03-abc123  # Dans le code source

# Bon ✅
export CLAUDE_API_KEY="$(cat ~/.claude_key)"  # Variable d'environnement
```

## Dépannage

### Problèmes Courants

#### 1. "No Claude API key found"
- Vérifiez le fichier `.env` existe
- Vérifiez la variable `CLAUDE_API_KEY` est définie
- Redémarrez le conteneur : `docker-compose restart backend`

#### 2. "Failed to initialize Claude API"
- Clé API invalide ou expirée
- Problème de connexion internet
- Quotas API dépassés

#### 3. Réponses incohérentes
- Mode fallback activé (pas d'API key)
- Erreur temporaire de l'API
- Contexte familial mal formaté

### Commands de Debug
```bash
# Vérifier les services
docker-compose ps

# Logs détaillés
docker-compose logs backend | grep -E "(Claude|API|Error)"

# Shell dans le conteneur
docker-compose exec backend bash

# Test de la clé API
docker-compose exec backend python -c "
import os, anthropic
key = os.getenv('CLAUDE_API_KEY')
print('Key found:', bool(key))
if key: client = anthropic.Anthropic(api_key=key); print('Client OK')
"
```

---

**L'intégration Claude transforme TreeChat Demo en véritable assistant généalogique intelligent ! 🚀**