"""
FastAPI + Jinja2 アプリ開発テンプレート生成スクリプト

使い方:
    python create_template.py <アプリ名>
    python create_template.py myapp

生成されるフォルダ:
    ./<アプリ名>/   ← このフォルダをコピーして開発開始

"""

import sys
import shutil
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  作成: {path.relative_to(path.parents[len(path.parts) - 2])}")


def touch(path: Path) -> None:
    """空のファイルを作成する（.gitkeep など）"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    print(f"  作成: {path.relative_to(path.parents[len(path.parts) - 2])}")


def copy_doc(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  コピー: {dst.relative_to(dst.parents[len(dst.parts) - 2])}")
    else:
        print(f"  スキップ（元ファイルなし）: {src}")


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("使い方: python create_template.py <アプリ名>")
        print("例    : python create_template.py myapp")
        sys.exit(1)

    app_name = sys.argv[1].strip()
    if not app_name.isidentifier():
        print(f"エラー: アプリ名 '{app_name}' は Python の識別子として有効な名前にしてください")
        print("       （英数字とアンダースコアのみ、先頭は英字）")
        sys.exit(1)

    # テンプレートの出力先
    here   = Path(__file__).parent          # このスクリプトの場所
    target = here.parent / app_name         # 出力先（一つ上の階層）

    if target.exists():
        ans = input(f"'{target}' はすでに存在します。上書きしますか？ [y/N]: ")
        if ans.lower() != "y":
            print("中断しました。")
            sys.exit(0)
        shutil.rmtree(target)

    print(f"\nテンプレートを作成しています: {target}\n")
    today = date.today().isoformat()

    # ─── 1. pyproject.toml ───────────────────────────────────────────
    write(target / "pyproject.toml", f"""\
[project]
name = "{app_name}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
    "pydantic>=2.0.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
    "python-dotenv>=1.0.0",
]

# 本番環境（PostgreSQL）: uv sync --extra prod
[project.optional-dependencies]
prod = [
    "asyncpg>=0.29.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "playwright>=1.44.0",
    "pytest-playwright>=0.5.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
""")

    # ─── 2. .env.example ─────────────────────────────────────────────
    write(target / ".env.example", f"""\
# 環境設定テンプレート
# このファイルをコピーして .env を作成してください
#   cp .env.example .env   （Mac/Linux）
#   copy .env.example .env （Windows）

APP_NAME={app_name}
DEBUG=false

# -------------------------------------------------------------------
# DB 設定（どちらか一方を有効にする）
# -------------------------------------------------------------------

# 開発環境: SQLite（ドライバ追加不要）
DATABASE_URL=sqlite+aiosqlite:///./{app_name}.sqlite

# 本番環境: PostgreSQL（uv sync --extra prod が必要）
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/{app_name}_db
""")

    # ─── 3. .gitignore ───────────────────────────────────────────────
    write(target / ".gitignore", """\
# 機密情報
.env

# DB ファイル
*.sqlite
*.db

# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
*.egg-info/
dist/
build/

# テスト
.pytest_cache/
htmlcov/
.coverage
tests/test_result.txt

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
""")

    # ─── 4. config.py ────────────────────────────────────────────────
    write(target / "config.py", """\
from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME    = os.getenv("APP_NAME", "MyApp")
DEBUG       = os.getenv("DEBUG", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.sqlite")
""")

    # ─── 5. db.py ────────────────────────────────────────────────────
    write(target / "db.py", """\
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import DATABASE_URL, DEBUG


class Base(DeclarativeBase):
    pass


def _build_engine():
    if DATABASE_URL.startswith("sqlite"):
        # SQLite: NullPool を使う（接続プールと相性が悪いため）
        return create_async_engine(
            DATABASE_URL,
            echo=DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    # PostgreSQL
    return create_async_engine(
        DATABASE_URL,
        echo=DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )


engine = _build_engine()
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    \"\"\"FastAPI Depends で使う DB セッションジェネレータ\"\"\"
    async with AsyncSessionLocal() as session:
        yield session
""")

    # ─── 6. main.py ──────────────────────────────────────────────────
    write(target / "main.py", f"""\
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from config import APP_NAME, DEBUG

# ── ロガー設定 ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── アプリ初期化 ─────────────────────────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    # 本番環境では Swagger UI を無効化する場合は以下を有効に
    # docs_url=None, redoc_url=None,
)

# ── 静的ファイル ─────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── セキュリティヘッダー ─────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── グローバルエラーハンドラ ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("予期しないエラー: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={{"detail": "サーバー内部でエラーが発生しました。管理者にお問い合わせください。"}},
    )

# ── ルーター登録 ─────────────────────────────────────────────────────
from routers import pages, item  # noqa: E402
app.include_router(pages.router)
app.include_router(item.router)
""")

    # ─── 7. init_database.py ─────────────────────────────────────────
    write(target / "init_database.py", """\
\"\"\"
テーブル初期化スクリプト

警告: 既存データは全て削除されます。本番環境では実行しないこと。

実行方法:
    uv run python init_database.py
\"\"\"
import asyncio
import sys

from db import Base, engine


async def init() -> None:
    print("テーブルを初期化します...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("完了しました。")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "--yes":
        ans = input("既存データが全て削除されます。続行しますか？ [y/N]: ")
        if ans.lower() != "y":
            print("中断しました。")
            sys.exit(0)
    asyncio.run(init())
""")

    # ─── 8. models/ ──────────────────────────────────────────────────
    write(target / "models" / "__init__.py", "")
    write(target / "models" / "item.py", """\
\"\"\"
SQLAlchemy モデルの雛形。
テーブル名・カラム名を実際のアプリに合わせて変更してください。
\"\"\"
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from db import Base


class Item(Base):
    __tablename__ = "items"  # ← 変更してください

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── ビジネスカラム（必要に応じて追加・変更） ──────────────────────
    title   = Column(String(100), nullable=False)
    content = Column(String(2000), nullable=False, default="")

    # ── 監査カラム（全テーブル共通・変更禁止） ───────────────────────
    is_deleted = Column(Boolean,  default=False,       nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.now, nullable=True)
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=True)


class ItemHistory(Base):
    \"\"\"変更履歴テーブル（全メインテーブルに必須）\"\"\"
    __tablename__ = "item_histories"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    item_id     = Column(Integer, nullable=False)
    operation   = Column(String(20),  nullable=False)  # CREATE / UPDATE / DELETE
    operated_at = Column(DateTime, default=datetime.now, nullable=False)
    operated_by = Column(String(100), nullable=False)
    # ビジネスカラムのスナップショット
    title   = Column(String(100), nullable=True)
    content = Column(String(2000), nullable=True)
""")

    # ─── 9. schemas/ ─────────────────────────────────────────────────
    write(target / "schemas" / "__init__.py", "")
    write(target / "schemas" / "item.py", """\
\"\"\"
Pydantic スキーマの雛形。
\"\"\"
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── 入力スキーマ ──────────────────────────────────────────────────────

class ItemCreateSchema(BaseModel):
    title:   str = Field(min_length=1, max_length=100)
    content: str = Field(default="", max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("タイトルは空白のみは使用できません")
        return stripped


class ItemUpdateSchema(BaseModel):
    title:   str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("タイトルは空白のみは使用できません")
        return v.strip() if v else v


# ── 出力スキーマ ──────────────────────────────────────────────────────

class ItemSchema(BaseModel):
    model_config = {"from_attributes": True}

    id:         int
    title:      str
    content:    str
    created_at: datetime
    updated_at: datetime | None
    created_by: str
    # 注意: is_deleted / deleted_at など内部フィールドは含めない


class ItemHistorySchema(BaseModel):
    model_config = {"from_attributes": True}

    id:          int
    item_id:     int
    operation:   str
    operated_at: datetime
    operated_by: str


class ResponseSchema(BaseModel):
    message: str
""")

    # ─── 10. cruds/ ──────────────────────────────────────────────────
    write(target / "cruds" / "__init__.py", "")
    write(target / "cruds" / "item.py", """\
\"\"\"
DB 操作ロジックの雛形。
\"\"\"
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.item import Item, ItemHistory
from schemas.item import ItemCreateSchema, ItemUpdateSchema

logger = logging.getLogger(__name__)


def _build_history(item: Item, operation: str, user: str) -> ItemHistory:
    return ItemHistory(
        item_id=item.id,
        operation=operation,
        operated_by=user,
        title=item.title,
        content=item.content,
    )


# ── READ ──────────────────────────────────────────────────────────────

async def get_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(
        select(Item)
        .where(Item.is_deleted == False)  # noqa: E712
        .order_by(Item.created_at.desc())
    )
    return list(result.scalars().all())


async def get_item_by_id(db: AsyncSession, item_id: int) -> Item | None:
    result = await db.execute(
        select(Item).where(Item.id == item_id, Item.is_deleted == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


# ── WRITE ─────────────────────────────────────────────────────────────

async def insert_item(db: AsyncSession, data: ItemCreateSchema, user: str) -> Item:
    try:
        new = Item(
            title=data.title,
            content=data.content,
            created_by=user,
            updated_by=user,
        )
        db.add(new)
        await db.flush()  # ID を確定させてから履歴を作る
        db.add(_build_history(new, "CREATE", user))
        await db.commit()
        await db.refresh(new)
        logger.info("Item created id=%d user=%s", new.id, user)
        return new
    except Exception:
        await db.rollback()
        raise


async def update_item(
    db: AsyncSession, item: Item, data: ItemUpdateSchema, user: str
) -> Item:
    try:
        if data.title   is not None: item.title   = data.title
        if data.content is not None: item.content = data.content
        item.updated_by = user
        db.add(_build_history(item, "UPDATE", user))
        await db.commit()
        await db.refresh(item)
        logger.info("Item updated id=%d user=%s", item.id, user)
        return item
    except Exception:
        await db.rollback()
        raise


async def delete_item(db: AsyncSession, item: Item, user: str) -> None:
    try:
        item.is_deleted = True
        item.deleted_at = datetime.now()
        item.updated_by = user
        db.add(_build_history(item, "DELETE", user))
        await db.commit()
        logger.info("Item deleted id=%d user=%s", item.id, user)
    except Exception:
        await db.rollback()
        raise
""")

    # ─── 11. routers/ ────────────────────────────────────────────────
    write(target / "routers" / "__init__.py", "")
    write(target / "routers" / "item.py", """\
\"\"\"
REST API エンドポイントの雛形 (/api/items)。
\"\"\"
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from cruds import item as item_crud
from db import get_db
from schemas.item import (
    ItemCreateSchema,
    ItemSchema,
    ItemUpdateSchema,
    ResponseSchema,
)

router = APIRouter(prefix="/api/items", tags=["items"])

# ── 共通依存：ID でアイテムを取得、なければ 404 ────────────────────────
async def get_item_or_404(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await item_crud.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="アイテムが見つかりません")
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
    return {"message": "削除しました"}
""")

    write(target / "routers" / "pages.py", """\
\"\"\"
Jinja2 ページルーターの雛形。
\"\"\"
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from cruds import item as item_crud
from db import get_db
from schemas.item import ItemCreateSchema

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)


@router.get("/")
async def index(request: Request, msg: str = "", db: AsyncSession = Depends(get_db)):
    items = await item_crud.get_items(db)
    return templates.TemplateResponse(request, "index.html", {
        "items": items,
        "msg": msg,
    })


@router.post("/items/create")
async def create_item_page(
    request: Request,
    title:   Annotated[str, Form()],
    content: Annotated[str, Form()] = "",
    db: AsyncSession = Depends(get_db),
):
    try:
        data = ItemCreateSchema(title=title, content=content)
        await item_crud.insert_item(db, data, user="system")
        return RedirectResponse("/?msg=created", status_code=303)
    except Exception:
        logger.exception("アイテム作成エラー")
        return RedirectResponse("/?msg=error", status_code=303)


@router.get("/items/{item_id}/edit")
async def edit_form(request: Request, item_id: int, db: AsyncSession = Depends(get_db)):
    item = await item_crud.get_item_by_id(db, item_id)
    if item is None:
        return RedirectResponse("/?msg=not_found", status_code=303)
    return templates.TemplateResponse(request, "edit.html", {"item": item})


@router.post("/items/{item_id}/edit")
async def update_item_page(
    request: Request,
    item_id: int,
    title:   Annotated[str, Form()],
    content: Annotated[str, Form()] = "",
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await item_crud.get_item_by_id(db, item_id)
        if item is None:
            return RedirectResponse("/?msg=not_found", status_code=303)
        from schemas.item import ItemUpdateSchema
        await item_crud.update_item(db, item, ItemUpdateSchema(title=title, content=content), user="system")
        return RedirectResponse(f"/?msg=updated", status_code=303)
    except Exception:
        logger.exception("アイテム更新エラー item_id=%d", item_id)
        return RedirectResponse(f"/items/{item_id}/edit?msg=error", status_code=303)


@router.post("/items/{item_id}/delete")
async def delete_item_page(
    request: Request,
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await item_crud.get_item_by_id(db, item_id)
        if item:
            await item_crud.delete_item(db, item, user="system")
        return RedirectResponse("/?msg=deleted", status_code=303)
    except Exception:
        logger.exception("アイテム削除エラー item_id=%d", item_id)
        return RedirectResponse("/?msg=error", status_code=303)
""")

    # ─── 12. templates/ ──────────────────────────────────────────────
    write(target / "templates" / "base.html", f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{% block title %}}{app_name}{{% endblock %}}</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header class="site-header">
    <h1 class="site-title">{app_name}</h1>
  </header>

  <main class="site-main">
    <!-- フラッシュメッセージ -->
    {{% if msg == "created" %}}
      <div class="flash flash--success" role="alert">登録しました。</div>
    {{% elif msg == "updated" %}}
      <div class="flash flash--success" role="alert">更新しました。</div>
    {{% elif msg == "deleted" %}}
      <div class="flash flash--info" role="alert">削除しました。</div>
    {{% elif msg == "not_found" %}}
      <div class="flash flash--error" role="alert">対象が見つかりませんでした。</div>
    {{% elif msg == "error" %}}
      <div class="flash flash--error" role="alert">エラーが発生しました。</div>
    {{% endif %}}

    {{% block content %}}{{% endblock %}}
  </main>

  <footer class="site-footer">
    <p>&copy; 2026 {app_name}</p>
  </footer>
</body>
</html>
""")

    write(target / "templates" / "index.html", """\
{% extends "base.html" %}

{% block title %}一覧{% endblock %}

{% block content %}
<section>
  <h2>一覧</h2>

  <!-- 登録フォーム -->
  <form method="post" action="/items/create" class="form-inline">
    <input type="text" name="title" placeholder="タイトル" required maxlength="100">
    <input type="text" name="content" placeholder="内容" maxlength="2000">
    <button type="submit" class="btn btn--primary">登録</button>
  </form>

  <!-- 一覧テーブル -->
  <table class="data-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>タイトル</th>
        <th>内容</th>
        <th>登録日時</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td>{{ item.id }}</td>
        <td>{{ item.title }}</td>
        <td>{{ item.content }}</td>
        <td>{{ item.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
        <td class="actions">
          <a href="/items/{{ item.id }}/edit" class="btn btn--secondary">編集</a>
          <form method="post" action="/items/{{ item.id }}/delete" style="display:inline"
                onsubmit="return confirm('削除してよいですか？')">
            <button type="submit" class="btn btn--danger">削除</button>
          </form>
        </td>
      </tr>
      {% else %}
      <tr>
        <td colspan="5" class="empty">データがありません。</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</section>
{% endblock %}
""")

    write(target / "templates" / "edit.html", """\
{% extends "base.html" %}

{% block title %}編集{% endblock %}

{% block content %}
<section>
  <h2>編集</h2>

  <form method="post" action="/items/{{ item.id }}/edit" class="form-block">
    <div class="form-group">
      <label for="title">タイトル</label>
      <input type="text" id="title" name="title"
             value="{{ item.title }}" required maxlength="100">
    </div>
    <div class="form-group">
      <label for="content">内容</label>
      <textarea id="content" name="content" maxlength="2000">{{ item.content }}</textarea>
    </div>
    <div class="form-actions">
      <button type="submit" class="btn btn--primary">更新</button>
      <a href="/" class="btn btn--secondary">キャンセル</a>
    </div>
  </form>
</section>
{% endblock %}
""")

    # ─── 13. static/styles.css ───────────────────────────────────────
    write(target / "static" / "styles.css", """\
/* ── リセット ─────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; font-size: 16px; color: #333; background: #f5f5f5; }

/* ── レイアウト ────────────────────────────────────────── */
.site-header { background: #2563eb; color: #fff; padding: 1rem 2rem; }
.site-title  { font-size: 1.5rem; font-weight: bold; }
.site-main   { max-width: 960px; margin: 2rem auto; padding: 0 1rem; }
.site-footer { text-align: center; padding: 2rem; color: #888; font-size: .875rem; }

/* ── フラッシュメッセージ ───────────────────────────────── */
.flash { padding: .75rem 1rem; border-radius: 4px; margin-bottom: 1rem; font-weight: 500; }
.flash--success { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
.flash--info    { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
.flash--error   { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

/* ── ボタン ────────────────────────────────────────────── */
.btn { display: inline-block; padding: .5rem 1rem; border-radius: 4px; border: none;
       cursor: pointer; font-size: .9rem; text-decoration: none; }
.btn--primary   { background: #2563eb; color: #fff; }
.btn--secondary { background: #e5e7eb; color: #374151; }
.btn--danger    { background: #dc2626; color: #fff; }
.btn:hover      { opacity: .85; }

/* ── フォーム ──────────────────────────────────────────── */
.form-inline { display: flex; gap: .5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.form-inline input { flex: 1; min-width: 160px; padding: .5rem; border: 1px solid #d1d5db; border-radius: 4px; }
.form-block .form-group { margin-bottom: 1rem; }
.form-block label { display: block; font-weight: 500; margin-bottom: .25rem; }
.form-block input, .form-block textarea {
  width: 100%; padding: .5rem; border: 1px solid #d1d5db; border-radius: 4px; font-size: 1rem;
}
.form-block textarea { min-height: 120px; resize: vertical; }
.form-actions { display: flex; gap: .5rem; margin-top: 1rem; }

/* ── テーブル ──────────────────────────────────────────── */
.data-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
.data-table th { background: #f9fafb; font-weight: 600; padding: .75rem 1rem; text-align: left; border-bottom: 2px solid #e5e7eb; }
.data-table td { padding: .75rem 1rem; border-bottom: 1px solid #f3f4f6; }
.data-table tbody tr:hover { background: #f9fafb; }
.data-table .empty { text-align: center; color: #9ca3af; }
.actions { white-space: nowrap; }
""")

    # ─── 14. tests/ ──────────────────────────────────────────────────
    write(target / "tests" / "__init__.py", "")
    write(target / "tests" / "unit" / "__init__.py", "")
    write(target / "tests" / "integration" / "__init__.py", "")
    write(target / "tests" / "e2e" / "__init__.py", "")

    write(target / "tests" / "conftest.py", """\
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
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
""")

    write(target / "tests" / "unit" / "test_schemas.py", """\
import pytest
from pydantic import ValidationError
from schemas.item import ItemCreateSchema


def test_create_schema_valid():
    s = ItemCreateSchema(title="テスト", content="内容")
    assert s.title == "テスト"


def test_create_schema_empty_title():
    with pytest.raises(ValidationError):
        ItemCreateSchema(title="")


def test_create_schema_blank_title():
    with pytest.raises(ValidationError):
        ItemCreateSchema(title="   ")


def test_create_schema_title_stripped():
    s = ItemCreateSchema(title="  前後スペース  ")
    assert s.title == "前後スペース"


def test_create_schema_missing_title():
    with pytest.raises(ValidationError):
        ItemCreateSchema()
""")

    write(target / "tests" / "integration" / "test_api.py", """\
import pytest


@pytest.mark.asyncio
async def test_list_items_empty(client):
    resp = await client.get("/api/items/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_item_success(client):
    resp = await client.post("/api/items/", json={"title": "テストアイテム", "content": "内容"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "テストアイテム"
    assert "id" in data
    assert "is_deleted" not in data  # 内部フィールドが漏れていないこと


@pytest.mark.asyncio
async def test_create_item_empty_title(client):
    resp = await client.post("/api/items/", json={"title": "", "content": "内容"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_item_not_found(client):
    resp = await client.get("/api/items/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_item(client):
    create = await client.post("/api/items/", json={"title": "更新前", "content": ""})
    item_id = create.json()["id"]
    resp = await client.put(f"/api/items/{item_id}", json={"title": "更新後"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "更新後"


@pytest.mark.asyncio
async def test_delete_item(client):
    create = await client.post("/api/items/", json={"title": "削除対象", "content": ""})
    item_id = create.json()["id"]
    del_resp = await client.delete(f"/api/items/{item_id}")
    assert del_resp.status_code == 200
    # 削除後は一覧に出ないこと
    list_resp = await client.get("/api/items/")
    assert all(i["id"] != item_id for i in list_resp.json())


@pytest.mark.asyncio
async def test_delete_item_not_found(client):
    resp = await client.delete("/api/items/9999")
    assert resp.status_code == 404
""")

    touch(target / "tests" / "e2e" / "test_app.py")

    # ─── 15. .github/workflows/ci.yml ───────────────────────────────
    write(target / ".github" / "workflows" / "ci.yml", """\
name: CI

on:
  push:
    branches: ["main", "master"]
  pull_request:
    branches: ["main", "master"]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync

      - name: Copy .env for testing
        run: cp .env.example .env

      - name: Run unit and integration tests
        run: uv run pytest tests/unit/ tests/integration/ -v --tb=short
""")

    # ─── 17. docs/ ───────────────────────────────────────────────────
    # 開発入門をコピー
    guide_src = here / "docs" / "事例で学ぶWeb開発入門.md"
    copy_doc(guide_src, target / "docs" / "事例で学ぶWeb開発入門.md")

    for tmpl_name in ["テンプレート_01_要件定義.md", "テンプレート_02_仕様書.md",
                       "テンプレート_03_テスト仕様書.md", "テンプレート_04_報告書.md"]:
        tmpl_src = here / "docs" / tmpl_name
        dest_name = tmpl_name.replace("テンプレート_", "")
        copy_doc(tmpl_src, target / "docs" / dest_name)

    # ─── 18. .github/copilot-instructions.md ─────────────────────────
    inst_src = here / ".github" / "copilot-instructions.md"
    copy_doc(inst_src, target / ".github" / "copilot-instructions.md")

    # CLAUDE.md もコピー
    claude_src = here / "CLAUDE.md"
    copy_doc(claude_src, target / "CLAUDE.md")

    # ─── 17. README.md ───────────────────────────────────────────────
    write(target / "README.md", f"""\
# {app_name}

（アプリの概要を 1〜2 文で記載）

---

## 必要な環境

| 項目 | 内容 |
| --- | --- |
| Python | 3.12 以上 |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) |
| 開発 DB | SQLite（追加インストール不要） |
| 本番 DB | PostgreSQL（`asyncpg` が別途必要） |

---

## セットアップ

```bash
# 1. 環境設定ファイルを作成
cp .env.example .env        # Mac/Linux
copy .env.example .env      # Windows

# 2. 依存パッケージをインストール（開発）
uv sync

# 3. DB を初期化
uv run python init_database.py

# 4. サーバーを起動
uv run uvicorn main:app --reload
```

ブラウザで `http://localhost:8000/` を開く。

---

## 本番環境（PostgreSQL）への切り替え

1. `.env` の `DATABASE_URL` を変更する
2. `uv sync --extra prod` で `asyncpg` をインストールする
3. `uv run python init_database.py` でテーブルを作成する

---

## テストの実行

```bash
# 単体テスト + 結合テスト
uv run pytest tests/unit/ tests/integration/ -v

# E2E テスト（サーバーを起動した状態で実行）
uv run pytest tests/e2e/ -v
```

---

## プロジェクト構成

```text
{app_name}/
├── main.py          # アプリ起動・ミドルウェア・ルーター登録
├── config.py        # 設定管理（.env 読み込み）
├── db.py            # DB エンジン・セッション
├── init_database.py # テーブル初期化
├── models/          # SQLAlchemy モデル
├── schemas/         # Pydantic スキーマ
├── cruds/           # DB 操作ロジック
├── routers/         # エンドポイント定義
├── templates/       # Jinja2 テンプレート
├── static/          # CSS
├── tests/           # テスト
└── docs/            # ドキュメント
```

---

## ドキュメント

| ファイル | 内容 |
| --- | --- |
| [01_要件定義.md](docs/01_要件定義.md) | 何を作るか（目的・機能・制約） |
| [02_仕様書.md](docs/02_仕様書.md) | どう作るか（ER 図・API 仕様・画面） |
| [03_テスト仕様書.md](docs/03_テスト仕様書.md) | どう検証するか（テスト設計） |
| [04_報告書.md](docs/04_報告書.md) | 結果（テスト結果・不具合・デプロイ依頼） |
| [Web 開発入門](docs/事例で学ぶWeb開発入門.md) | バイブコーディング入門＋技術解説 |
""")

    # ─── 完了メッセージ ───────────────────────────────────────────────
    print(f"""
==========================================================
  テンプレートを作成しました
==========================================================

場所: {target}

生成ファイル:
  pyproject.toml / .env.example / .gitignore
  main.py / config.py / db.py / init_database.py
  models/ schemas/ cruds/ routers/ templates/ static/
  tests/  (unit / integration / e2e)
  docs/   (01_要件定義 ~ 04_報告書 + 開発入門)
  CLAUDE.md / .github/copilot-instructions.md
  .github/workflows/ci.yml  <- GitHub Actions (自動テスト)

----------------------------------------------------------
ローカルで動かす
----------------------------------------------------------
  cd {target}
  copy .env.example .env       (Windows)
  cp .env.example .env         (Mac/Linux)
  uv sync
  uv run python init_database.py
  uv run uvicorn main:app --reload
  -> http://localhost:8000/

テスト実行:
  uv run pytest tests/unit/ tests/integration/ -v

----------------------------------------------------------
GitHub に登録する (テンプレートリポジトリとして公開)
----------------------------------------------------------
  cd {target}
  git init
  git add .
  git commit -m "chore: initial template from fastapi-memoapp"

  # GitHub CLI でリポジトリ作成 & プッシュ
  gh repo create {app_name} --public --source=. --remote=origin --push

  # テンプレートリポジトリに設定
  # (他の人が Use this template で使えるようになる)
  gh repo edit {app_name} --template

----------------------------------------------------------
開発の始め方 (AI への最初の一言)
----------------------------------------------------------
  「CLAUDE.md のルールに従って、
   docs/01_要件定義.md を参考に models/{app_name}.py を作って」
==========================================================
""")


if __name__ == "__main__":
    main()
