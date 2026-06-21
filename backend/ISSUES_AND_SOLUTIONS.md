# Issues and Solutions Log

## Issue 1: SQLAlchemy MissingGreenlet Error

### Problem
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
```

### Root Cause
The Alembic configuration in `alembic.ini` was using an **async database URL** (`postgresql+asyncpg://`) but Alembic's migration runner requires a **synchronous engine** to run migrations. Async drivers like asyncpg cannot be used in synchronous contexts.

### Solution
Changed the database URL in `alembic.ini` from:
```
sqlalchemy.url = postgresql+asyncpg://document_user:password@localhost:5432/document_db
```

To:
```
sqlalchemy.url = postgresql://document_user:password@localhost:5432/document_db
```

This allows Alembic to use the synchronous `psycopg2` driver for migrations, while the FastAPI app continues to use the async `asyncpg` driver.

---

## Issue 2: ModuleNotFoundError - psycopg2 Not Installed

### Problem
```
ModuleNotFoundError: No module named 'psycopg2'
```

### Root Cause
The `psycopg2-binary` package was not included in `requirements.txt`. When trying to use the synchronous PostgreSQL driver, the venv didn't have the necessary psycopg2 module installed.

### Solution

1. **Added psycopg2-binary to requirements.txt:**
   ```
   fastapi
   uvicorn[standard]
   
   sqlalchemy
   asyncpg
   psycopg2-binary
   alembic
   ```

2. **Installed the package in the virtual environment:**
   ```bash
   source venv/bin/activate
   pip install --upgrade pip setuptools
   pip install psycopg2-binary
   ```

---

## Issue 3: Corrupted Migration History

### Problem
```
ERROR [alembic.util.messaging] Can't locate revision identified by '8b8eac27e307'
FAILED: Can't locate revision identified by '8b8eac27e307'
```

### Root Cause
The database's `alembic_version` table contained a reference to a migration revision (`8b8eac27e307`) that no longer existed in the codebase. The `migrations/versions/` directory was empty, causing a mismatch between the database state and the migration files.

### Solution
Cleared the corrupted migration history by executing:
```python
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

with engine.connect() as conn:
    conn.execute(text("DELETE FROM alembic_version"))
    conn.commit()
    print("Cleared alembic_version table")
```

This reset Alembic's tracking, allowing it to generate migrations from scratch.

---

## Issue 4: Syntax Error in main.py

### Problem
```python
app.include_router/(router)  # Invalid syntax
```

### Solution
Fixed the typo:
```python
app.include_router(router)  # Corrected
```

---

## Final Resolution

Successfully created and applied the initial migration:
```
alembic revision --autogenerate -m "add file path to documents"
alembic upgrade head
```

### Migration Generated
- **File:** `migrations/versions/9159f102c13f_add_file_path_to_documents.py`
- **Status:** Applied successfully

### Architecture Now In Place
- ✅ **For Migrations (Alembic):** Uses synchronous `psycopg2` driver
- ✅ **For Application (FastAPI):** Uses async `asyncpg` driver
- ✅ **Database:** PostgreSQL at `localhost:5432/document_db`
- ✅ **Migration History:** Clean and tracked in `alembic_version` table

---

## Lessons Learned

1. **Async vs Sync Drivers:** Always use synchronous database drivers for Alembic migrations, even if your application uses async drivers
2. **Virtual Environment:** Ensure packages are installed in the correct virtual environment, not globally
3. **Migration Integrity:** Keep `migrations/versions/` directory in sync with the database's `alembic_version` table
4. **Configuration:** Use different URLs for different components when needed (async for app, sync for migrations)

