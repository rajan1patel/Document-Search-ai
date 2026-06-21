# Backend Guide

This backend is a FastAPI service for a Document Intelligence Search System.

It handles:

- User registration and login
- JWT authentication
- Document metadata in PostgreSQL
- File upload and text extraction
- Text chunking
- Embedding generation
- Vector insert/search/delete in Milvus

## Tech Used

- FastAPI
- Python
- SQLAlchemy async
- Alembic
- PostgreSQL
- Milvus
- JWT auth
- Pydantic

## Backend Folder Structure

```text
backend/
  app/
    api/
      routes/          API route files
      dependencies.py  Auth dependency
    core/
      config.py        Environment settings
      security.py      Password hashing and JWT
    database/
      connection.py    Async DB session
      base.py          SQLAlchemy base
    models/            SQLAlchemy models
    repositories/      DB query helpers
    schemas/           Pydantic request/response schemas
    services/          Business logic
    main.py            FastAPI app entrypoint
  migrations/          Alembic migrations
  requirements.txt
  Dockerfile
```

## Environment

The backend reads settings from `.env`.

Expected local values:

```env
APP_NAME="Document Intelligence Search"
DATABASE_URL=postgresql+asyncpg://document_user:password@localhost:5432/document_db
JWT_SECRET=mysecretkey
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

Inside Docker, the backend must use service names:

```env
DATABASE_URL=postgresql+asyncpg://document_user:password@postgres:5432/document_db
MILVUS_HOST=milvus
```

## Run Backend Locally

From project root:

```powershell
cd D:\document-serarch-ai\Document-Search-ai\backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
http://localhost:8000/docs
```

## PostgreSQL Setup

Create database and user:

```powershell
psql -U postgres
```

Inside `psql`:

```sql
CREATE USER document_user WITH PASSWORD 'password';
CREATE DATABASE document_db OWNER document_user;
GRANT ALL PRIVILEGES ON DATABASE document_db TO document_user;
\q
```

Run migrations:

```powershell
cd D:\document-serarch-ai\Document-Search-ai\backend
.\venv\Scripts\activate
alembic upgrade head
```

Expected tables:

```text
users
documents
document_chunks
```

## Main API Endpoints

### Auth

Register:

```http
POST /auth/register
```

Body:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Login:

```http
POST /auth/login
```

Body:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### Documents

All document routes require:

```http
Authorization: Bearer <token>
```

List documents:

```http
GET /documents
```

Upload document:

```http
POST /documents/upload
```

Request type:

```text
multipart/form-data
```

Field:

```text
file
```

Supported files:

```text
PDF
DOCX
TXT
```

Delete document:

```http
DELETE /documents/{document_id}
```

### Search

Search requires authentication:

```http
POST /search
```

Body:

```json
{
  "query": "example search",
  "limit": 5
}
```

Response:

```json
[
  {
    "filename": "document.pdf",
    "page": 0,
    "chunk": "matching text chunk",
    "score": 0.82
  }
]
```

## Document Processing Flow

```text
User uploads file
  |
  v
FastAPI receives multipart/form-data
  |
  v
File is saved to backend/uploads
  |
  v
Document metadata is saved in PostgreSQL
  |
  v
Text is extracted from PDF/DOCX/TXT
  |
  v
Text is split into chunks
  |
  v
Chunks are saved in PostgreSQL
  |
  v
Embeddings are generated
  |
  v
Vectors are stored in Milvus
  |
  v
Document status becomes completed
```

## What Needs PostgreSQL

These need PostgreSQL:

- Register
- Login
- JWT user lookup
- Dashboard
- Documents list
- Document metadata
- Document chunks

## What Needs Milvus

These need Milvus:

- Upload with vector storage
- Semantic search
- Vector deletion on document delete

If Milvus is not running, full upload/search will fail.

## Docker Usage

From project root:

```powershell
docker compose up --build -d
```

Run migrations:

```powershell
docker compose exec backend alembic upgrade head
```

Stop containers:

```powershell
docker compose down
```

Stop and delete database volume:

```powershell
docker compose down -v
```

## Best Local Testing Order

1. Start PostgreSQL.
2. Run Alembic migrations.
3. Start backend.
4. Test `/docs`.
5. Register user.
6. Login user.
7. Check dashboard/documents.
8. Start Milvus.
9. Upload document.
10. Search document content.

