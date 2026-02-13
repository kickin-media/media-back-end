# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based backend API for a media/photo management system. The system handles photo uploads, processing, storage, and retrieval with AWS integration (S3, SQS, Lambda).

## Development Commands

### Running Locally

The API requires the `ENVIRONMENT` environment variable to be set (valid values: `development`, `staging`, `production`).

```bash
cd src
export ENVIRONMENT=development
export DB_CONNECTION="mysql+pymysql://user:pass@localhost/media_backend"
export JWT_KEY_CERTIFICATE="your-jwt-cert"
export CORS_ALLOWED_ORIGINS="http://localhost:3000"
export S3_PHOTO_BUCKET="your-bucket"
export SQS_PHOTO_QUEUE="your-queue-url"

# Run migrations
alembic upgrade head

# Start the API
uvicorn main:api --host 0.0.0.0 --port 80
```

Or use the provided startup script:
```bash
cd src
./start.sh
```

### Database Migrations

```bash
cd src

# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Docker

```bash
# Build the image
docker build -t media-photo-api .

# Run locally
docker run -p 80:80 \
  -e ENVIRONMENT=development \
  -e DB_CONNECTION="mysql+pymysql://user:pass@host/db" \
  media-photo-api
```

### Lambda Development

The photo processing Lambda is in `/lambdas/photo-processing-lambda/`.

```bash
cd lambdas/photo-processing-lambda

# Install dependencies (Python 3.12)
pip install -r requirements.txt

# Test locally with sample event
python -c "from index import process; import json; process(json.load(open('test_source.json')), {})"
```

## Architecture

### Request Flow

1. **API Layer** (`/src/main.py`): FastAPI application with middleware (CORS, optional sitewide password)
2. **Routers** (`/src/routers/`): Endpoint handlers organized by resource type
   - `system.py` - Health checks and system endpoints
   - `events.py` - Event management
   - `albums.py` - Album management
   - `photos.py` - Photo upload/retrieval (main functionality)
   - `author.py` - Author/user management
3. **Authentication** (`/src/auth/`):
   - `sitewide_password_middleware.py` - Optional sitewide password via custom header (API-wide)
   - `auth_bearer.py` - JWT bearer token validation with RS256 (per-endpoint)
4. **Database** (`/src/database.py`): SQLModel/SQLAlchemy with NullPool connection management
5. **Models** (`/src/models/`): SQLModel table definitions with Pydantic validation

### Photo Upload Flow

1. Client requests upload URL from `/photo/upload` endpoint
2. API generates presigned S3 URL for `uploads/` prefix with 15-minute expiry
3. Client uploads photo directly to S3
4. Client calls `/photo/{photo_id}/process` to trigger processing
5. API sends SQS message to photo processing queue
6. Lambda processes photo:
   - Extracts EXIF data
   - Generates multiple sizes (original, large, medium, small)
   - Adds watermark to certain sizes
   - Stores processed versions in S3 under `photos/{secret}/` prefix
   - Updates photo record with EXIF data via API callback
7. Processed photos accessible via `/photo/{photo_id}` endpoint

### Database Schema

Key models and relationships:
- **Photo**: Main photo entity with EXIF data, timestamps, S3 paths
  - `author_id` → **Author** (many-to-one)
  - Links to **Album** via **AlbumPhotoLink** (many-to-many)
- **Album**: Photo collections, optionally tied to **Event**
- **Event**: Time-based event containers for albums
- **Author**: Photo uploaders/owners

### AWS Integration

- **S3 Bucket**: Three path prefixes
  - `uploads/` - Temporary upload location (presigned URLs)
  - `originals/` - Original full-resolution photos
  - `photos/{secret}/` - Processed photo variants (requires secret to access)
  - `assets/` - Static assets like watermark fonts
- **SQS Queue**: Photo processing job queue
- **Lambda**: Processes uploaded photos, generates thumbnails, extracts EXIF

### Authentication

The API has two layers of authentication:

#### 1. Sitewide Password (Optional, API-wide)

Optional first layer of defense applied to all endpoints via middleware. Enabled by setting `SITEWIDE_PASSWORD` environment variable.

- **Header**: `X-Sitewide-Password` (custom header to avoid conflicts with Bearer token auth)
- **Value**: Base64-encoded password
- **Password**: Configurable via `SITEWIDE_PASSWORD` environment variable
- **Hint**: Configurable via `SITEWIDE_PASSWORD_HINT` environment variable (returned in 401 responses)
- **Behavior**: If `SITEWIDE_PASSWORD` is not set, no sitewide password is required (API behaves as if this feature doesn't exist)
- **Implementation**: `SitewidePasswordMiddleware` in `/src/auth/sitewide_password_middleware.py`
- **CORS preflight**: OPTIONS requests skip authentication to allow CORS preflight
- **401 Response**: Returns JSON with `{"error": "authentication_required", "hint": "..."}`

This is a low-complexity first line of defense, not intended as the primary security mechanism. Uses a custom header instead of HTTP Basic Auth to allow coexistence with JWT Bearer tokens.

#### 2. JWT Bearer Tokens (Per-endpoint)

JWT tokens with RS256 signature validation for individual endpoint protection. Tokens require:
- Valid signature against `JWT_KEY_CERTIFICATE`
- Valid audience (`JWT_AUDIENCE`)
- Not expired (`exp` claim)
- Optional permission-based authorization via `permissions` claim

Use `JWTBearer` dependency in routers:
```python
from auth.auth_bearer import JWTBearer

@router.get("/protected", dependencies=[Depends(JWTBearer())])
def protected_endpoint():
    pass

# With permission requirements
@router.post("/admin", dependencies=[Depends(JWTBearer(required_permissions=["admin"]))])
def admin_endpoint():
    pass
```

### Configuration

All configuration is environment-based (see `/src/variables.py`):
- `ENVIRONMENT` - Required: development/staging/production
- `DB_CONNECTION` - Database connection string
- `CORS_ALLOWED_ORIGINS` - Comma-separated allowed origins
- `SITEWIDE_PASSWORD` - Optional: Password for sitewide authentication (sent as base64 in X-Sitewide-Password header)
- `SITEWIDE_PASSWORD_HINT` - Optional: Hint text returned to clients when authentication is required
- `JWT_KEY_CERTIFICATE` - Base64-encoded RSA public key
- `JWT_AUDIENCE` - JWT audience for token validation
- `S3_PHOTO_BUCKET` - S3 bucket for photo storage
- `SQS_PHOTO_QUEUE` - SQS queue URL for processing
- `MAPBOX_API_TOKEN` - Mapbox API token for location features

## Deployment

### Docker Deployment

GitHub Actions automatically builds and publishes Docker images to GitHub Container Registry on pushes to `main`. Images are tagged with:
- `latest`
- `YYYYMMDD_HHmmss-{git-sha}`

After building, Ansible deploys the updated docker-compose configuration to servers.

### Infrastructure Deployment

Terraform manages AWS infrastructure across three environments (`kick-in`, `bata`, `jwg`):
- S3 buckets for photo storage
- SQS queues for photo processing
- Lambda functions for photo processing
- IAM roles and policies

Terraform deployment is triggered automatically via GitHub Actions on changes to `/terraform/**` or `/lambdas/**`.

```bash
cd terraform/environments/kick-in
terraform init
terraform plan
terraform apply
```

### Deployment Configuration

Ansible playbooks in `/deployment/`:
- `deploy.yaml` - Main deployment playbook
- `docker-compose.yaml` - Primary deployment configuration (encrypted)
- `docker-compose-hetzner.yaml` - Hetzner-specific configuration (encrypted)
- Encrypted files use ansible-vault (see `/deployment/README.md` for encryption/decryption)

## Code Patterns

### Adding a New Router

1. Create router file in `/src/routers/`
2. Define router with prefix and tags:
   ```python
   from fastapi import APIRouter, Depends
   from auth.auth_bearer import JWTBearer

   router = APIRouter(prefix="/resource", tags=["resource"])

   @router.get("/", dependencies=[Depends(JWTBearer())])
   async def list_resources(db: Session = Depends(get_db)):
       pass
   ```
3. Register router in `/src/main.py`:
   ```python
   from routers import resource
   api.include_router(resource.router)
   ```

### Adding a Database Model

1. Create model in `/src/models/`
2. Define SQLModel with table=True:
   ```python
   from sqlmodel import SQLModel, Field, Relationship

   class MyModel(SQLModel, table=True):
       __tablename__ = "my_models"
       id: str = Field(primary_key=True)
       # ... fields
   ```
3. Import model in migration env.py if needed
4. Generate migration: `alembic revision --autogenerate -m "add my_model"`
5. Review and apply migration: `alembic upgrade head`

### Database Sessions

Always use `get_db()` dependency for database sessions:
```python
from database import get_db
from sqlmodel import Session, select

@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    statement = select(MyModel).where(MyModel.active == True)
    results = db.exec(statement).all()
    return results
```

The database uses NullPool to avoid connection pooling issues in multi-worker environments.

## Repository Structure

- `/src/` - FastAPI application code
  - `main.py` - Application entry point
  - `start.sh` - Startup script (migrations + uvicorn)
  - `database.py` - Database engine and session management
  - `variables.py` - Environment-based configuration
  - `routers/` - API endpoint handlers
  - `models/` - SQLModel database models
  - `auth/` - JWT authentication
  - `migrations/` - Alembic migration files
  - `config/` - Additional configuration files
  - `assets/` - Static assets
- `/lambdas/` - AWS Lambda functions
  - `photo-processing-lambda/` - Photo processing worker
- `/deployment/` - Ansible deployment configuration
- `/terraform/` - Infrastructure as code
  - `environments/` - Per-environment configurations
  - `modules/` - Reusable terraform modules
- `/tools/` - Development utilities
