# Milvus Vector Database Setup

## Overview

This project uses **Milvus 2.4.0** (standalone mode) as the vector database for storing and searching document embeddings. It enables semantic/AI-powered search across uploaded documents.

---

## Architecture

Milvus runs in **standalone mode** with two dependencies:

```
etcd (v3.5.5)  ──>  Milvus (v2.4.0)  ──>  MinIO (for object storage)
```

| Component | Image | Purpose |
|---|---|---|
| **etcd** | `quay.io/coreos/etcd:v3.5.5` | Metadata storage & service discovery |
| **MinIO** | `minio/minio` | Stores vector index files and data snapshots |
| **Milvus** | `milvusdb/milvus:v2.4.0` | Vector database — stores & searches embeddings |

---

## How It's Set Up (docker-compose.yml)

All three services are defined in `docker-compose.yml`:

### etcd

```yaml
etcd:
  image: quay.io/coreos/etcd:v3.5.5
  container_name: document_etcd
  environment:
    ETCD_AUTO_COMPACTION_MODE: revision
    ETCD_AUTO_COMPACTION_RETENTION: "1000"
    ETCD_LISTEN_CLIENT_URLS: http://0.0.0.0:2379
    ETCD_ADVERTISE_CLIENT_URLS: http://etcd:2379
```

### MinIO

```yaml
minio:
  image: minio/minio
  container_name: document_minio
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  command: server /data --console-address ":9001"
```

### Milvus

```yaml
milvus:
  image: milvusdb/milvus:v2.4.0
  container_name: document_milvus
  environment:
    ETCD_ENDPOINTS: etcd:2379
    MINIO_ADDRESS: minio:9000
    MINIO_ACCESS_KEY: minioadmin
    MINIO_SECRET_KEY: minioadmin
  command: ["milvus", "run", "standalone"]
  ports:
    - "19530:19530"
  depends_on:
    - etcd
    - minio
```

---

## Credentials

| Service | Username | Password | Notes |
|---|---|---|---|
| **Milvus** | — | — | No auth enabled by default |
| **MinIO (Console)** | `minioadmin` | `minioadmin` | Used internally by Milvus for storage |

> **Note:** Milvus itself does **not** require authentication in this setup. Access is controlled at the application level via JWT tokens.

---

## Connection Details

### From Backend Container (Docker network)

| Variable | Value |
|---|---|
| Host | `milvus` (service name in docker-compose) |
| Port | `19530` |
| gRPC Endpoint | `milvus:19530` |

### From Local Machine (outside Docker)

| Variable | Value |
|---|---|
| Host | `localhost` |
| Port | `19530` |
| gRPC Endpoint | `localhost:19530` |

Configured in `backend/app/core/config.py`:

```python
MILVUS_HOST: str = "localhost"   # Overridden via env var in docker-compose
MILVUS_PORT: int = 19530
```

The docker-compose overrides these at runtime:

```yaml
environment:
  MILVUS_HOST: milvus
  MILVUS_PORT: 19530
```

---

## Collection Schema

The backend creates a collection named **`document_vectors`** automatically on first use with this schema:

| Field | Type | Description |
|---|---|---|
| `id` | INT64 (Primary Key, Auto-ID) | Auto-generated unique ID |
| `document_id` | INT64 | Reference to the document in PostgreSQL |
| `user_id` | INT64 | Owner of the document |
| `chunk_text` | VARCHAR(2000) | The text chunk content |
| `page_number` | INT64 | Page number (for PDFs) |
| `embedding` | FLOAT_VECTOR(384) | 384-dim embedding vector |

**Index:** IVF_FLAT with COSINE distance metric, `nlist: 128`.

---

## How the Backend Interacts with Milvus

### Service: `backend/app/services/milvus_service.py`

The `MilvusService` class handles all Milvus operations:

**1. Connection (`milvus_service._connect()`)**
- Uses `pymilvus` library
- Retries up to 30 times with 2s intervals (waits ~60s for Milvus to be ready)
- Uses `connections.connect(alias="default", host=..., port=...)`

**2. Collection Setup (`milvus_service._get_collection()`)**
- Checks if `document_vectors` exists; creates it if not
- Automatically builds the schema with all fields
- Creates the IVF_FLAT index on the `embedding` field

**3. Insert Vectors (`milvus_service.insert_vector()`)**
```python
milvus_service.insert_vector(
    document_id=doc_id,
    user_id=user_id,
    text=chunk_text,
    vector=embedding_vector,  # 384-dim float list
    page_number=page_number
)
```

**4. Search (`milvus_service.search()`)**
```python
results = milvus_service.search(
    vector=query_embedding,
    user_id=user_id,
    limit=5  # top-k results
)
```
- Searches with COSINE similarity
- Filters by `user_id` so users only search their own documents
- Returns ranked chunks with scores

**5. Delete (`milvus_service.delete_document_vectors()`)**
- Deletes all vectors belonging to a specific document + user

### Flow: Upload → Embed → Store

```
1. User uploads document
2. ExtractorService extracts text & chunks it
3. EmbeddingService creates 384-dim vectors (all-MiniLM-L6-v2)
4. MilvusService.insert_vector() stores each chunk + vector
```

### Flow: Search Query

```
1. User enters a query
2. EmbeddingService encodes query into a 384-dim vector
3. MilvusService.search() does ANN search with COSINE similarity
4. Results returned with document_id, chunk_text, page_number, score
```

---

## Embedding Model

The embeddings are generated using **`all-MiniLM-L6-v2`** from Sentence Transformers, producing **384-dimensional** vectors.

**File:** `backend/app/services/embedding_service.py`

```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = None

    def _get_model(self):
        if self.model is None:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        return self.model

    def create_embedding(self, text: str):
        vector = self._get_model().encode(text)
        return vector.tolist()
```

---

## Viewing / GUI Options

### 1. Attu (Milvus GUI) — Recommended

[**Attu**](https://github.com/zilliztech/attu) is the official open-source GUI for Milvus.

**To run Attu:**

```bash
docker run -d --name attu \
  -p 8001:3000 \
  -e MILVUS_URL=localhost:19530 \
  zilliz/attu:latest
```

Then open **http://localhost:8001** in your browser.

> **Note:** If running Milvus in Docker and Attu on the same host, use `localhost:19530`. If Attu is also in Docker, use the Milvus container name: `document_milvus:19530`.

### 2. pymilvus CLI (Python)

You can connect and inspect via Python:

```python
from pymilvus import connections, Collection, utility

connections.connect(alias="default", host="localhost", port="19530")

# List collections
print(utility.list_collections())

# Get collection stats
collection = Collection("document_vectors")
collection.load()
print(f"Entity count: {collection.num_entities}")

# Peek at first 5 rows
collection.query(expr="", output_fields=["document_id", "chunk_text", "page_number"], limit=5)
```

### 3. MinIO Console

Milvus stores index files in MinIO. Access the MinIO web console at:

- **URL:** http://localhost:9001
- **Username:** `minioadmin`
- **Password:** `minioadmin`

The bucket used by Milvus is typically named `milvus-bucket` (auto-created).

---

## Useful Commands

```bash
# Check if Milvus is running
docker ps | grep milvus

# View Milvus logs
docker logs document_milvus

# Check etcd health
docker exec document_etcd etcdctl endpoint health

# Check MinIO health
docker exec document_minio curl -f http://localhost:9000/minio/health/live

# Restart all vector infra
docker compose restart etcd minio milvus

# Full reset (⚠️ deletes all vector data)
docker compose down -v  # removes volumes
docker compose up -d    # fresh start
```

---

## Key Libraries

| Library | Version | Purpose |
|---|---|---|
| `pymilvus` | latest | Python SDK for Milvus |
| `sentence-transformers` | latest | Generates embeddings via `all-MiniLM-L6-v2` |

Both are listed in `backend/requirements.txt`.
