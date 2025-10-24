# ⚡ Electricity Meter Reading Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![CI](https://img.shields.io/badge/CI-Passing-brightgreen.svg)

**API professionnelle de gestion des relevés de compteurs électriques avec géolocalisation automatique, upload S3 et interface complète.**

[Documentation](#-documentation) •
[Installation](#-installation) •
[API Reference](#-api-reference) •
[Déploiement](#-déploiement) •
[Support](#-support)

</div>

---

## 📑 Table des Matières

- [✨ Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture](#️-architecture)
- [🚀 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [📚 Documentation](#-documentation)
- [🔌 API Reference](#-api-reference)
- [🗂️ Structure du Projet](#️-structure-du-projet)
- [🐳 Docker & Kubernetes](#-docker--kubernetes)
- [🧪 Tests](#-tests)
- [🔐 Sécurité](#-sécurité)
- [📊 Monitoring](#-monitoring)
- [🤝 Contribution](#-contribution)
- [📄 Licence](#-licence)

---

## ✨ Fonctionnalités

### 🎯 Fonctionnalités Principales

#### 👥 Gestion des Utilisateurs

- **3 rôles distincts** : Administrateur, Superviseur, Contrôleur
- **Authentification JWT** avec tokens d'accès et de rafraîchissement
- **Permissions granulaires** basées sur les rôles et les villes
- **Gestion complète** : création, modification, désactivation

#### 🏙️ Gestion des Villes

- Organisation hiérarchique par ville
- Attribution des utilisateurs et compteurs par ville
- Statistiques et rapports par ville
- Gestion multi-ville pour les administrateurs

#### ⚡ Gestion des Compteurs

- **Import massif** via fichiers Excel (template téléchargeable)
- Validation automatique des données
- Historique complet des lectures
- Statuts multiples : actif, inactif, maintenance, décommissionné
- Coordonnées GPS optionnelles pour validation de localisation

#### 📊 Relevés de Compteurs

- **Photos obligatoires** (minimum 2 par relevé)
- **Upload S3/MinIO** automatique et sécurisé
- **Géolocalisation automatique** via GPS de l'appareil
- Validation de la distance par rapport au compteur
- Commentaires et métadonnées
- Validation des valeurs (croissantes uniquement)
- Édition limitée dans le temps (24h pour les contrôleurs)

#### 📸 Gestion des Photos

- Upload multiple (jusqu'à 10 photos par relevé)
- Formats supportés : JPEG, PNG, WebP
- Taille maximale : 10MB par photo
- Stockage organisé par compteur
- Suppression automatique lors de la suppression du relevé

#### 📍 Géolocalisation

- **Capture automatique** de la position GPS
- Validation de la proximité avec le compteur
- Fallback vers géolocalisation IP si GPS indisponible
- Niveaux de précision (high, medium, low)
- Configuration flexible (obligatoire/optionnel)

#### 📈 Statistiques et Rapports

- Dashboard par ville et par contrôleur
- Statistiques de lectures (min, max, moyenne)
- Comptage des photos uploadées
- Historique des lectures par période
- Export des données

### 🛡️ Sécurité et Performance

- **Authentification sécurisée** avec JWT (RS256)
- **Rate limiting** configurable par endpoint
- **Validation stricte** des données avec Pydantic
- **Transactions atomiques** pour l'intégrité des données
- **Connexion pooling** pour optimiser les performances
- **Cache Redis** pour les requêtes fréquentes
- **CORS configurables** pour sécuriser les origines
- **Headers de sécurité** (CSP, HSTS, X-Frame-Options, etc.)

### 🔧 Fonctionnalités Techniques

- **API RESTful** complète avec FastAPI
- **Documentation interactive** Swagger/OpenAPI
- **Pagination** sur tous les endpoints de liste
- **Filtrage avancé** par date, statut, ville, etc.
- **Relations chargées** dynamiquement (eager/lazy loading)
- **Migrations automatiques** avec Alembic
- **Logs structurés** avec rotation automatique
- **Health checks** pour monitoring
- **Scalabilité horizontale** avec Kubernetes

---

## 🏗️ Architecture

### Stack Technique

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend/Mobile                      │
│         (React, React Native, Web App)                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS/REST API
┌────────────────────▼────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                 │
│            Rate Limiting, SSL, Compression               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   FastAPI Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Auth       │  │   Business   │  │   Upload     │  │
│  │   Service    │  │   Logic      │  │   Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────┬──────────────────┬─────────────────┬───────────┘
        │                  │                 │
        │                  │                 │
┌───────▼─────┐    ┌──────▼──────┐   ┌─────▼──────────┐
│  PostgreSQL │    │    Redis    │   │  S3/MinIO      │
│  Database   │    │    Cache    │   │  Storage       │
└─────────────┘    └─────────────┘   └────────────────┘
```

### Technologies

| Composant         | Technologie | Version | Description                         |
| ----------------- | ----------- | ------- | ----------------------------------- |
| **Backend**       | FastAPI     | 0.104+  | Framework web moderne et performant |
| **Language**      | Python      | 3.11+   | Langage de programmation            |
| **Database**      | PostgreSQL  | 15+     | Base de données relationnelle       |
| **ORM**           | SQLAlchemy  | 2.0+    | ORM asynchrone                      |
| **Cache**         | Redis       | 7+      | Cache et sessions                   |
| **Storage**       | S3/MinIO    | -       | Stockage d'objets                   |
| **Server**        | Uvicorn     | 0.24+   | Serveur ASGI                        |
| **Proxy**         | Nginx       | 1.25+   | Reverse proxy                       |
| **Container**     | Docker      | 20.10+  | Conteneurisation                    |
| **Orchestration** | Kubernetes  | 1.28+   | Orchestration de conteneurs         |

### Base de Données

**Schéma des Entités :**

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   cities    │         │    users    │         │   meters    │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ id (PK)     │◄───┐    │ id (PK)     │    ┌───►│ id (PK)     │
│ name        │    │    │ username    │    │    │ code        │
│ created_at  │    └────│ city_id (FK)│    │    │ city_id (FK)│
│ updated_at  │         │ role        │    │    │ owner_name  │
└─────────────┘         │ is_active   │    │    │ address     │
                        └─────────────┘    │    │ meter_number│
                                           │    │ prev_reading│
                        ┌─────────────┐    │    │ status      │
                        │  readings   │    │    └─────────────┘
                        ├─────────────┤    │
                        │ id (PK)     │    │
                        │ meter_id(FK)├────┘
                        │ controller_ │
                        │   id (FK)   ├────────► users
                        │ reading_val │
                        │ reading_date│
                        │ photo_urls  │
                        │ latitude    │
                        │ longitude   │
                        │ comment     │
                        └─────────────┘
```

---

## 🚀 Installation

### Prérequis

- **Python** 3.11 ou supérieur
- **PostgreSQL** 15 ou supérieur
- **Redis** 7 ou supérieur (optionnel)
- **Docker** 20.10+ et Docker Compose (pour le déploiement)
- **Git**

### Installation en Développement

#### 1. Cloner le Repository

```bash
git clone https://github.com/yourusername/meter-reading-api.git
cd meter-reading-api
```

#### 2. Créer l'Environnement Virtuel

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

#### 3. Installer les Dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configuration

Copier le fichier d'exemple et le configurer :

```bash
cp .env.example .env
nano .env
```

Configuration minimale :

```env
# Application
APP_NAME="Meter Reading API"
APP_VERSION="1.0.0"
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=meter_readings

# Redis (optionnel en dev)
REDIS_ENABLED=false

# S3 (utiliser MinIO en dev)
S3_ENABLED=true
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://localhost:9000
S3_BUCKET_NAME=meter-readings

# First Superuser
FIRST_SUPERUSER_USERNAME=admin
FIRST_SUPERUSER_PASSWORD=Admin123!
FIRST_SUPERUSER_FULL_NAME=Administrator
```

#### 5. Démarrer PostgreSQL et MinIO

**Option A : Docker Compose (Recommandé)**

```bash
docker-compose up -d db redis minio
```

**Option B : Installation Locale**

Installer PostgreSQL et MinIO localement selon votre OS.

#### 6. Créer la Base de Données

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE meter_readings;
\q
```

#### 7. Exécuter les Migrations

```bash
alembic upgrade head
```

#### 8. Démarrer le Serveur

```bash
# Mode développement avec reload automatique
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ou avec make
make run-dev
```

#### 9. Accéder à l'Application

- **API** : http://localhost:8000
- **Documentation Interactive** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **Health Check** : http://localhost:8000/health

### Installation avec Docker

#### Développement

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f api

# Arrêter les services
docker-compose down
```

#### Production

```bash
# Build et démarrer
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Vérifier le statut
docker-compose ps
```

---

## ⚙️ Configuration

### Variables d'Environnement

Toutes les variables sont documentées dans `.env.example`. Voici les principales :

#### Application

```env
APP_NAME=Meter Reading API
APP_VERSION=1.0.0
ENVIRONMENT=production  # production, development, staging
DEBUG=false
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
SECRET_KEY=generate-with-openssl-rand-hex-32
```

#### Base de Données

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=secure_password_here
DB_NAME=meter_readings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

#### Authentification

```env
# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# First Superuser (créé au démarrage)
FIRST_SUPERUSER_USERNAME=admin
FIRST_SUPERUSER_PASSWORD=ChangeMe123!
FIRST_SUPERUSER_FULL_NAME=System Administrator
```

#### Stockage S3

```env
S3_ENABLED=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_ENDPOINT_URL=https://s3.amazonaws.com  # ou http://localhost:9000 pour MinIO
S3_BUCKET_NAME=meter-readings
S3_FOLDER_READINGS=readings
S3_FOLDER_TEMP=temp
```

#### Géolocalisation

```env
GEOLOCATION_REQUIRED=true
GEOLOCATION_STRICT_VALIDATION=false
GEOLOCATION_MAX_DISTANCE=500
GEOLOCATION_IP_FALLBACK=true
```

#### Rate Limiting

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

#### CORS

```env
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://app.yourdomain.com"]
```

### Génération de Clés Secrètes

```bash
# SECRET_KEY
openssl rand -hex 32

# Ou avec Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📚 Documentation

### Documentation Interactive

Une fois l'application démarrée, accédez à :

- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`
- **OpenAPI JSON** : `http://localhost:8000/openapi.json`

### Guides Disponibles

Dans le répertoire `docs/` :

- **README_AUTH.md** - Guide d'authentification
- **README_PHOTOS.md** - Guide de gestion des photos
- **README_GEOLOCATION.md** - Guide de géolocalisation
- **README_IMPORT.md** - Guide d'import Excel
- **DEPLOYMENT.md** - Guide de déploiement
- **API_REFERENCE.md** - Référence complète de l'API

### Exemples Frontend

Dans `frontend/examples/` :

- `geolocation.js` - Implémentation géolocalisation (React/React Native)
- `photo-upload.js` - Upload de photos
- `auth.js` - Authentification JWT
- `api-client.js` - Client API TypeScript

---

## 🔌 API Reference

### Authentification

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=Admin123!
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "full_name": "Administrator",
    "role": "admin",
    "city_id": null,
    "is_active": true
  }
}
```

#### Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "controller1",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "role": "controller",
  "city_id": "uuid-city"
}
```

### Villes

#### Lister les Villes

```http
GET /api/v1/cities?page=1&limit=10
Authorization: Bearer {token}
```

#### Créer une Ville

```http
POST /api/v1/cities
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Paris"
}
```

### Compteurs

#### Lister les Compteurs

```http
GET /api/v1/meters?city_id=uuid&page=1&limit=20
Authorization: Bearer {token}
```

#### Créer un Compteur

```http
POST /api/v1/meters
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "MTR-001",
  "owner_name": "John Doe",
  "address": "123 Main Street",
  "meter_number": "SN-2024-001",
  "city_id": "uuid",
  "previous_reading": 1250.5,
  "status": "active"
}
```

#### Import Excel

```http
POST /api/v1/meters/import/upload?city_id=uuid
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: meters.xlsx
```

### Lectures

#### Créer une Lecture avec Photos

```http
POST /api/v1/readings/with-photos
Authorization: Bearer {token}
Content-Type: multipart/form-data

meter_id: uuid
reading_value: 1500.75
reading_date: 2024-01-15T14:30:00Z
photos: [file1.jpg, file2.jpg]
comment: Lecture normale
latitude: 48.8566
longitude: 2.3522
location_accuracy: 15.5
```

**Response:**

```json
{
  "id": "uuid",
  "meter_id": "uuid",
  "controller_id": "uuid",
  "reading_value": 1500.75,
  "reading_date": "2024-01-15T14:30:00Z",
  "photo_urls": ["https://s3.../photo1.jpg", "https://s3.../photo2.jpg"],
  "photos_count": 2,
  "comment": "Lecture normale",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "location_accuracy": 15.5,
  "has_geolocation": true,
  "created_at": "2024-01-15T14:30:05Z"
}
```

#### Lister les Lectures

```http
GET /api/v1/readings?meter_id=uuid&start_date=2024-01-01&page=1
Authorization: Bearer {token}
```

#### Statistiques

```http
GET /api/v1/readings/stats/overview?city_id=uuid&start_date=2024-01-01
Authorization: Bearer {token}
```

### Codes d'Erreur

| Code | Signification         | Description           |
| ---- | --------------------- | --------------------- |
| 200  | OK                    | Requête réussie       |
| 201  | Created               | Ressource créée       |
| 204  | No Content            | Suppression réussie   |
| 400  | Bad Request           | Données invalides     |
| 401  | Unauthorized          | Non authentifié       |
| 403  | Forbidden             | Accès refusé          |
| 404  | Not Found             | Ressource non trouvée |
| 409  | Conflict              | Conflit (ex: doublon) |
| 422  | Unprocessable Entity  | Validation échouée    |
| 500  | Internal Server Error | Erreur serveur        |

### Rate Limiting

- **Par défaut** : 100 requêtes/minute
- **Uploads** : 2 requêtes/seconde
- **Headers** :
  - `X-RateLimit-Limit` : Limite totale
  - `X-RateLimit-Remaining` : Requêtes restantes
  - `X-RateLimit-Reset` : Timestamp de reset

---

## 🗂️ Structure du Projet

```
meter-reading-api/
├── 📁 app/                          # Code source de l'application
│   ├── 📁 api/                      # Endpoints API
│   │   ├── 📁 v1/
│   │   │   ├── 📁 endpoints/        # Endpoints par resource
│   │   │   │   ├── auth.py          # Authentification
│   │   │   │   ├── users.py         # Gestion utilisateurs
│   │   │   │   ├── cities.py        # Gestion villes
│   │   │   │   ├── meters.py        # Gestion compteurs
│   │   │   │   ├── meter_import.py  # Import Excel
│   │   │   │   ├── readings.py      # Gestion lectures
│   │   │   │   └── upload.py        # Upload S3
│   │   │   └── router.py            # Router principal v1
│   │   └── deps.py                  # Dépendances (auth, db, etc.)
│   ├── 📁 core/                     # Configuration et utilitaires
│   │   ├── config.py                # Configuration Pydantic
│   │   ├── security.py              # JWT, hashing, etc.
│   │   ├── exceptions.py            # Exceptions personnalisées
│   │   └── pagination.py            # Système de pagination
│   ├── 📁 db/                       # Base de données
│   │   ├── session.py               # Session async SQLAlchemy
│   │   └── init_db.py               # Initialisation DB
│   ├── 📁 models/                   # Modèles SQLAlchemy
│   │   ├── base.py                  # Modèle de base
│   │   ├── user.py                  # Modèle User
│   │   ├── city.py                  # Modèle City
│   │   ├── meter.py                 # Modèle Meter
│   │   └── reading.py               # Modèle Reading
│   ├── 📁 schemas/                  # Schémas Pydantic
│   │   ├── base.py                  # Schémas de base
│   │   ├── user.py                  # Schémas User
│   │   ├── city.py                  # Schémas City
│   │   ├── meter.py                 # Schémas Meter
│   │   ├── meter_import.py          # Schémas Import
│   │   └── reading.py               # Schémas Reading
│   ├── 📁 services/                 # Logique métier
│   │   ├── base.py                  # Service de base (CRUD)
│   │   ├── auth.py                  # Service Auth
│   │   ├── user.py                  # Service User
│   │   ├── city.py                  # Service City
│   │   ├── meter.py                 # Service Meter
│   │   ├── meter_import.py          # Service Import Excel
│   │   ├── reading.py               # Service Reading
│   │   ├── upload.py                # Service Upload S3
│   │   └── geolocation.py           # Service Géolocalisation
│   └── main.py                      # Point d'entrée FastAPI
├── 📁 alembic/                      # Migrations de base de données
│   ├── versions/                    # Fichiers de migration
│   ├── env.py                       # Configuration Alembic
│   └── alembic.ini                  # Config Alembic
├── 📁 docker/                       # Configuration Docker
│   ├── Dockerfile                   # Dockerfile production
│   ├── Dockerfile.dev               # Dockerfile développement
│   ├── 📁 nginx/                    # Configuration Nginx
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── conf.d/
│   └── 📁 scripts/                  # Scripts Docker
│       ├── entrypoint.sh            # Script de démarrage
│       └── wait-for-it.sh           # Attente des services
├── 📁 kubernetes/                   # Configuration Kubernetes
│   ├── 📁 base/                     # Ressources de base
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── hpa.yaml
│   ├── 📁 postgres/                 # PostgreSQL
│   ├── 📁 redis/                    # Redis
│   └── 📁 monitoring/               # Monitoring
├── 📁 scripts/                      # Scripts utilitaires
│   ├── deploy.sh                    # Script de déploiement
│   ├── backup.sh                    # Script de backup
│   └── restore.sh                   # Script de restore
├── 📁 tests/                        # Tests
│   ├── 📁 unit/                     # Tests unitaires
│   ├── 📁 integration/              # Tests d'intégration
│   └── conftest.py                  # Configuration pytest
├── 📁 docs/                         # Documentation
│   ├── README_AUTH.md
│   ├── README_PHOTOS.md
│   ├── README_GEOLOCATION.md
│   ├── README_IMPORT.md
│   └── DEPLOYMENT.md
├── 📁 frontend/                     # Exemples frontend
│   └── examples/
│       ├── geolocation.js
│       ├── photo-upload.js
│       └── auth.js
├── .env.example                     # Variables d'environnement exemple
├── .gitignore                       # Fichiers ignorés par Git
├── docker-compose.yml               # Docker Compose base
├── docker-compose.dev.yml           # Docker Compose dev
├── docker-compose.prod.yml          # Docker Compose prod
├── requirements.txt                 # Dépendances Python
├── Makefile                         # Commandes make
├── README.md                        # Ce fichier
└── LICENSE                          # Licence MIT
```

---

## 🐳 Docker & Kubernetes

### Docker Compose

#### Développement

```bash
# Démarrer tous les services
make up

# ou
docker-compose up -d

# Voir les logs
make logs

# Shell API
make shell

# Shell DB
make db-shell
```

#### Production

```bash
# Build et tag
docker build -t meter-reading-api:1.0.0 -f docker/Dockerfile .

# Push vers registry
docker push yourdockerhub/meter-reading-api:1.0.0

# Déployer
VERSION=1.0.0 docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes

#### Déploiement Complet

```bash
# Script automatisé
./scripts/deploy.sh

# Ou manuellement
kubectl apply -f kubernetes/base/namespace.yaml
kubectl apply -f kubernetes/base/secrets.yaml
kubectl apply -f kubernetes/base/configmap.yaml
kubectl apply -f kubernetes/postgres/
kubectl apply -f kubernetes/redis/
kubectl apply -f kubernetes/base/deployment.yaml
kubectl apply -f kubernetes/base/service.yaml
kubectl apply -f kubernetes/base/ingress.yaml
kubectl apply -f kubernetes/base/hpa.yaml
```

#### Commandes Utiles

```bash
# Statut
kubectl get all -n meter-reading

# Logs
kubectl logs -f deployment/api-deployment -n meter-reading

# Shell
kubectl exec -it deployment/api-deployment -n meter-reading -- /bin/bash

# Scale
kubectl scale deployment/api-deployment --replicas=5 -n meter-reading

# Rollout
kubectl rollout restart deployment/api-deployment -n meter-reading
kubectl rollout status deployment/api-deployment -n meter-reading
kubectl rollout undo deployment/api-deployment -n meter-reading
```

#### Monitoring

```bash
# Metrics des pods
kubectl top pods -n meter-reading

# Metrics des nodes
kubectl top nodes

# Events
kubectl get events -n meter-reading --sort-by='.lastTimestamp'
```

---

## 🧪 Tests

### Exécuter les Tests

```bash
# Tous les tests
pytest

# Avec coverage
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/unit/
pytest tests/integration/

# Test spécifique
pytest tests/unit/test_auth.py

# Verbose
pytest -v -s

# Avec Docker
docker-compose exec api pytest tests/ -v
```

### Structure des Tests

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def admin_token(client):
    # Login admin et retourner token
    pass

# tests/unit/test_auth.py
async def test_login(client):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Coverage

```bash
# Générer le rapport
pytest --cov=app --cov-report=html

# Ouvrir dans le navigateur
open htmlcov/index.html
```

---

## 🔐 Sécurité

### Best Practices Implémentées

✅ **Authentification**

- JWT avec tokens signés (RS256 ou HS256)
- Tokens d'accès à courte durée (30 min)
- Refresh tokens à longue durée (7 jours)
- Hashing bcrypt pour les mots de passe

✅ **Autorisation**

- RBAC (Role-Based Access Control)
- Permissions granulaires par endpoint
- Isolation des données par ville

✅ **Validation**

- Validation stricte avec Pydantic
- SQL injection prevention (ORM)
- XSS protection (sanitization)

✅ **Network**

- HTTPS obligatoire en production
- CORS configurables
- Rate limiting par IP
- Headers de sécurité (HSTS, CSP, etc.)

✅ **Secrets**

- Variables d'environnement
- Secrets Kubernetes
- Rotation recommandée tous les 90 jours

✅ **Monitoring**

- Logs structurés
- Health checks
- Alertes sur erreurs

### Checklist Sécurité

Avant le déploiement en production :

- [ ] Changer tous les mots de passe par défaut
- [ ] Générer une nouvelle `SECRET_KEY`
- [ ] Configurer HTTPS avec certificats valides
- [ ] Activer le rate limiting
- [ ] Configurer les CORS correctement
- [ ] Désactiver DEBUG mode
- [ ] Configurer les backups automatiques
- [ ] Activer les logs de sécurité
- [ ] Scanner les vulnérabilités (Trivy, Snyk)
- [ ] Tester les endpoints avec OWASP ZAP

### Rapporter une Vulnérabilité

Si vous découvrez une vulnérabilité de sécurité, merci de **NE PAS** créer d'issue publique. Envoyez un email à : security@yourdomain.com

---

## 📊 Monitoring

### Health Checks

```bash
# Health check simple
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "app_name": "Meter Reading API",
  "version": "1.0.0",
  "environment": "production",
  "database": "connected",
  "s3_enabled": true,
  "redis_enabled": true
}
```

### Prometheus Metrics

```bash
# Metrics endpoint
curl http://localhost:8000/metrics
```

### Logs

```bash
# Docker
docker-compose logs -f api

# Kubernetes
kubectl logs -f deployment/api-deployment -n meter-reading

# Suivre un pod spécifique
kubectl logs -f pod-name -n meter-reading

# Logs des 1h dernière
kubectl logs --since=1h deployment/api-deployment -n meter-reading
```

### Grafana Dashboard

Un dashboard Grafana est disponible dans `kubernetes/monitoring/grafana.yaml` avec :

- Requêtes par seconde
- Temps de réponse
- Erreurs 5xx
- Utilisation CPU/RAM
- Nombre de lectures créées
- Taille du cache Redis

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

### 1. Fork le Projet

```bash
git clone https://github.com/yourusername/meter-reading-api.git
cd meter-reading-api
```

### 2. Créer une Branche

```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
```

### 3. Développer

- Suivre les conventions de code (Black, isort, flake8)
- Ajouter des tests pour les nouvelles fonctionnalités
- Documenter les changements

### 4. Tester

```bash
# Linter
black app/
isort app/
flake8 app/

# Tests
pytest tests/ -v --cov=app
```

### 5. Commit

```bash
git add .
git commit -m "feat: ajout de ma nouvelle fonctionnalité"
```

Conventions de commit :

- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `refactor:` refactoring
- `test:` ajout de tests
- `chore:` tâches maintenance

### 6. Push et Pull Request

```bash
git push origin feature/ma-nouvelle-fonctionnalite
```

Créer une Pull Request sur GitHub avec :

- Description claire des changements
- Screenshots si applicable
- Tests ajoutés/modifiés
- Documentation mise à jour

### Code Style

Le projet utilise :

- **Black** pour le formatage
- **isort** pour l'ordre des imports
- **flake8** pour le linting
- **mypy** pour le type checking

```bash
# Formater le code
black app/
isort app/

# Vérifier
flake8 app/ --max-line-length=100
mypy app/ --ignore-missing-imports
```

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

```
MIT License

Copyright (c) 2024 Your Company Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🌟 Remerciements

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderne
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM puissant
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Validation de données
- [PostgreSQL](https://www.postgresql.org/) - Base de données fiable
- [Redis](https://redis.io/) - Cache performant
- [Docker](https://www.docker.com/) - Conteneurisation
- [Kubernetes](https://kubernetes.io/) - Orchestration

---

## 📞 Support

### Documentation

- 📖 [Documentation complète](https://docs.yourdomain.com)
- 🎓 [Guides et tutoriels](https://docs.yourdomain.com/guides)
- 📹 [Vidéos de formation](https://youtube.com/yourdomain)

### Communauté

- 💬 [Discord](https://discord.gg/yourdomain)
- 💼 [LinkedIn](https://linkedin.com/company/yourdomain)
- 🐦 [Twitter](https://twitter.com/yourdomain)

### Contact

- 📧 Email : support@yourdomain.com
- 🐛 Issues : [GitHub Issues](https://github.com/yourusername/meter-reading-api/issues)
- 💡 Feature Requests : [GitHub Discussions](https://github.com/yourusername/meter-reading-api/discussions)

### Support Commercial

Pour un support professionnel, des formations ou du développement sur mesure :

- 🏢 Enterprise : enterprise@yourdomain.com
- 📞 Téléphone : +33 1 23 45 67 89

---

<div align="center">

<p><strong>⭐ Si ce projet vous a aidé, n&apos;hésitez pas à lui donner une étoile ! ⭐</strong></p>

Made with ❤️ by [Your Company](https://yourdomain.com)

[⬆ Retour en haut](#-electricity-meter-reading-management-system)

</div>
