# AI 開発指示書

このファイルは AI アシスタントへの指示書です。  
新しいアプリを作るとき、このファイルをプロジェクトのルートに置いて  
**「このファイルを守って実装して」** と伝えるだけで開発を始められます。

---

## 1. このプロジェクトについて

### 技術スタック（変更禁止）

| 区分 | 技術 | バージョン |
| --- | --- | --- |
| 言語 | Python | 3.12 以上 |
| Web フレームワーク | FastAPI | 0.115 以上 |
| テンプレートエンジン | Jinja2 | 3.1 以上（SSR） |
| ORM | SQLAlchemy | 2.x（非同期モード） |
| バリデーション | Pydantic | v2 |
| DB ドライバ（開発） | aiosqlite | SQLite 用 |
| DB ドライバ（本番） | asyncpg | PostgreSQL 用 |
| 設定管理 | python-dotenv | `.env` ファイル読み込み |
| パッケージ管理 | uv | `pyproject.toml` |
| テスト | pytest + pytest-asyncio | |
| E2E テスト | Playwright | |

### 絶対に変えてはいけないもの

- パッケージ管理は **uv** のみ（pip / poetry / pipenv は使わない）
- 画面は **Jinja2 テンプレート**（React / Vue などのフロントフレームワークは使わない）
- DB アクセスは **SQLAlchemy 非同期モード**（同期モードは使わない）
- フォーム送信後は必ず **PRG パターン**（`RedirectResponse(..., status_code=303)`）

---

## 2. ファイル構成の規約

新しいアプリを作るとき、**必ずこの構成を守る**。

```
my_app/
├── CLAUDE.md             ← この指示書（常にルートに置く）
├── main.py               ← アプリ起動・ミドルウェア・ルーター登録のみ
├── config.py             ← 設定値の定義のみ（ビジネスロジックを書かない）
├── db.py                 ← DB エンジン・セッション定義のみ
├── init_database.py      ← テーブル初期化スクリプト
├── pyproject.toml
├── .env                  ← git 管理外（機密情報）
├── .env.example          ← git 管理対象（テンプレート）
├── .gitignore
│
├── models/               ← SQLAlchemy モデル（テーブル定義）
│   └── {テーブル名}.py
│
├── schemas/              ← Pydantic スキーマ（入出力バリデーション）
│   └── {テーブル名}.py
│
├── cruds/                ← DB 操作ロジック（ビジネスロジックの中核）
│   └── {テーブル名}.py
│
├── routers/              ← エンドポイント定義
│   ├── {テーブル名}.py   ← REST API（/api/〇〇）
│   └── pages.py          ← Jinja2 ページ（/）
│
├── templates/            ← HTML テンプレート
│   ├── base.html
│   ├── index.html
│   └── edit.html
│
├── static/
│   └── styles.css
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── test_schemas.py
│   ├── integration/
│   │   └── test_api.py
│   └── e2e/
│       └── test_{アプリ名}.py
│
└── docs/
    ├── 仕様書.md
    └── テスト仕様書・報告書.md
```

---

## 3. 実装の順番（この順番を守る）

```
1. models/        テーブル定義を先に確定させる
   ↓
2. schemas/       入出力のバリデーションを決める
   ↓
3. cruds/         DB 操作ロジックを書く
   ↓
4. routers/       エンドポイントを書く（API → pages の順）
   ↓
5. templates/     HTML を書く
   ↓
6. tests/         テストを書く（スキーマ → API の順）
   ↓
7. docs/          ドキュメントを書く
```

**理由**: 上位の層が確定していないと、下位の層で何度も書き直しが発生する。

---

## 4. コーディング規約

### 4-1. models/（テーブル定義）

```python
# ✅ 必ず含めるカラム（全テーブル共通）
is_deleted  = Column(Boolean, default=False, nullable=False)   # 論理削除フラグ
deleted_at  = Column(DateTime, nullable=True)                  # 削除日時
created_at  = Column(DateTime, default=datetime.now, nullable=False)
updated_at  = Column(DateTime, onupdate=datetime.now, nullable=True)
created_by  = Column(String(100), nullable=False)              # 登録者
updated_by  = Column(String(100), nullable=True)               # 更新者

# ✅ 変更履歴テーブルを必ず作る
# メインテーブルと 1:N の関係で、スナップショットを保存する

# ❌ やってはいけないこと
# - nullable=True を安易に付けない（本当に NULL になるカラムだけ）
# - __tablename__ を省略しない
# - 物理削除（db.delete()）は使わない
```

### 4-2. schemas/（Pydantic）

```python
# ✅ 必ず書くこと
model_config = {"from_attributes": True}  # SQLAlchemy モデルからの変換に必要

# ✅ バリデーションを必ず付ける
title: str = Field(min_length=1, max_length=100)  # 空文字を許可しない

# ✅ スキーマの分け方
# - 登録・更新リクエスト用（入力）: XxxCreateSchema / XxxUpdateSchema
# - レスポンス用（出力）        : XxxSchema
# - 履歴レスポンス用            : XxxHistorySchema
# - 操作結果                    : ResponseSchema（message: str のみ）

# ❌ やってはいけないこと
# - Field(..., example=...) は Pydantic v2 で非推奨。使わない
# - レスポンス用スキーマに password などの機密情報を含めない
```

### 4-3. cruds/（DB 操作）

```python
# ✅ 書き込み操作（insert / update / delete）は必ずこの形にする
async def insert_xxx(db: AsyncSession, data: XxxCreateSchema, user: str):
    try:
        new = Xxx(title=data.title, created_by=user, updated_by=user)
        db.add(new)
        await db.flush()              # ← ID 確定。コミットはしない
        db.add(_build_history(new, "CREATE", user))
        await db.commit()
        await db.refresh(new)
        return new
    except Exception:
        await db.rollback()           # ← 例外が起きたら必ずロールバック
        raise                         # ← 例外を握り潰さずに再 raise する

# ✅ 取得クエリは必ず is_deleted == False でフィルタする
select(Model).where(Model.is_deleted == False)

# ✅ 削除は論理削除のみ
model.is_deleted = True
model.deleted_at = datetime.now()

# ❌ やってはいけないこと
# - except Exception: pass  → エラーを握り潰さない
# - db.delete(model)        → 物理削除は使わない
# - flush() なしで履歴を作ろうとしない（ID が確定していないため）
# - commit() 後に try の外で追加の DB 操作をしない
```

### 4-4. routers/（エンドポイント）

```python
# ✅ REST API の命名
# - POST   / 新規登録   → status_code=201
# - GET    /           → status_code=200
# - GET    /{id}       → status_code=200
# - PUT    /{id}       → status_code=200
# - DELETE /{id}       → status_code=200

# ✅ API プレフィックス
router = APIRouter(prefix="/api/{テーブル名複数形}", tags=[...])

# ✅ ページルーターの TemplateResponse（Starlette 1.x の書き方）
return templates.TemplateResponse(request, "index.html", {
    "items": items,
    # "request" をここに含めない（第1引数で渡す）
})

# ✅ フォーム POST は必ず 303 リダイレクト（PRG パターン）
return RedirectResponse("/?msg=created", status_code=303)

# ✅ Jinja2Templates は絶対パスで初期化する
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# ❌ やってはいけないこと
# - ビジネスロジックをルーターに書かない（cruds/ に書く）
# - TemplateResponse に "request" をコンテキスト dict に含めない（Starlette 1.x）
# - POST ハンドラが HTML を直接返す（必ずリダイレクト）
```

### 4-5. templates/（Jinja2）

```html
<!-- ✅ 必ず base.html を継承する -->
{% extends "base.html" %}

<!-- ✅ 削除フォームには確認ダイアログを付ける -->
<form method="post" action="/items/{{ item.id }}/delete"
      onsubmit="return confirm('削除してよいですか？')">
  <button type="submit">削除</button>
</form>

<!-- ✅ フラッシュメッセージを表示する -->
{% if msg == "created" %}<div class="flash flash--success">登録しました</div>{% endif %}

<!-- ❌ やってはいけないこと -->
<!-- - JavaScript の fetch/axios でバックエンドを呼ぶ（Jinja2 SSR の原則に反する） -->
<!-- - <script> タグでビジネスロジックを書く                                      -->
<!-- - inline style を書く（styles.css に書く）                                   -->
```

### 4-6. db.py（DB 設定）

```python
# ✅ URL に応じて自動で設定を切り替える
def _build_engine():
    if DATABASE_URL.startswith("sqlite"):
        return create_async_engine(
            DATABASE_URL, echo=DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    # PostgreSQL
    return create_async_engine(
        DATABASE_URL, echo=DEBUG,
        pool_pre_ping=True, pool_size=5, max_overflow=10,
        pool_timeout=30, pool_recycle=1800,
    )

# ❌ やってはいけないこと
# - SQLite でも pool_pre_ping=True を付けない（NullPool と競合）
# - async_sessionmaker の代わりに sessionmaker を使わない（SQLAlchemy 2.x では非推奨）
```

---

## 5. セキュリティルール

### 絶対に守ること

```
✅ .env をコミットしない
   → .gitignore に必ず .env を書く

✅ DB 接続情報・API キーなどは .env に書く
   → ソースコードにハードコードしない

✅ *.sqlite ファイルをコミットしない
   → .gitignore に *.sqlite を書く

✅ SQL は必ず SQLAlchemy の ORM / select() で書く
   → 文字列結合で SQL を作らない（SQL インジェクション防止）

✅ ユーザー入力は Pydantic スキーマで必ずバリデーションする
   → FastAPI の依存注入機能（Depends）を使う

✅ エラーメッセージにスタックトレースや DB 情報を含めない
   → HTTPException の detail は利用者向けのメッセージのみ

✅ パスワードなどの機密情報をログに出力しない
   → logging で DEBUG モードでも出力しない
```

### .gitignore に必ず含めること

```gitignore
.env
*.sqlite
*.db
__pycache__/
.venv/
```

### .env.example には必ず書くこと

```env
APP_NAME=アプリ名
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./app.sqlite
# 本番: DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

---

## 6. テスト規約

### テストの原則

```
✅ テスト用 DB はインメモリ SQLite（":memory:"）を使う
   → 本番 DB には絶対に接続しない

✅ テスト関数ごとに DB をリセットする
   → conftest.py の setup_db フィクスチャを使う

✅ テストは必ず独立して実行できる状態にする
   → テスト間でデータを引き継がない

✅ 単体テスト → 結合テスト の順に書く
```

### 最低限書くべきテスト

| テスト種別 | 対象 | 最低限のケース |
| --- | --- | --- |
| 単体テスト | スキーマ | 正常値・空文字・必須項目なし |
| 結合テスト | POST /api/〇〇/ | 正常登録（201）・バリデーションエラー（422） |
| 結合テスト | GET /api/〇〇/ | 0件・複数件 |
| 結合テスト | GET /api/〇〇/{id} | 存在するID・存在しないID（404） |
| 結合テスト | PUT /api/〇〇/{id} | 正常更新・存在しないID（404） |
| 結合テスト | DELETE /api/〇〇/{id} | 正常削除・削除後に取得すると404 |
| 結合テスト | 履歴 | 登録後に CREATE 履歴が1件ある |

### conftest.py の基本形（変えてはいけない）

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
```

---

## 7. ドキュメント規約

### すべてのドキュメントに必ず含めるヘッダー

どのドキュメントも冒頭に以下のメタ情報を記載する。

```markdown
| 項目 | 内容 |
| --- | --- |
| 作成日 | YYYY-MM-DD |
| 最終更新日 | YYYY-MM-DD |
| 版数 | v1.0 |
| 作成者 | （名前） |
```

- **版数のルール**: 初版は `v1.0`。内容を追記・修正するたびに `v1.1`, `v1.2` と上げる。構成を大幅に変えた場合は `v2.0` にする。
- **最終更新日**: ドキュメントを編集したら必ず更新する。

### 作成するドキュメント

| ファイル | タイミング | 内容 |
| --- | --- | --- |
| `docs/仕様書.md` | 実装前に作成 | ER図・API一覧・処理フロー |
| `docs/テスト仕様書・報告書.md` | テスト前に作成 | テスト仕様・実行結果 |
| `README.md` | 実装後に作成 | セットアップ・起動方法 |

### README.md に必ず書くこと

1. アプリの概要（1〜2文）
2. セットアップ手順（`uv sync` から起動まで）
3. 本番 DB（PostgreSQL）への切り替え方法
4. テストの実行方法

---

## 8. AI へのお願い

### 質問するとき

- アイデアメモ（目的・画面・機能・テーブル）を渡してから「設計書を作って」と頼む
- 設計書ができたらチェックリストで確認してから「実装して」と頼む
- 一度に全部作ろうとしない。**「models を作って」「schemas を作って」と1ステップずつ頼む**

### AI に守ってほしいルール

```
1. 実装の順番（models → schemas → cruds → routers → templates → tests）を守る

2. 指示書（このファイル）に書いていない技術・ライブラリを勝手に追加しない
   → 追加が必要な場合は先に理由を説明して確認を取る

3. コードを書いたら必ず動作確認コマンドを示す
   → 「サーバーを起動して http://localhost:8000/ を確認してください」など

4. エラーが出たら原因と修正箇所を説明してから修正する
   → 黙って書き直さない

5. ファイルを削除・リネームするときは事前に確認する
   → 「〇〇.py を削除してよいですか？」と聞く

6. DB の初期化（init_database.py）を実行するときは事前に確認する
   → 既存データが消えるため

7. .env ファイルの内容を出力・ログに表示しない

8. commit / push は指示があった場合のみ実行する
   → 勝手にコミットしない

9. 動作確認なしに「完成しました」と言わない
   → テストが通る、またはブラウザで確認できた場合のみ完成と宣言する

10. 既存コードを変更するときは変更理由を先に説明する
    → 理由のない変更はしない
```

### 開発の進め方（推奨フロー）

```
1. アイデアメモを書いて渡す
   「このアイデアメモをもとに設計書を作って」

2. 設計書（仕様書.md）を確認する
   「チェックリストで確認して問題があれば教えて」

3. 1ステップずつ実装する
   「models/expense.py を作って」
   「schemas/expense.py を作って」
   「cruds/expense.py を作って」
   「routers/expense.py を作って」
   「routers/pages.py を作って」
   「templates を作って」

4. 動作確認
   「サーバーを起動して動作確認コマンドを実行して」

5. テストを書く
   「テスト仕様書を作って、テストを実行して」

6. ドキュメントを整える
   「README.md とテスト報告書を更新して」
```

---

## 9. よく使うコマンド早見表

```bash
# 依存パッケージのインストール
uv sync                    # 開発（SQLite）
uv sync --extra prod       # 本番（PostgreSQL 含む）

# DB 初期化（既存データは消える）
uv run python init_database.py

# サーバー起動
uv run uvicorn main:app --reload
uv run uvicorn main:app --reload --port 8001   # ポート指定

# テスト実行
uv run pytest tests/unit/ tests/integration/ -v
uv run pytest tests/ -v                        # 全テスト
uv run pytest tests/integration/test_api.py::test_create_success -v  # 1件だけ

# GitHub に push
git add .
git commit -m "コミットメッセージ"
git push
```
