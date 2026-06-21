# Frontend Guide

This frontend is a Nuxt 4 application for the Document Intelligence Search System.

It provides pages for:

- Register
- Login
- Dashboard
- Upload documents
- View documents
- Semantic search

## Tech Used

- Nuxt 4
- Vue 3 Composition API
- TypeScript
- TailwindCSS
- Pinia
- Axios

## Frontend Folder Structure

```text
frontend/
  app/
    components/       Reusable UI components
    composables/      API helpers for documents/search
    middleware/       Route protection
    pages/            Nuxt pages
    plugins/          Auth initialization
    stores/           Pinia auth store
    utils/
      api.ts          Axios client
  public/
  package.json
  Dockerfile
```

## Run Frontend Locally

From project root:

```powershell
cd D:\document-serarch-ai\Document-Search-ai\frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Backend Connection

The frontend sends API requests to:

```text
http://localhost:8000
```

This is configured in:

```text
frontend/app/utils/api.ts
```

The Axios client automatically attaches JWT tokens:

```http
Authorization: Bearer <token>
```

The token is read from browser `localStorage`.

## Auth Flow

```text
User opens login/register page
  |
  v
User submits email and password
  |
  v
Frontend sends request to FastAPI
  |
  v
Backend returns JWT token on login
  |
  v
Frontend stores token in localStorage
  |
  v
Axios sends token on protected requests
  |
  v
User can access dashboard/documents/upload/search
```

## Pages

### `/register`

Creates a new user.

Calls:

```http
POST /auth/register
```

Payload:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### `/login`

Logs in a user.

Calls:

```http
POST /auth/login
```

Stores:

```text
access_token
```

in:

```text
localStorage["token"]
```

### `/dashboard`

Shows document stats.

Calls:

```http
GET /dashboard
```

Requires JWT.

### `/documents`

Shows uploaded documents.

Calls:

```http
GET /documents
DELETE /documents/{id}
```

Requires JWT.

### `/upload`

Uploads a document.

Calls:

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

### `/search`

Searches uploaded document chunks semantically.

Calls:

```http
POST /search
```

Payload:

```json
{
  "query": "example search",
  "limit": 5
}
```

Expected response:

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

## Complete System Flow

```text
Nuxt frontend
  |
  | HTTP requests with Axios
  v
FastAPI backend
  |
  +--> PostgreSQL
  |      stores users, document metadata, chunks
  |
  +--> Milvus
         stores embeddings and semantic-search vectors
```

User flow:

```text
Register
  |
  v
Login
  |
  v
JWT saved in browser
  |
  v
Upload document
  |
  v
Backend extracts text and stores metadata
  |
  v
Backend chunks text and creates embeddings
  |
  v
Vectors saved in Milvus
  |
  v
Search query creates embedding
  |
  v
Milvus returns closest chunks
  |
  v
Frontend displays filename, page, chunk, score
```

## Best Local Testing Order

1. Start backend:

```powershell
cd D:\document-serarch-ai\Document-Search-ai\backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

2. Start frontend:

```powershell
cd D:\document-serarch-ai\Document-Search-ai\frontend
npm run dev
```

3. Open:

```text
http://localhost:3000
```

4. Test:

```text
Register -> Login -> Dashboard -> Documents
```

5. For upload/search, make sure PostgreSQL and Milvus are running.

## Docker Usage

From project root:

```powershell
docker compose up --build -d
```

Open:

```text
http://localhost:3000
```

Stop:

```powershell
docker compose down
```

