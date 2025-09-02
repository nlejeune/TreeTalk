# TreeChat Demo - Configuration Docker

## Architecture Docker

L'application TreeChat Demo utilise Docker Compose pour orchestrer 3 services :

### Services

#### 1. Database (`db`)
**Image :** `postgres:15-alpine`
**Port :** `5432`
**Configuration :**
```yaml
environment:
  POSTGRES_USER: treechat_user
  POSTGRES_PASSWORD: treechat_password
  POSTGRES_DB: treechat_demo
volumes:
  - postgres_data:/var/lib/postgresql/data
```

**Rôle :** Base de données PostgreSQL pour stocker les données familiales (prête pour l'intégration future).

#### 2. Backend (`backend`)
**Image :** `demo-backend` (build local)
**Port :** `8000`
**Dockerfile :**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

**Dépendances :** Base de données (depends_on: db)

#### 3. Frontend (`frontend`) 
**Image :** `demo-frontend` (build local)
**Port :** `3000`
**Dockerfile :**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]
```

## Configuration docker-compose.yml

### Version et Services
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: treechat_user
      POSTGRES_PASSWORD: treechat_password
      POSTGRES_DB: treechat_demo
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://treechat_user:treechat_password@db:5432/treechat_demo

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Réseau Docker

### Communication Inter-Services
- **Frontend → Backend :** `http://backend:8000` (réseau Docker interne)
- **Backend → Database :** `postgresql://treechat_user:treechat_password@db:5432/treechat_demo`
- **Host → Services :** Via port mapping (3000, 8000, 5432)

### Résolution DNS
Docker Compose crée automatiquement un réseau avec résolution DNS par nom de service :
- `db` résout vers le conteneur PostgreSQL
- `backend` résout vers le conteneur Flask
- `frontend` résout vers le conteneur React

## Volumes

### Persistance des Données
```yaml
volumes:
  postgres_data:
    # Volume nommé pour persister les données PostgreSQL
    # Survit aux redémarrages et reconstructions des conteneurs
```

## Ports Exposés

| Service  | Port Interne | Port Externe | URL d'accès |
|----------|-------------|-------------|-------------|
| Frontend | 3000        | 3000        | http://localhost:3000 |
| Backend  | 8000        | 8000        | http://localhost:8000 |
| Database | 5432        | 5432        | localhost:5432 |

## Commandes Docker

### Démarrage
```bash
# Construire et démarrer tous les services
docker-compose up --build

# Démarrer en arrière-plan
docker-compose up -d

# Démarrer un service spécifique
docker-compose up backend
```

### Gestion
```bash
# Voir les services en cours
docker-compose ps

# Logs d'un service
docker-compose logs frontend
docker-compose logs -f backend  # Suivre les logs

# Redémarrer un service
docker-compose restart frontend

# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

### Build et Maintenance
```bash
# Reconstruire un service
docker-compose build backend
docker-compose build --no-cache frontend

# Reconstruire et démarrer
docker-compose up --build

# Nettoyer les images inutilisées
docker system prune
```

### Debug et Développement
```bash
# Accéder au shell d'un conteneur
docker-compose exec backend bash
docker-compose exec frontend sh

# Executer une commande
docker-compose exec backend python -c "print('Hello')"

# Voir les variables d'environnement
docker-compose exec backend env
```

## Gestion des Données

### Base de Données
```bash
# Connexion à PostgreSQL
docker-compose exec db psql -U treechat_user -d treechat_demo

# Backup
docker-compose exec db pg_dump -U treechat_user treechat_demo > backup.sql

# Restore
docker-compose exec -T db psql -U treechat_user treechat_demo < backup.sql
```

## Problèmes Courants

### 1. Port déjà utilisé
```bash
# Vérifier les ports occupés
netstat -tulpn | grep :3000
lsof -i :8000

# Changer les ports dans docker-compose.yml
ports:
  - "3001:3000"  # Utiliser 3001 au lieu de 3000
```

### 2. Build échoue
```bash
# Nettoyer le cache Docker
docker-compose build --no-cache
docker system prune -a
```

### 3. Services ne communiquent pas
- Vérifier les noms de services dans le code
- S'assurer que `depends_on` est configuré
- Vérifier la résolution DNS avec `docker-compose exec frontend nslookup backend`

### 4. Base de données non accessible
```bash
# Vérifier que le service DB est démarré
docker-compose ps

# Tester la connexion
docker-compose exec backend nc -zv db 5432
```

## Configuration de Développement

### Volumes de Développement
Pour le développement avec hot-reload :

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:3000"
  volumes:
    - ./frontend/src:/app/src  # Hot reload
    - /app/node_modules        # Préserver node_modules
```

### Variables d'Environnement
```yaml
backend:
  environment:
    - FLASK_ENV=development
    - FLASK_DEBUG=1
    - DATABASE_URL=postgresql://treechat_user:treechat_password@db:5432/treechat_demo
```

## Production

### Optimisations Production
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.prod  # Build optimisé
  
backend:
  environment:
    - FLASK_ENV=production
    - GUNICORN_WORKERS=4
```

### Reverse Proxy (Nginx)
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - frontend
    - backend
```