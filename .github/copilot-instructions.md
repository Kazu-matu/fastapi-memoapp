# AI Development Instructions — FastAPI + Jinja2 + SQLAlchemy (Async)

> **For AI assistants**: GitHub Copilot, Cursor, Claude, ChatGPT, Gemini, and others.
> Follow every rule in this file precisely. If you are unsure, ask the developer before proceeding.
>
> **For beginners**: Every rule includes a "Why?" explanation. Read those before asking the AI to implement anything.

---

## 0. Core Philosophy

This project prioritizes **safety**, **maintainability**, **extensibility**, and **security** in that order.

| Priority | Principle | Practical meaning |
|---|---|---|
| 1 | Safety | Never lose data. Never expose secrets. Always rollback on error. |
| 2 | Maintainability | Each file has one responsibility. Logic lives in one place only. |
| 3 | Extensibility | Add features without rewriting existing code. |
| 4 | Security | Validate all input. Never trust the client. |

When these conflict, always choose the higher-priority value.

---

## 1. Technology Stack (DO NOT CHANGE)

| Category | Technology | Version | Why this choice |
|---|---|---|---|
| Language | Python | 3.12+ | Modern async support, type hints, performance |
| Web Framework | FastAPI | 0.115+ | Automatic validation, OpenAPI docs, async-native |
| Template Engine | Jinja2 | 3.1+ (SSR) | No JS build step; simpler for beginners |
| ORM | SQLAlchemy | 2.x async | Type-safe DB access; prevents SQL injection |
| Validation | Pydantic | v2 | Catches bad data at the boundary, not deep in logic |
| DB Driver (dev) | aiosqlite | latest | Zero setup; file-based; same SQL as PostgreSQL |
| DB Driver (prod) | asyncpg | latest | High-performance PostgreSQL async driver |
| Config | python-dotenv | latest | Keeps secrets out of source code |
| Package Manager | uv | latest | Faster than pip; reproducible installs |
| Testing | pytest + pytest-asyncio | latest | Industry standard; async-aware |
| E2E Testing | Playwright | latest | Headless browser; catches UI regressions |

### Non-negotiable constraints

- **Package manager**: `uv` only. Never use `pip`, `poetry`, or `pipenv`.
  > Why: `uv` produces a lockfile (`uv.lock`) that guarantees every developer and CI environment installs the exact same versions. pip does not guarantee this.

- **Frontend**: Jinja2 SSR only. Never use React, Vue, Next.js, or any JS framework.
  > Why: Adding a JS frontend doubles the complexity (two build pipelines, two sets of dependencies, CORS issues). For CRUD apps, SSR is simpler, faster to develop, and easier to maintain.

- **DB access**: SQLAlchemy async mode only. Never use synchronous sessions.
  > Why: FastAPI is async. Mixing sync DB calls blocks the event loop and degrades performance for all users simultaneously.

- **Form POST handling**: Always redirect with `RedirectResponse(..., status_code=303)` (PRG pattern).
  > Why: Without this, pressing the browser Back button or refreshing re-submits the form, creating duplicate data.

---

## 2. Directory Structure

Every file has exactly one responsibility. Do not put logic where it does not belong.

```
project/
├── main.py               # ONLY: app init, middleware, router registration
├── config.py             # ONLY: read settings from .env
├── db.py                 # ONLY: engine and session factory
├── init_database.py      # ONLY: create/drop tables (never run in production automatically)
├── pyproject.toml        # dependency definitions
├── .env                  # NOT committed — contains secrets
├── .env.example          # Committed — shows required keys without values
├── .gitignore
│
├── models/               # SQLAlchemy ORM models (what the DB looks like)
│   └── {table_name}.py
│
├── schemas/              # Pydantic schemas (what the API accepts and returns)
│   └── {table_name}.py
│
├── cruds/                # All DB read/write logic lives here — nowhere else
│   └── {table_name}.py
│
├── routers/              # URL routing only — no business logic here
│   ├── {table_name}.py   # REST API endpoints (/api/...)
│   └── pages.py          # Jinja2 page endpoints (/)
│
├── templates/            # HTML files rendered by Jinja2
│   ├── base.html         # shared layout (nav, head, footer)
│   ├── index.html
│   └── edit.html
│
├── static/
│   └── styles.css        # all styles go here — no inline styles
│
├── tests/
│   ├── conftest.py       # shared fixtures (DB setup, test client)
│   ├── unit/
│   │   └── test_schemas.py
│   ├── integration/
│   │   └── test_api.py
│   └── e2e/
│       └── test_{app_name}.py
│
└── docs/
    ├── 01_要件定義.md       # what to build (required before coding)
    ├── 02_仕様書.md         # how to build it (ER, API, screens)
    ├── 03_テスト仕様書.md   # how to verify it (test cases)
    └── 04_報告書.md         # results (test results, bugs, deploy request)
```

### One-responsibility rule (enforce strictly)

| File | Allowed | Forbidden |
|---|---|---|
| `main.py` | register routers, add middleware | any business logic, DB queries |
| `config.py` | read env vars, define Settings class | any computation or side effects |
| `db.py` | create engine, session factory | model definitions, queries |
| `models/` | SQLAlchemy column definitions | validation logic, DB queries |
| `schemas/` | Pydantic field definitions, validators | DB queries, HTTP calls |
| `cruds/` | DB queries, transactions, history writes | HTTP concerns, template logic |
| `routers/` | receive request, call crud, return response | direct DB access, business rules |
| `templates/` | display data from context | fetch calls, business logic in JS |

---

## 3. Implementation Order (ALWAYS follow this sequence)

```
1. models/     → columns, relationships, constraints
      ↓
2. schemas/    → what the API receives and returns
      ↓
3. cruds/      → how data is read and written
      ↓
4. routers/    → which URL calls which crud (API first, then pages)
      ↓
5. templates/  → how pages look
      ↓
6. tests/      → unit tests first, then integration, then E2E
      ↓
7. docs/       → spec and test report
```

> **Why this order?** Each layer depends on the one above it. If you write a router before the schema, you will rewrite the router when the schema changes. Start from the data model and work outward.

---

## 4. Coding Rules

### 4-1. models/ — Table Definitions

Every table MUST include the following audit and soft-delete columns:

```python
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from db import Base

class Item(Base):
    __tablename__ = "items"  # REQUIRED — never omit

    id         = Column(Integer, primary_key=True, autoincrement=True)

    # --- audit columns (REQUIRED on every table) ---
    is_deleted = Column(Boolean, default=False, nullable=False)  # soft-delete flag
    deleted_at = Column(DateTime, nullable=True)                 # set when deleted
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.now, nullable=True)
    created_by = Column(String(100), nullable=False)             # who created this row
    updated_by = Column(String(100), nullable=True)              # who last modified

# REQUIRED: create a paired history table for every main table
class ItemHistory(Base):
    __tablename__ = "item_histories"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    item_id     = Column(Integer, nullable=False)   # FK to items.id (snapshot — not a real FK)
    operation   = Column(String(20), nullable=False) # "CREATE" | "UPDATE" | "DELETE"
    operated_at = Column(DateTime, default=datetime.now, nullable=False)
    operated_by = Column(String(100), nullable=False)
    # Mirror all business columns here as a snapshot
```

> **Why soft-delete?** Physical deletion (`DELETE FROM items`) is irreversible. Soft-delete (`is_deleted = True`) means you can restore data, audit what was deleted, and maintain referential integrity.

> **Why a history table?** `updated_at` only tells you when a row changed, not what it was before. A history table gives you a complete audit trail — essential for any app used by more than one person.

**FORBIDDEN in models:**
- `nullable=True` unless the column genuinely allows NULL at the business level
- Omitting `__tablename__`
- Using `db.delete()` anywhere in the codebase

---

### 4-2. schemas/ — Pydantic Validation

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# --- Input schemas (what the API accepts) ---

class ItemCreateSchema(BaseModel):
    title:    str = Field(min_length=1, max_length=100)   # empty string is rejected
    content:  str = Field(min_length=1, max_length=2000)
    priority: int = Field(ge=1, le=5)                     # 1–5 only

    @field_validator("title")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        # Prevent "   " (spaces only) from passing min_length check
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped

class ItemUpdateSchema(BaseModel):
    title:    str | None = Field(default=None, min_length=1, max_length=100)
    content:  str | None = Field(default=None, min_length=1, max_length=2000)
    priority: int | None = Field(default=None, ge=1, le=5)

# --- Output schemas (what the API returns) ---

class ItemSchema(BaseModel):
    model_config = {"from_attributes": True}  # REQUIRED for SQLAlchemy model conversion

    id:         int
    title:      str
    content:    str
    priority:   int
    created_at: datetime
    updated_at: datetime | None
    created_by: str
    # NEVER include: is_deleted, deleted_at, or any secret fields

class ItemHistorySchema(BaseModel):
    model_config = {"from_attributes": True}
    id:          int
    item_id:     int
    operation:   str
    operated_at: datetime
    operated_by: str

class ResponseSchema(BaseModel):
    message: str  # used for operation results: {"message": "Created successfully"}
```

**FORBIDDEN in schemas:**
- `Field(..., example=...)` — deprecated in Pydantic v2; use `json_schema_extra` instead
- Secrets (`password`, `token`, `api_key`) in any response schema
- Business logic or DB access inside validators

---

### 4-3. cruds/ — DB Operations

All database access lives here. Routers call these functions; they never query the DB directly.

```python
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.item import Item, ItemHistory
from schemas.item import ItemCreateSchema, ItemUpdateSchema

# --- READ ---

async def get_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(
        select(Item)
        .where(Item.is_deleted == False)  # ALWAYS filter soft-deleted rows
        .order_by(Item.created_at.desc())
    )
    return list(result.scalars().all())

async def get_item_by_id(db: AsyncSession, item_id: int) -> Item | None:
    result = await db.execute(
        select(Item).where(Item.id == item_id, Item.is_deleted == False)
    )
    return result.scalar_one_or_none()

# --- WRITE (REQUIRED try/except pattern) ---

async def insert_item(db: AsyncSession, data: ItemCreateSchema, user: str) -> Item:
    try:
        new = Item(
            title=data.title,
            content=data.content,
            priority=data.priority,
            created_by=user,
            updated_by=user,
        )
        db.add(new)
        await db.flush()  # assigns new.id WITHOUT committing — required before history

        db.add(ItemHistory(
            item_id=new.id,
            operation="CREATE",
            operated_by=user,
            # mirror business fields here
        ))
        await db.commit()
        await db.refresh(new)
        return new
    except Exception:
        await db.rollback()  # ALWAYS rollback on any error
        raise               # NEVER swallow — let the router handle it

async def update_item(db: AsyncSession, item: Item, data: ItemUpdateSchema, user: str) -> Item:
    try:
        if data.title    is not None: item.title    = data.title
        if data.content  is not None: item.content  = data.content
        if data.priority is not None: item.priority = data.priority
        item.updated_by = user

        db.add(ItemHistory(item_id=item.id, operation="UPDATE", operated_by=user))
        await db.commit()
        await db.refresh(item)
        return item
    except Exception:
        await db.rollback()
        raise

async def delete_item(db: AsyncSession, item: Item, user: str) -> None:
    try:
        item.is_deleted = True
        item.deleted_at = datetime.now()
        item.updated_by = user

        db.add(ItemHistory(item_id=item.id, operation="DELETE", operated_by=user))
        await db.commit()
    except Exception:
        await db.rollback()
        raise
```

**FORBIDDEN in cruds:**
- `except Exception: pass` — always re-raise
- `db.delete(model)` — no physical deletes
- Creating history records before `await db.flush()` (the ID does not exist yet)
- Any code that directly returns HTTP responses (that belongs in routers)

---

### 4-4. routers/ — Endpoints

Routers are thin: validate input → call crud → return response. No logic lives here.

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from cruds import item as item_crud
from schemas.item import ItemCreateSchema, ItemSchema, ResponseSchema

router = APIRouter(prefix="/api/items", tags=["items"])

# Dependency: look up item or raise 404 — reuse this across GET/PUT/DELETE
async def get_item_or_404(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await item_crud.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.get("/", response_model=list[ItemSchema], status_code=200)
async def list_items(db: AsyncSession = Depends(get_db)):
    return await item_crud.get_items(db)

@router.post("/", response_model=ItemSchema, status_code=201)
async def create_item(data: ItemCreateSchema, db: AsyncSession = Depends(get_db)):
    return await item_crud.insert_item(db, data, user="system")

@router.get("/{item_id}", response_model=ItemSchema, status_code=200)
async def read_item(item=Depends(get_item_or_404)):
    return item

@router.put("/{item_id}", response_model=ItemSchema, status_code=200)
async def update_item(
    data: ItemUpdateSchema,
    item=Depends(get_item_or_404),
    db: AsyncSession = Depends(get_db),
):
    return await item_crud.update_item(db, item, data, user="system")

@router.delete("/{item_id}", response_model=ResponseSchema, status_code=200)
async def delete_item(item=Depends(get_item_or_404), db: AsyncSession = Depends(get_db)):
    await item_crud.delete_item(db, item, user="system")
    return {"message": "Deleted successfully"}
```

**Page router** (Jinja2):

```python
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
# REQUIRED: absolute path — relative paths break when uvicorn is started from a different directory
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/")
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    items = await item_crud.get_items(db)
    return templates.TemplateResponse(request, "index.html", {"items": items})
    # NOTE: do NOT put "request" inside the dict — Starlette 1.x takes it as the first argument

@router.post("/items/create")
async def create_item_page(
    request: Request,
    title: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    data = ItemCreateSchema(title=title, ...)
    await item_crud.insert_item(db, data, user="system")
    return RedirectResponse("/?msg=created", status_code=303)  # PRG pattern — ALWAYS 303
```

**FORBIDDEN in routers:**
- Direct `db.execute()` or `db.add()` calls
- Business rules (conditions, calculations)
- `status_code=302` on redirects (use 303 — 302 can re-POST on some browsers)

---

### 4-5. templates/ — Jinja2 HTML

```html
<!-- Every page extends base.html -->
{% extends "base.html" %}

{% block content %}

<!-- Flash messages — always check for msg parameter -->
{% if msg == "created" %}
  <div class="flash flash--success" role="alert">Created successfully.</div>
{% elif msg == "updated" %}
  <div class="flash flash--success" role="alert">Updated successfully.</div>
{% elif msg == "deleted" %}
  <div class="flash flash--warning" role="alert">Deleted.</div>
{% elif msg == "error" %}
  <div class="flash flash--error" role="alert">An error occurred. Please try again.</div>
{% endif %}

<!-- Delete form: ALWAYS require confirmation -->
<form method="post" action="/items/{{ item.id }}/delete"
      onsubmit="return confirm('Delete this item? This cannot be undone.')">
  <!-- CSRF token if authentication is added later -->
  <button type="submit" class="btn btn--danger">Delete</button>
</form>

<!-- Escape all user-generated content (Jinja2 auto-escapes by default — never use | safe on user data) -->
<p>{{ item.title }}</p>         {# safe — auto-escaped #}
<p>{{ item.title | safe }}</p>  {# DANGEROUS — XSS risk — never use on user input #}

{% endblock %}
```

**FORBIDDEN in templates:**
- `fetch()`, `axios`, or any XHR/API calls — violates SSR principle
- `| safe` filter on any user-provided content — XSS vulnerability
- `<script>` tags containing business logic
- Inline `style=""` attributes — use `styles.css`
- Hardcoded URLs — use route variables or URL parameters

---

### 4-6. db.py — Database Configuration

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from config import DATABASE_URL, DEBUG

def _build_engine():
    if DATABASE_URL.startswith("sqlite"):
        # SQLite: NullPool because SQLite does not support connection pooling across threads
        return create_async_engine(
            DATABASE_URL,
            echo=DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    # PostgreSQL: connection pool for performance
    return create_async_engine(
        DATABASE_URL,
        echo=DEBUG,
        pool_pre_ping=True,   # test connections before use (detects dropped connections)
        pool_size=5,          # keep 5 connections open
        max_overflow=10,      # allow up to 10 extra under load
        pool_timeout=30,      # wait max 30s for a free connection
        pool_recycle=1800,    # recycle connections every 30 min (prevents stale connections)
    )

engine = _build_engine()
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        # Session closes automatically — no need for try/finally here
```

**FORBIDDEN in db.py:**
- `pool_pre_ping=True` on SQLite (NullPool makes it meaningless and can cause errors)
- `sessionmaker` instead of `async_sessionmaker` (deprecated in SQLAlchemy 2.x)
- Model imports (circular import risk)

---

## 5. Error Handling

Consistent error handling makes debugging faster and prevents information leakage to users.

### Global exception handler (add to main.py)

```python
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full traceback internally
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    # Return a safe message to the user — NEVER expose stack traces
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )
```

### HTTPException conventions

```python
# 404 — resource not found
raise HTTPException(status_code=404, detail="Item not found")

# 422 — invalid input (FastAPI raises this automatically from Pydantic)

# 409 — conflict (e.g. duplicate unique value)
raise HTTPException(status_code=409, detail="An item with this title already exists")

# 403 — forbidden (authenticated but not allowed)
raise HTTPException(status_code=403, detail="You do not have permission to do this")

# FORBIDDEN: never expose internal details
raise HTTPException(status_code=500, detail=str(e))          # exposes stack trace
raise HTTPException(status_code=500, detail=repr(exc))       # exposes internal state
raise HTTPException(status_code=404, detail=f"SELECT * FROM items WHERE id={item_id} returned no rows")
```

### Page error handling (Jinja2 routers)

```python
@router.post("/items/{item_id}/update")
async def update_item_page(request: Request, item_id: int, ...):
    try:
        ...
        return RedirectResponse(f"/items/{item_id}?msg=updated", status_code=303)
    except Exception:
        logger.exception("Failed to update item %d", item_id)
        return RedirectResponse(f"/items/{item_id}?msg=error", status_code=303)
        # Redirect to the same page with an error message — never show raw errors to users
```

---

## 6. Security Rules

### Input and output safety

```
✅ Validate ALL user input through Pydantic schemas — never trust raw form data
✅ Use SQLAlchemy ORM / select() for ALL queries — never build SQL strings
✅ Jinja2 auto-escapes HTML by default — NEVER bypass with | safe on user data
✅ Strip and validate string fields (whitespace-only strings must be rejected)
✅ Enforce min/max lengths on all string fields
✅ Enforce numeric ranges on all numeric fields (ge=, le=, gt=, lt=)
```

### Secrets and configuration

```
✅ Never commit .env — it must be in .gitignore before the first commit
✅ Never hardcode secrets in source code (DB URLs, API keys, passwords)
✅ Never log secret values, even at DEBUG level
✅ Never include secrets in HTTPException.detail messages
✅ Never include is_deleted, deleted_at, or internal fields in response schemas
```

### HTTP security headers (add to main.py)

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### Required .gitignore entries (must exist before first `git add`)

```gitignore
# Secrets
.env

# Database files
*.sqlite
*.db

# Python cache
__pycache__/
*.pyc
*.pyo

# Virtual environment
.venv/
venv/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

### Required .env.example (commit this — it is the template, not the secret)

```env
# Application
APP_NAME=MyApp
DEBUG=false

# Database
# Development (default):
DATABASE_URL=sqlite+aiosqlite:///./app.sqlite
# Production:
# DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

---

## 7. Logging

Logging lets you understand what happened when something goes wrong. Without it, bugs in production are nearly impossible to diagnose.

### Setup (add to main.py)

```python
import logging

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
```

### Logging conventions

```python
# Use module-level loggers (one per file)
logger = logging.getLogger(__name__)

# INFO: normal operations worth recording
logger.info("Item %d created by %s", item.id, user)
logger.info("Item %d deleted by %s", item_id, user)

# WARNING: unexpected but recoverable
logger.warning("Item %d not found — may have been deleted", item_id)

# ERROR/EXCEPTION: unexpected failures (use .exception to include traceback)
logger.exception("Failed to create item for user %s", user)

# FORBIDDEN
logger.debug("DB password: %s", db_password)   # never log secrets
logger.info(request.body())                     # never log raw request bodies
logger.error(str(exc))                          # use .exception() instead to get traceback
```

---

## 8. Pagination and Filtering (for list endpoints)

All list endpoints that could return more than ~50 rows MUST support pagination.

```python
# Schema for query parameters
class ItemFilterSchema(BaseModel):
    page:     int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)  # cap at 100 to prevent abuse
    keyword:  str | None = Field(default=None, max_length=100)

# crud function
async def get_items(db: AsyncSession, filters: ItemFilterSchema) -> tuple[list[Item], int]:
    query = select(Item).where(Item.is_deleted == False)

    if filters.keyword:
        like = f"%{filters.keyword}%"
        query = query.where(Item.title.ilike(like))  # case-insensitive search

    # Get total count before pagination
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Apply pagination
    offset = (filters.page - 1) * filters.per_page
    result = await db.execute(query.order_by(Item.created_at.desc()).offset(offset).limit(filters.per_page))
    return list(result.scalars().all()), total

# router
@router.get("/", response_model=dict)
async def list_items(filters: ItemFilterSchema = Depends(), db: AsyncSession = Depends(get_db)):
    items, total = await item_crud.get_items(db, filters)
    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "pages": (total + filters.per_page - 1) // filters.per_page,
    }
```

---

## 9. Testing Rules

Tests give you confidence that the code works and catch regressions when you change something.

### Core principles

```
✅ Test DB must be in-memory SQLite — never connect to the real DB
✅ Reset the DB schema before every test function — no shared state
✅ Each test must be able to run independently in any order
✅ Write unit tests before integration tests
✅ Tests must pass before declaring any feature complete
```

### Required conftest.py (do not change this pattern)

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # reuse the same connection (required for in-memory SQLite)
)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # create tables
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)     # drop tables — clean state

@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

### Minimum required test coverage

| Type | Target | Cases to cover |
|---|---|---|
| Unit | Schema | valid input, empty string rejected, max-length exceeded, missing required field |
| Integration | `POST /api/items/` | success → 201, validation error → 422 |
| Integration | `GET /api/items/` | returns empty list, returns multiple items |
| Integration | `GET /api/items/{id}` | found → 200, not found → 404 |
| Integration | `PUT /api/items/{id}` | success → 200, not found → 404, partial update works |
| Integration | `DELETE /api/items/{id}` | success → 200, subsequent GET → 404 |
| Integration | History | after insert, one CREATE history record exists |
| Integration | Soft delete | deleted item does not appear in list |

### Test example

```python
import pytest

@pytest.mark.asyncio
async def test_create_item_success(client):
    response = await client.post("/api/items/", json={"title": "Test", "content": "Body", "priority": 1})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"
    assert "id" in data
    assert "is_deleted" not in data  # internal field must not be exposed

@pytest.mark.asyncio
async def test_create_item_empty_title(client):
    response = await client.post("/api/items/", json={"title": "", "content": "Body", "priority": 1})
    assert response.status_code == 422  # Pydantic rejects empty title

@pytest.mark.asyncio
async def test_deleted_item_not_in_list(client):
    create = await client.post("/api/items/", json={"title": "To delete", "content": "x", "priority": 1})
    item_id = create.json()["id"]
    await client.delete(f"/api/items/{item_id}")
    items = await client.get("/api/items/")
    assert all(i["id"] != item_id for i in items.json())
```

---

## 10. Documentation Rules

> **Documentation is not optional.** Every project MUST maintain the four documents below.
> An undocumented system cannot be handed over, audited, or approved by an IT department.

### Required header for every document

```markdown
| Field | Value |
|---|---|
| Created | YYYY-MM-DD |
| Last Updated | YYYY-MM-DD |
| Version | v1.0 |
| Author | Name |
```

Version rules:
- Start at `v1.0`
- Increment to `v1.1`, `v1.2` for additions and fixes
- Jump to `v2.0` for major structural changes
- **Update "Last Updated" and the version number every time the file changes — no exceptions**

### Mandatory documents (all four MUST exist before release)

| File | When to create | When to update | Content |
|---|---|---|---|
| `docs/01_要件定義.md` | Before writing any code | When scope, requirements, or constraints change | Purpose, scope, functional/non-functional requirements, stakeholders |
| `docs/02_仕様書.md` | After requirements are confirmed | When DB schema, API, or screens change | ER diagram, API list, screen spec, processing flows |
| `docs/03_テスト仕様書.md` | Before writing tests | When test cases are added or changed | Test policy, unit/integration/E2E test specs |
| `docs/04_報告書.md` | After tests pass | When test results, bugs, or deployment info change | Test results, bug list, deliverables, deployment request |
| `README.md` | After implementation | When setup steps or commands change | Setup, launch, test, DB switch |

### When the AI must prompt the user to update documents

The AI **must proactively remind** the user to update documentation in these situations:

```
✅ After adding a new table or column        → update 02_仕様書.md (ER diagram)
✅ After adding or changing an API endpoint  → update 02_仕様書.md (API list)
✅ After adding or changing a screen         → update 02_仕様書.md (screen spec)
✅ After adding a new test case              → update 03_テスト仕様書.md
✅ After running tests                       → update 04_報告書.md (test results)
✅ After fixing a bug found in testing       → update 04_報告書.md (bug list)
✅ After changing startup or setup commands  → update README.md
```

**Reminder phrasing to use:**
> "The DB schema changed. Please update `docs/02_仕様書.md` section 4 (ER diagram) and increment the version to v1.x."

### Use Mermaid to make documents visual

Every document that describes structure, flow, or relationships **must include at least one Mermaid diagram**.
Plain prose alone is not sufficient — diagrams reduce misunderstanding and speed up review.

#### Required diagrams by document

| Document | Required Mermaid diagram | Diagram type |
|---|---|---|
| `02_仕様書.md` | ER diagram (all tables and relationships) | `erDiagram` |
| `02_仕様書.md` | Registration flow (POST → cruds → DB → redirect) | `sequenceDiagram` |
| `02_仕様書.md` | PRG pattern overview | `flowchart LR` |
| `01_要件定義.md` | Business flow (current vs. improved) | `flowchart TD` |
| `04_報告書.md` | Deployment architecture | `flowchart LR` |

#### ER diagram — standard template

````markdown
```mermaid
erDiagram
    memos {
        int memo_id PK
        string title
        string description
        string priority
        bool is_deleted
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }
    memo_histories {
        int history_id PK
        int memo_id FK
        string operation
        string title
        datetime created_at
        string created_by
    }
    memos ||--o{ memo_histories : "1 to many"
```
````

#### Sequence diagram — PRG registration flow

````markdown
```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Browser as ブラウザ
    participant Router as routers/pages.py
    participant Crud as cruds/memo.py
    participant DB as SQLite / PostgreSQL

    User->>Browser: フォーム入力 → 登録ボタン
    Browser->>Router: POST /memos
    Router->>Crud: insert_memo(db, data, user)
    Crud->>DB: INSERT memos + INSERT memo_histories
    DB-->>Crud: commit OK
    Crud-->>Router: Memo object
    Router-->>Browser: 303 Redirect /?msg=created
    Browser->>Router: GET /?msg=created
    Router-->>Browser: 200 HTML（一覧 + フラッシュメッセージ）
```
````

#### Flowchart — business flow

````markdown
```mermaid
flowchart TD
    A[業務開始] --> B{メモを探す}
    B -->|あり| C[詳細確認]
    B -->|なし| D[新規登録]
    C --> E{変更が必要?}
    E -->|はい| F[更新]
    E -->|いいえ| G[完了]
    F --> G
    D --> G
```
````

**AI instructions for Mermaid:**

- When writing or updating `02_仕様書.md`, always include the ER diagram with **all current tables and columns**.
- When a table or column changes, **update the ER diagram immediately** in the same response.
- When writing `01_要件定義.md`, include a `flowchart TD` showing the business flow (current state → problem → improved state).
- Never describe a flow or relationship in prose only — add a diagram.
- Use Japanese labels inside diagrams (`actor User as ユーザー`) to match the audience.

### Required README.md sections

1. One-paragraph overview of what the app does
2. Requirements (Python version, uv)
3. Setup (`cp .env.example .env` → `uv sync` → `init_database.py` → `uvicorn`)
4. Switching to PostgreSQL for production
5. How to run tests
6. Project structure summary

---

## 11. Rules for AI Assistants

These rules exist to protect beginners from irreversible mistakes and ensure consistent, reviewable progress.

### Behavior rules — mandatory

1. **Follow the implementation order** (models → schemas → cruds → routers → templates → tests → docs).
   Never jump ahead. If the user asks to skip a step, explain why the order matters.

2. **Never add libraries or tools not listed in section 1.**
   If you believe an addition is necessary, state: "I recommend adding X because Y. Shall I proceed?"

3. **After writing code, always provide the command to verify it.**
   Example: `uv run uvicorn main:app --reload` then open `http://localhost:8000/docs`.

4. **Before fixing a bug, explain the cause.**
   State the file, line number, and reason. Then ask permission to fix.

5. **Before deleting or renaming any file, ask explicitly.**
   Example: "I need to rename `routers/item.py` to `routers/items.py`. Is that OK?"

6. **Before running `init_database.py`, warn the user.**
   "This will delete all existing data. Are you sure?"

7. **Never output, log, or display `.env` file contents.**

8. **Never run `git commit` or `git push` without explicit user instruction.**

9. **Never say "it's done" without evidence.**
   Accepted evidence: all tests pass (`pytest` output shown), or specific browser behavior confirmed.

10. **Before modifying existing code, state the reason.**
    "I'm changing X because Y. The affected lines are Z."

11. **When a beginner asks "why?", always explain the concept before implementing.**
    Do not just write code. Explain the tradeoff in plain language first.

12. **Generate one layer at a time.**
    Do not write models + schemas + cruds + routers in one response. Complete and confirm each layer.

13. **Documents must be created and kept up to date — always remind the user.**
    - At the start of a new project: "Please fill in `docs/01_要件定義.md` before we write any code."
    - After every schema/API/screen change: remind the user which doc section to update (see section 10).
    - At the end of testing: "Please record the test results in `docs/04_報告書.md`."
    - Never declare a feature complete if the relevant documentation is still a placeholder.

14. **Before any large change, recommend a git commit checkpoint.**
    A "large change" means: adding a new feature, refactoring an existing layer, changing the DB schema,
    or any change that touches more than two files.
    Use this exact phrasing:

    > "Before we make this change, I recommend saving your current progress:
    > ```
    > git add {list the specific files}
    > git commit -m "chore: checkpoint before {brief description of upcoming change}"
    > ```
    > This way you can easily revert if something goes wrong. Ready to proceed?"

    Wait for the user to confirm before starting the change.

### Recommended conversation flow

```
Step 1 — Fill in requirements (BEFORE writing any code)
  "Here is my idea: [purpose, screens, features, tables]"
  → AI helps fill in docs/01_要件定義.md
  → AI creates docs/02_仕様書.md (ER diagram, API list, screen list)

Step 2 — Review spec
  "Review the spec. Are there any issues?"
  → AI checks for missing fields, ambiguous requirements, security risks
  → User confirms → git commit: "docs: add requirements and spec"

Step 3 — Implement layer by layer
  [AI prompts a git commit before each layer if previous layer changed files]
  "Create models/item.py"         → AI writes + explains → remind to update 02_仕様書.md if schema changed
  "Create schemas/item.py"        → AI writes + explains
  "Create cruds/item.py"          → AI writes + explains
  "Create routers/item.py"        → AI writes + explains
  "Create routers/pages.py"       → AI writes + explains
  "Create the templates"          → AI writes + explains → remind to update 02_仕様書.md (screen spec)

Step 4 — Verify
  "Start the server and show me how to verify it works"
  → git commit: "feat: implement {feature name}"

Step 5 — Test
  "Create the test spec, write tests, then run them"
  → AI helps fill in docs/03_テスト仕様書.md
  → AI writes tests and runs them
  → AI reminds user to fill in docs/04_報告書.md with results
  → git commit: "test: add unit and integration tests"

Step 6 — Complete documentation
  "Update README.md and docs/04_報告書.md"
  → git commit: "docs: finalize test report and README"

Step 7 — Before any new feature or refactor
  → AI recommends: "git add + git commit before we start, so you have a safe restore point"
```

---

## 12. Common Mistakes (Beginner Reference)

These mistakes appear frequently. The AI must actively prevent them.

| Mistake | Symptom | Correct approach |
|---|---|---|
| Business logic in router | Router function is long and hard to test | Move all logic to `cruds/` |
| No `await db.flush()` before history | `IntegrityError`: FK value is NULL | Always `flush()` before referencing the new row's ID |
| `except Exception: pass` | Errors silently disappear; data is inconsistent | Always `rollback()` and `raise` |
| `db.delete(model)` | Data is permanently lost | Set `is_deleted = True` instead |
| `nullable=True` everywhere | Corrupt data accumulates over time | Only use `nullable=True` when NULL is a valid business value |
| Secrets in source code | Credentials exposed in git history | Always use `.env` |
| `| safe` on user content | XSS attack possible | Never use `| safe` on user-provided strings |
| Skipping `model_config` | `ValidationError` when converting SQLAlchemy model to schema | Add `model_config = {"from_attributes": True}` |
| `status_code=302` on redirect | Browser may re-POST on Back | Always use `303` for form POST redirects |
| Forgetting `await db.rollback()` | DB session left in broken state | Every write function must have `try/except` with `rollback()` |
| Direct DB access in router | Impossible to unit test the router in isolation | Routers only call `cruds/` functions |
| No pagination on list endpoints | App slows down as data grows | Always add `limit` / `offset` from day one |

---

## 13. Common Commands

```bash
# Install dependencies
uv sync                              # development (SQLite)
uv sync --extra prod                 # production (adds asyncpg for PostgreSQL)

# Initialize DB — WARNING: destroys all existing data
uv run python init_database.py

# Start development server
uv run uvicorn main:app --reload
uv run uvicorn main:app --reload --port 8001   # alternate port

# Check API docs (after starting server)
# http://localhost:8000/docs    ← Swagger UI
# http://localhost:8000/redoc   ← ReDoc

# Run tests
uv run pytest tests/unit/ tests/integration/ -v          # unit + integration
uv run pytest tests/ -v                                  # all tests including E2E
uv run pytest tests/integration/test_api.py -v -k "create"  # filter by name
uv run pytest tests/ --tb=short                          # shorter traceback

# Type checking (optional but recommended)
uv run mypy .

# Commit (only when explicitly instructed)
git add {specific files}    # never use git add . blindly
git commit -m "message"
git push
```
