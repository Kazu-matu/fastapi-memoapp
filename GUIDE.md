# FastAPI アプリ開発ガイド（初心者向け）

このガイドは、このメモアプリを**見本（テンプレート）**として使い、  
自分のアプリを**ゼロから順番に作れる**ようにするためのものです。

---

## ガイドの全体の流れ

```
ステップ 0  アイデアをメモする
    ↓
ステップ 1  設計書を作る
    ↓
ステップ 2  設計を確認する（チェックリスト）
    ↓
ステップ 3  実装する
    ↓
ステップ 4  テストする
```

各ステップにテンプレートがあります。  
コピーして自分のアプリ用に書き換えながら進めてください。

---

## ステップ 0：アイデアをメモする

> **目的**: 頭の中にあるアイデアを言葉にする。完璧でなくていい。箇条書きで OK。

下のテンプレートをコピーして `my_app_idea.md` などのファイルに書き出してください。

---

### テンプレート：アイデアメモ

```markdown
# アプリ名（仮）：〇〇管理アプリ

## このアプリで何をしたいか（1〜2 文）
例）家計の支出を記録して、月ごとの合計を確認できるようにしたい。

## 誰が使うか
例）自分 / 家族 / 小さなチーム

## 技術スタック
変えないもの（見本のまま使う）:
- Python / FastAPI
- SQLAlchemy（非同期）
- Jinja2（画面）
- SQLite（開発）/ PostgreSQL（本番）
- uv（パッケージ管理）

変えるもの・追加するもの:
- 例）認証が必要 → FastAPI-Users を追加
- 例）グラフを表示したい → Chart.js を追加

## 画面一覧
| 画面名 | URL | 説明 |
| --- | --- | --- |
| 一覧 | / | 登録済みデータを一覧表示 |
| 新規作成フォーム | / （同じページ）| データを入力して登録 |
| 編集 | /{id}/edit | 既存データを編集 |
| （追加したい画面があれば書く） | | |

## 機能一覧
| # | 機能名 | 説明 |
| --- | --- | --- |
| 1 | 登録 | フォームからデータを登録する |
| 2 | 一覧表示 | 登録済みデータを一覧で見る |
| 3 | 編集 | 既存データを変更する |
| 4 | 削除 | データを論理削除する |
| 5 | 変更履歴 | 誰がいつ変更したか記録する |
| 6 | （追加したい機能があれば書く） | |

## テーブル（何を保存するか）
### メインテーブル：〇〇テーブル
| カラム名 | 型 | 説明 |
| --- | --- | --- |
| id | 整数（自動採番） | 主キー |
| （自分のデータ項目） | | |
| is_deleted | 真偽値 | 論理削除フラグ |
| created_by | 文字列 | 登録者 |
| updated_by | 文字列 | 更新者 |
| created_at | 日時 | 登録日時 |
| updated_at | 日時 | 更新日時 |

### 変更履歴テーブル（必要なら）
| カラム名 | 型 | 説明 |
| --- | --- | --- |
| history_id | 整数 | 主キー |
| （メインテーブル）_id | 整数 | 外部キー |
| action | 文字列 | CREATE / UPDATE / DELETE |
| changed_at | 日時 | 操作日時 |
| changed_by | 文字列 | 操作者 |
| （変更前の値のスナップショット） | | |

## 優先度
- まず作る（必須）：
- 余裕があれば作る（任意）：
```

---

## ステップ 1：設計書を作る

> **目的**: アイデアメモをもとに、実装前に「何を作るか」を明確にする。

### 1-1. ファイル構成を決める

見本のファイル構成と見比べながら、自分のアプリ用に書き換えます。

```
my_app/
├── main.py              # ← 見本のまま使える（アプリ名だけ変える）
├── config.py            # ← 見本のまま使える（APP_NAME だけ変える）
├── db.py                # ← 見本のまま使える
├── init_database.py     # ← 見本のまま使える
├── pyproject.toml       # ← 見本のまま + 追加パッケージを書く
├── .env                 # ← 見本のまま + 自分の設定に変える
│
├── models/
│   └── （テーブル名）.py  # ← モデルを書く（見本: models/memo.py）
│
├── schemas/
│   └── （テーブル名）.py  # ← スキーマを書く（見本: schemas/memo.py）
│
├── cruds/
│   └── （テーブル名）.py  # ← CRUD を書く（見本: cruds/memo.py）
│
├── routers/
│   ├── （テーブル名）.py  # ← REST API（見本: routers/memo.py）
│   └── pages.py          # ← 画面（見本: routers/pages.py）
│
├── templates/
│   ├── base.html         # ← 見本をコピーしてアプリ名だけ変える
│   ├── index.html        # ← 一覧・登録フォーム
│   └── edit.html         # ← 編集フォーム
│
└── static/
    └── styles.css        # ← 見本のまま使える（色などは変えてもよい）
```

### 1-2. ER 図を書く（テーブル設計）

アイデアメモのテーブルをもとに、関係を矢印で整理します。

```
＜書き方の例＞

[テーブルA]                     [テーブルB（履歴）]
- id (PK)                       - history_id (PK)
- 〇〇                          - テーブルA_id (FK) ──→ テーブルA.id
- is_deleted                    - action (CREATE/UPDATE/DELETE)
- created_by                    - changed_at
- created_at                    - changed_by
- updated_at                    - 〇〇（スナップショット）
```

### 1-3. API 設計（エンドポイント一覧）

| メソッド | URL | 処理 | ステータス |
| --- | --- | --- | --- |
| GET | /api/〇〇/ | 全件取得 | 200 |
| POST | /api/〇〇/ | 新規登録 | 201 |
| GET | /api/〇〇/{id} | 1件取得 | 200 |
| PUT | /api/〇〇/{id} | 更新 | 200 |
| DELETE | /api/〇〇/{id} | 論理削除 | 200 |
| GET | /api/〇〇/{id}/histories | 変更履歴 | 200 |

### 1-4. 画面遷移図

```
[一覧画面（/）]
    │
    ├─ 登録ボタン → POST /〇〇 → リダイレクト → [一覧画面]（フラッシュメッセージ）
    │
    ├─ 編集ボタン → GET /〇〇/{id}/edit → [編集画面]
    │                    └─ 更新ボタン → POST /〇〇/{id}/edit → リダイレクト → [一覧画面]
    │
    └─ 削除ボタン → POST /〇〇/{id}/delete → リダイレクト → [一覧画面]
```

---

## ステップ 2：設計を確認する

> **目的**: 実装を始める前に「抜け漏れがないか」確認する。  
> 全部 ✅ になってから実装に進みましょう。

### チェックリスト

#### アイデアメモ

- [ ] アプリの目的が1〜2文で書けている
- [ ] 誰が使うか書いている
- [ ] 画面一覧が書けている（画面名・URL・説明）
- [ ] 機能一覧が書けている
- [ ] テーブルの項目が書けている

#### テーブル設計

- [ ] 主キー（id）がある
- [ ] 論理削除フラグ（is_deleted）がある
- [ ] 登録者・更新者（created_by / updated_by）がある
- [ ] 登録日時・更新日時（created_at / updated_at）がある
- [ ] 変更履歴テーブルが必要な場合、外部キーが設定されている

#### API 設計

- [ ] CRUD（登録・取得・更新・削除）のエンドポイントが揃っている
- [ ] レスポンスのステータスコードを決めた（POST=201、GET=200 など）
- [ ] エラー時（404, 422）の動作を考えた

#### 画面

- [ ] 一覧画面がある
- [ ] 登録フォームがある
- [ ] 編集フォームがある
- [ ] 削除操作に確認ダイアログがある（誤操作防止）
- [ ] 操作後のフラッシュメッセージを決めた（例：「登録しました」）

#### その他

- [ ] `.env.example` を用意する（DB 接続情報などを書く）
- [ ] `.gitignore` に `.env` と `*.sqlite` を書いた
- [ ] README.md にセットアップ手順を書く予定がある

---

## ステップ 3：実装する

> **目的**: 設計書をもとにコードを書く。  
> **順番を守る**ことで、前の工程でエラーが出にくくなります。

### 実装の順番

```
1. 環境セットアップ
    ↓
2. モデル（models/）
    ↓
3. スキーマ（schemas/）
    ↓
4. CRUD（cruds/）
    ↓
5. ルーター API（routers/〇〇.py）
    ↓
6. ルーター ページ（routers/pages.py）
    ↓
7. テンプレート（templates/）
    ↓
8. 動作確認（ブラウザで確認）
```

---

### 3-1. 環境セットアップ

```bash
# 1. このリポジトリをコピーして新しいフォルダに貼り付け
#    （または git clone してリネーム）

# 2. 不要なファイルを削除
#    frontapp/ フォルダ（古いSPA版）は不要なら削除してよい

# 3. .env を作成
cp .env.example .env
# .env の APP_NAME を自分のアプリ名に変更

# 4. 依存パッケージをインストール
uv sync

# 5. DB を初期化（モデルを書いた後に実行）
uv run python init_database.py
```

---

### 3-2. モデルを書く（models/〇〇.py）

> **見本ファイル**: `models/memo.py`  
> コピーして、テーブル名・カラム名を自分のものに書き換えます。

```python
# models/expense.py（例：支出管理アプリの場合）
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime


class Expense(Base):
    """支出テーブル"""
    __tablename__ = "expenses"

    expense_id  = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(100), nullable=False)      # ← 自分の項目
    amount      = Column(Float, nullable=False)            # ← 自分の項目
    category    = Column(String(50), nullable=False)       # ← 自分の項目
    memo        = Column(String(255), nullable=True)       # ← 自分の項目

    # ↓ ここから下は見本のままコピーして OK（論理削除・監査フィールド）
    is_deleted  = Column(Boolean, default=False, nullable=False)
    deleted_at  = Column(DateTime, nullable=True)
    created_at  = Column(DateTime, default=datetime.now, nullable=False)
    updated_at  = Column(DateTime, onupdate=datetime.now, nullable=True)
    created_by  = Column(String(100), nullable=False)
    updated_by  = Column(String(100), nullable=True)

    histories   = relationship("ExpenseHistory", back_populates="expense",
                               cascade="all, delete-orphan")


class ExpenseHistory(Base):
    """支出変更履歴テーブル"""
    __tablename__ = "expense_histories"

    history_id  = Column(Integer, primary_key=True, autoincrement=True)
    expense_id  = Column(Integer, ForeignKey("expenses.expense_id"), nullable=False)
    action      = Column(String(20), nullable=False)   # CREATE / UPDATE / DELETE
    changed_at  = Column(DateTime, default=datetime.now, nullable=False)
    changed_by  = Column(String(100), nullable=False)

    # ↓ 変更時点のスナップショット（自分の項目に合わせて書く）
    title       = Column(String(100))
    amount      = Column(Float)
    category    = Column(String(50))

    expense     = relationship("Expense", back_populates="histories")
```

**書いたら確認**:

- [ ] `__tablename__` を設定した
- [ ] 主キーに `autoincrement=True` を付けた
- [ ] 外部キー（`ForeignKey`）の参照先テーブル名が正しい
- [ ] `relationship` の文字列が正しいクラス名になっている

---

### 3-3. スキーマを書く（schemas/〇〇.py）

> **見本ファイル**: `schemas/memo.py`  
> Pydantic でリクエスト・レスポンスのバリデーションを定義します。

```python
# schemas/expense.py（例）
from pydantic import BaseModel, Field
from datetime import datetime


class ExpenseCreateSchema(BaseModel):
    """登録・更新リクエスト用"""
    title:    str   = Field(min_length=1, max_length=100)
    amount:   float = Field(gt=0)                    # 0より大きい
    category: str   = Field(min_length=1, max_length=50)
    memo:     str   = ""


class ExpenseSchema(ExpenseCreateSchema):
    """レスポンス用（DB の値を含む）"""
    expense_id: int
    created_at: datetime
    updated_at: datetime | None = None
    created_by: str
    updated_by: str | None = None
    is_deleted: bool = False

    model_config = {"from_attributes": True}


class ExpenseHistorySchema(BaseModel):
    """履歴レスポンス用"""
    history_id:  int
    expense_id:  int
    action:      str
    changed_at:  datetime
    changed_by:  str
    title:       str
    amount:      float
    category:    str

    model_config = {"from_attributes": True}


class ResponseSchema(BaseModel):
    """操作結果レスポンス"""
    message: str
```

**書いたら確認**:

- [ ] 必須フィールドにバリデーション（`min_length` など）を付けた
- [ ] `model_config = {"from_attributes": True}` を書いた（SQLAlchemy → Pydantic 変換に必要）
- [ ] レスポンス用スキーマに DB の項目（id・日時・ユーザー）を含めた

---

### 3-4. CRUD を書く（cruds/〇〇.py）

> **見本ファイル**: `cruds/memo.py`  
> DB の操作（登録・取得・更新・削除）をまとめます。

```python
# cruds/expense.py（最小限の例）
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

import models.expense as expense_model
from schemas.expense import ExpenseCreateSchema


def _build_history(expense, action: str, user: str):
    """変更履歴レコードを生成する"""
    return expense_model.ExpenseHistory(
        expense_id=expense.expense_id,
        action=action,
        changed_by=user,
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
    )


async def get_expenses(db: AsyncSession):
    """論理削除されていないものを全件取得"""
    result = await db.execute(
        select(expense_model.Expense)
        .where(expense_model.Expense.is_deleted == False)
        .order_by(expense_model.Expense.created_at.desc())
    )
    return result.scalars().all()


async def get_expense_by_id(db: AsyncSession, expense_id: int):
    """1件取得（論理削除済みは除く）"""
    result = await db.execute(
        select(expense_model.Expense)
        .where(
            expense_model.Expense.expense_id == expense_id,
            expense_model.Expense.is_deleted == False,
        )
    )
    return result.scalar_one_or_none()


async def insert_expense(db: AsyncSession, data: ExpenseCreateSchema, user: str):
    """登録（トランザクション + 履歴記録）"""
    try:
        new = expense_model.Expense(
            title=data.title, amount=data.amount,
            category=data.category, memo=data.memo,
            created_by=user, updated_by=user,
        )
        db.add(new)
        await db.flush()                              # ID を確定（まだコミットしない）
        db.add(_build_history(new, "CREATE", user))
        await db.commit()
        await db.refresh(new)
        return new
    except Exception:
        await db.rollback()
        raise


async def update_expense(db: AsyncSession, expense_id: int, data: ExpenseCreateSchema, user: str):
    """更新（トランザクション + 履歴記録）"""
    expense = await get_expense_by_id(db, expense_id)
    if not expense:
        return None
    try:
        expense.title    = data.title
        expense.amount   = data.amount
        expense.category = data.category
        expense.memo     = data.memo
        expense.updated_by = user
        await db.flush()
        db.add(_build_history(expense, "UPDATE", user))
        await db.commit()
        await db.refresh(expense)
        return expense
    except Exception:
        await db.rollback()
        raise


async def delete_expense(db: AsyncSession, expense_id: int, user: str):
    """論理削除（トランザクション + 履歴記録）"""
    expense = await get_expense_by_id(db, expense_id)
    if not expense:
        return None
    try:
        expense.is_deleted = True
        expense.deleted_at = datetime.now()
        expense.updated_by = user
        await db.flush()
        db.add(_build_history(expense, "DELETE", user))
        await db.commit()
        return expense
    except Exception:
        await db.rollback()
        raise
```

**書いたら確認**:

- [ ] `insert` / `update` / `delete` すべてに `try / except / rollback` を書いた
- [ ] `flush()` で ID を確定してから履歴レコードを作っている
- [ ] `get_〇〇` は `is_deleted == False` でフィルタしている

---

### 3-5. REST API ルーターを書く（routers/〇〇.py）

> **見本ファイル**: `routers/memo.py`  
> エンドポイントを定義します。CRUD 関数を呼び出すだけなのでシンプルです。

```python
# routers/expense.py（最小限の例）
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.expense import ExpenseCreateSchema, ExpenseSchema, ResponseSchema
import cruds.expense as expense_crud
import db as app_db
from config import get_login_user

router = APIRouter(tags=["Expenses API"], prefix="/api/expenses")


@router.post("/", response_model=ResponseSchema, status_code=201)
async def create_expense(data: ExpenseCreateSchema, session: AsyncSession = Depends(app_db.get_dbsession)):
    await expense_crud.insert_expense(session, data, get_login_user())
    return ResponseSchema(message="登録しました")


@router.get("/", response_model=list[ExpenseSchema])
async def list_expenses(session: AsyncSession = Depends(app_db.get_dbsession)):
    return await expense_crud.get_expenses(session)


@router.get("/{expense_id}", response_model=ExpenseSchema)
async def get_expense(expense_id: int, session: AsyncSession = Depends(app_db.get_dbsession)):
    expense = await expense_crud.get_expense_by_id(session, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="見つかりません")
    return expense


@router.put("/{expense_id}", response_model=ResponseSchema)
async def update_expense(expense_id: int, data: ExpenseCreateSchema, session: AsyncSession = Depends(app_db.get_dbsession)):
    result = await expense_crud.update_expense(session, expense_id, data, get_login_user())
    if not result:
        raise HTTPException(status_code=404, detail="更新対象が見つかりません")
    return ResponseSchema(message="更新しました")


@router.delete("/{expense_id}", response_model=ResponseSchema)
async def delete_expense(expense_id: int, session: AsyncSession = Depends(app_db.get_dbsession)):
    result = await expense_crud.delete_expense(session, expense_id, get_login_user())
    if not result:
        raise HTTPException(status_code=404, detail="削除対象が見つかりません")
    return ResponseSchema(message="削除しました")
```

---

### 3-6. ページルーターを書く（routers/pages.py）

> **見本ファイル**: `routers/pages.py`  
> Jinja2 テンプレートを返す画面用ルーターです。  
> PRG パターン（POST → リダイレクト → GET）を守ってください。

```python
# routers/pages.py の骨格（自分の変数名に書き換える）
from pathlib import Path
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

import cruds.expense as expense_crud
import db as app_db
from config import get_login_user
from schemas.expense import ExpenseCreateSchema

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/")
async def index(request: Request, msg: str = "", session: AsyncSession = Depends(app_db.get_dbsession)):
    items = await expense_crud.get_expenses(session)
    return templates.TemplateResponse(request, "index.html", {
        "items": items, "msg": msg, "login_user": get_login_user(),
    })


@router.post("/expenses")
async def create(
    request: Request,
    title:    Annotated[str,   Form()],
    amount:   Annotated[float, Form()],
    category: Annotated[str,   Form()],
    memo:     Annotated[str,   Form()] = "",
    session:  AsyncSession = Depends(app_db.get_dbsession),
):
    data = ExpenseCreateSchema(title=title, amount=amount, category=category, memo=memo)
    await expense_crud.insert_expense(session, data, get_login_user())
    return RedirectResponse("/?msg=created", status_code=303)   # ← PRG：必ず 303
```

**書いたら確認**:

- [ ] `templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))` と絶対パスにした
- [ ] POST ハンドラは `RedirectResponse(..., status_code=303)` を返している
- [ ] `TemplateResponse(request, "template.html", {...})` の順番になっている（`request` が第1引数）

---

### 3-7. テンプレートを書く（templates/）

> **見本ファイル**: `templates/base.html` / `templates/index.html` / `templates/edit.html`

**base.html のカスタマイズ箇所**（2ヶ所だけ変える）:

```html
<!-- アプリ名を変える -->
<h1><a href="/">📝 メモアプリ</a></h1>  ← ここを自分のアプリ名に
```

**index.html のポイント**:

```html
<!-- フラッシュメッセージ（見本のまま使える） -->
{% if msg == "created" %}
<div class="flash flash--success">登録しました</div>
{% endif %}

<!-- 登録フォーム -->
<form method="post" action="/expenses" class="memo-form">
  <input type="text" name="title" required>
  <input type="number" name="amount" step="0.01" required>
  <select name="category">
    <option>食費</option>
    <option>交通費</option>
  </select>
  <button type="submit" class="btn btn--primary">登録</button>
</form>

<!-- 一覧テーブル -->
{% for item in items %}
<tr>
  <td>{{ item.title }}</td>
  <td>{{ item.amount }}</td>
  <td>
    <!-- 削除フォーム（JS の confirm で確認する） -->
    <form method="post" action="/expenses/{{ item.expense_id }}/delete"
          onsubmit="return confirm('削除しますか？')">
      <button type="submit" class="btn btn--danger btn--sm">削除</button>
    </form>
  </td>
</tr>
{% endfor %}
```

---

### 3-8. main.py にルーターを登録する

```python
# main.py に追加
from routers.expense import router as expense_api_router   # ← 追加
from routers.pages import router as pages_router

app.include_router(pages_router)
app.include_router(expense_api_router)                     # ← 追加
```

---

### 3-9. DB を初期化して起動確認

```bash
# テーブルを作成
uv run python init_database.py

# サーバーを起動
uv run uvicorn main:app --reload

# ブラウザで確認
# http://localhost:8000/       → 画面
# http://localhost:8000/docs   → API ドキュメント
```

**画面確認チェックリスト**:

- [ ] 一覧画面が表示される（エラーなし）
- [ ] 登録フォームから登録できる
- [ ] 登録後に一覧に追加される
- [ ] フラッシュメッセージが表示される
- [ ] 編集画面が開く
- [ ] 更新できる
- [ ] 削除できる（確認ダイアログが出る）
- [ ] `/docs` で API ドキュメントが表示される

---

## ステップ 4：テストする

> **目的**: 作ったコードが正しく動くことを自動で確認できるようにする。

### 4-1. テストファイルの構成

```
tests/
├── conftest.py           # ← 見本のまま使える（テーブル名が変わる場合は不要）
├── unit/
│   └── test_schemas.py   # ← スキーマのバリデーションテスト
└── integration/
    └── test_api.py       # ← API エンドポイントのテスト
```

### 4-2. スキーマのテスト（unit/test_schemas.py）

> **見本ファイル**: `tests/unit/test_schemas.py`

```python
# tests/unit/test_schemas.py（例）
import pytest
from pydantic import ValidationError
from schemas.expense import ExpenseCreateSchema


def test_valid_expense():
    """正常なデータでバリデーション通過"""
    data = ExpenseCreateSchema(title="ランチ", amount=800, category="食費")
    assert data.title == "ランチ"


def test_empty_title_raises():
    """title が空のときエラー"""
    with pytest.raises(ValidationError):
        ExpenseCreateSchema(title="", amount=800, category="食費")


def test_negative_amount_raises():
    """amount が 0 以下のときエラー"""
    with pytest.raises(ValidationError):
        ExpenseCreateSchema(title="テスト", amount=-1, category="食費")
```

### 4-3. API の結合テスト（integration/test_api.py）

> **見本ファイル**: `tests/integration/test_api.py`

```python
# tests/integration/test_api.py（テンプレート）
import pytest

BASE = "/api/expenses"   # ← 自分の API パスに変える

PAYLOAD = {
    "title": "テストランチ",
    "amount": 800,
    "category": "食費",
}

@pytest.mark.asyncio
async def test_create_success(client):
    res = await client.post(f"{BASE}/", json=PAYLOAD)
    assert res.status_code == 201

@pytest.mark.asyncio
async def test_get_empty(client):
    res = await client.get(f"{BASE}/")
    assert res.status_code == 200
    assert res.json() == []

@pytest.mark.asyncio
async def test_get_after_create(client):
    await client.post(f"{BASE}/", json=PAYLOAD)
    res = await client.get(f"{BASE}/")
    assert len(res.json()) == 1

@pytest.mark.asyncio
async def test_delete_success(client):
    await client.post(f"{BASE}/", json=PAYLOAD)
    item_id = (await client.get(f"{BASE}/")).json()[0]["expense_id"]
    res = await client.delete(f"{BASE}/{item_id}")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_get_deleted_returns_404(client):
    """論理削除後は 404 になる"""
    await client.post(f"{BASE}/", json=PAYLOAD)
    item_id = (await client.get(f"{BASE}/")).json()[0]["expense_id"]
    await client.delete(f"{BASE}/{item_id}")
    res = await client.get(f"{BASE}/{item_id}")
    assert res.status_code == 404
```

### 4-4. テスト実行

```bash
# 単体テスト + 結合テスト
uv run pytest tests/unit/ tests/integration/ -v

# 特定のテストだけ実行
uv run pytest tests/integration/test_api.py::test_create_success -v
```

---

## よくある失敗と対処法

| 症状 | 原因 | 対処法 |
| --- | --- | --- |
| `ImportError: cannot import name 'Base' from 'db'` | `db.py` に `Base` がない | `db.py` に `Base = declarative_base()` があるか確認 |
| テンプレートで `Internal Server Error` | `TemplateResponse` の引数順が違う | `TemplateResponse(request, "name.html", {...})` の順にする |
| POST で `307 Temporary Redirect` が返る | URL の末尾 `/` が抜けている | `client.post("/api/〇〇/", ...)` と `/` を付ける |
| `flush()` 後にエラーが出る | `commit()` 前にモデルを触っている | `flush()` 直後に履歴レコードを作り、すぐ `commit()` する |
| テスト時に DB が汚染される | `setup_db` フィクスチャを使っていない | `conftest.py` の `client` フィクスチャを使っているか確認 |
| `.env` の値が反映されない | `load_dotenv()` を呼んでいない | `config.py` の先頭に `load_dotenv(...)` があるか確認 |

---

## 参考：見本との対応表

自分のアプリを作るとき、見本のどのファイルをどう変えるかの早見表です。

| 見本のファイル | 自分のアプリでの扱い |
| --- | --- |
| `config.py` | `APP_NAME` だけ変える。ほぼそのまま使える |
| `db.py` | そのまま使える |
| `main.py` | ルーターの `import` と `include_router` を追加する |
| `init_database.py` | モデルの `import` を自分のものに変える |
| `models/memo.py` | **コピーして** カラム名・テーブル名を変える |
| `schemas/memo.py` | **コピーして** フィールドを変える |
| `cruds/memo.py` | **コピーして** モデル名・フィールド名を変える |
| `routers/memo.py` | **コピーして** スキーマ名・CRUD 関数名を変える |
| `routers/pages.py` | **コピーして** フォーム項目・リダイレクト先を変える |
| `templates/base.html` | アプリ名だけ変える |
| `templates/index.html` | **コピーして** フォーム・テーブルの項目を変える |
| `templates/edit.html` | **コピーして** フォームの項目を変える |
| `static/styles.css` | そのまま使える（色を変えたい場合だけ編集） |
| `tests/conftest.py` | そのまま使える |
| `tests/unit/test_schemas.py` | **コピーして** スキーマ名・バリデーション条件を変える |
| `tests/integration/test_api.py` | **コピーして** `BASE` と `PAYLOAD` を変える |
