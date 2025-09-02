# 🚀 OpenRouter Integration - TreeChat Demo

**OpenRouter est la solution recommandée** pour TreeChat Demo car elle offre :
- ✅ **Accès unifié** à tous les grands modèles (Claude, GPT-4, Llama, etc.)
- 💰 **Meilleurs prix** que les APIs directes
- 🔄 **Fallback automatique** entre modèles
- 📊 **Dashboard unifié** pour monitoring
- 🎯 **Même qualité** que Claude direct

## 🔧 Configuration Rapide

### 1. Obtenir une clé OpenRouter
1. Créez un compte sur **https://openrouter.ai/**
2. Allez dans **API Keys** : https://openrouter.ai/keys
3. Créez une clé (commence par `sk-or-v1-...`)
4. **Ajoutez des crédits** si nécessaire (gratuit jusqu'à 10$)

### 2. Configuration .env
```bash
cd Demo
cp .env.example .env
# Éditez .env avec vos vraies clés
```

**Configuration Recommandée (.env) :**
```bash
# ===== CONFIGURATION RECOMMANDÉE =====
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-votre-vraie-clé-ici
OPENROUTER_MODEL=anthropic/claude-3-sonnet:beta

# Optionnel: Clé Claude directe en fallback
CLAUDE_API_KEY=sk-ant-api03-votre-clé-claude-si-vous-avez

# Database Configuration (ne pas changer)
POSTGRES_USER=treechat
POSTGRES_PASSWORD=treechat123
POSTGRES_DB=treechat_demo
```

### 3. Redémarrage
```bash
docker-compose build backend
docker-compose up -d
```

## 🎯 Modèles Disponibles

### Modèles Claude (Recommandés)
```bash
# Claude 3 Sonnet (Recommandé - Équilibre qualité/prix)
OPENROUTER_MODEL=anthropic/claude-3-sonnet:beta

# Claude 3 Haiku (Plus rapide et économique)
OPENROUTER_MODEL=anthropic/claude-3-haiku:beta

# Claude 3 Opus (Qualité maximale, plus cher)
OPENROUTER_MODEL=anthropic/claude-3-opus:beta
```

### Alternatives OpenAI
```bash
# GPT-4 Turbo (Alternative performante)
OPENROUTER_MODEL=openai/gpt-4-turbo

# GPT-3.5 Turbo (Économique)
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```

### Modèles Open Source
```bash
# Llama 3 70B (Gratuit, très performant)
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct

# Mistral 7B (Ultra-rapide)
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
```

## 💰 Coûts Comparatifs (approximatifs)

| Modèle | Prix / 1M tokens | Qualité | Vitesse | Recommandé pour |
|--------|------------------|---------|---------|-----------------|
| **Claude 3 Sonnet** | ~$3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Production** |
| Claude 3 Haiku | ~$1 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Développement |
| GPT-4 Turbo | ~$10 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Alternative |
| Llama 3 70B | **Gratuit** | ⭐⭐⭐⭐ | ⭐⭐⭐ | Tests/Demo |

## 🔄 Système de Fallback

L'application utilise un **système de fallback intelligent** :

1. **Provider préféré** (défini par `AI_PROVIDER`)
2. **Fallback automatique** vers l'autre provider si erreur
3. **Mode démo** si aucune clé API disponible

### Exemple de Configuration Robuste
```bash
# Configuration maximale
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-votre-clé-openrouter
CLAUDE_API_KEY=sk-ant-api03-votre-clé-claude
OPENROUTER_MODEL=anthropic/claude-3-sonnet:beta
```

**Comportement :**
- Utilise OpenRouter en priorité
- Si OpenRouter échoue → Fallback vers Claude direct
- Si les deux échouent → Mode démo avec réponses programmées

## 🏗️ Configurations par Environnement

### 🧪 Développement/Tests
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct  # Gratuit
```

### 🚀 Production
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=anthropic/claude-3-sonnet:beta
CLAUDE_API_KEY=sk-ant-api03-xxx  # Fallback
```

### 💸 Économique
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=anthropic/claude-3-haiku:beta
```

## 📊 Monitoring et Dashboard

### OpenRouter Dashboard
- **Usage** : https://openrouter.ai/activity
- **Crédits** : https://openrouter.ai/credits
- **Modèles** : https://openrouter.ai/docs#models

### Logs Application
```bash
# Vérifier le provider actif
docker-compose logs backend | grep -E "(✅|❌|ℹ️)"

# Messages typiques
✅ OpenRouter API initialized successfully with model: anthropic/claude-3-sonnet:beta
✅ Fallback to Claude API successful
ℹ️  No AI API configured, using fallback responses
```

## 🔧 Debug et Dépannage

### Vérifier la Configuration
```bash
# Variables d'environnement dans le conteneur
docker-compose exec backend env | grep -E "(AI_|OPENROUTER|CLAUDE)"

# Test de connectivité
docker-compose exec backend python -c "
import os
print('AI_PROVIDER:', os.getenv('AI_PROVIDER'))
print('OpenRouter Key:', 'Configuré' if os.getenv('OPENROUTER_API_KEY') else 'Manquant')
print('Claude Key:', 'Configuré' if os.getenv('CLAUDE_API_KEY') else 'Manquant')
"
```

### Problèmes Courants

#### 1. "No AI API configured"
**Cause :** Aucune clé API valide trouvée
**Solution :**
```bash
# Vérifiez le .env existe et contient les bonnes clés
cat .env
# Redémarrez après modification
docker-compose restart backend
```

#### 2. "Failed to initialize OpenRouter API"
**Causes possibles :**
- Clé API invalide ou expirée
- Problème réseau
- Crédits épuisés

**Solutions :**
```bash
# Vérifiez votre clé sur https://openrouter.ai/keys
# Vérifiez vos crédits sur https://openrouter.ai/credits
# Testez en mode Claude fallback
AI_PROVIDER=claude
```

#### 3. Réponses étranges ou erreurs
**Cause :** Modèle mal configuré
**Solution :**
```bash
# Utilisez un modèle testé et supporté
OPENROUTER_MODEL=anthropic/claude-3-sonnet:beta
```

## 🚀 Avantages d'OpenRouter

### 🔄 Flexibilité
- **Changement de modèle** en 1 variable
- **Tests A/B** faciles entre modèles
- **Migration** sans code

### 💰 Économies
- **Prix négociés** avec les providers
- **Pas de frais cachés**
- **Facturation unifiée**

### 📊 Observabilité
- **Dashboard unifié** pour tous les modèles
- **Métriques détaillées** par modèle
- **Alertes** sur les quotas

### 🔒 Fiabilité
- **Infrastructure redondante**
- **Fallback automatique** entre providers
- **SLA professionnel**

---

**Avec OpenRouter, TreeChat Demo devient un laboratoire IA complet ! 🧪🚀**

## Next Steps

1. **Créez votre compte OpenRouter** : https://openrouter.ai/
2. **Ajoutez $5-10 de crédits** pour commencer
3. **Configurez votre .env** avec la clé OpenRouter
4. **Expérimentez** avec différents modèles !

L'avenir de TreeChat est multi-modèles grâce à OpenRouter ! ⚡