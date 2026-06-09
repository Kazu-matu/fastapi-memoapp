# メモアプリ（FastAPI + Jinja2）

FastAPI + Jinja2 によるサーバーサイドレンダリング構成のメモ管理 Web アプリケーションです。  
メモの CRUD・優先度・期限日・完了フラグを管理し、変更履歴の自動記録・論理削除・監査フィールドに対応します。

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

### 1. 環境設定ファイルの作成

```bash
cp .env.example .env
```

`.env` を開き、必要に応じて値を変更します（デフォルトは SQLite）。

### 2. 依存パッケージのインストール

```bash
# 開発環境（SQLite）
uv sync

# 本番環境（PostgreSQL ドライバも含める）
uv sync --extra prod
```

### 3. データベースの初期化

```bash
uv run python init_database.py
```

> 再実行すると既存データは**全て削除**されます。本番環境では実行しないこと。

---

## 起動方法

```bash
# 開発サーバー（ホットリロードあり）
uv run uvicorn main:app --reload

# ポート指定
uv run uvicorn main:app --reload --port 8000
```

起動後にアクセスできる URL:

| URL | 内容 |
| --- | --- |
| `http://localhost:8000/` | メモ一覧・作成画面 |
| `http://localhost:8000/docs` | Swagger UI（REST API ドキュメント） |
| `http://localhost:8000/redoc` | ReDoc |

---

## 本番環境（PostgreSQL）への切り替え

1. `.env` の `DATABASE_URL` を変更する

```env
DATABASE_URL=postgresql+asyncpg://memoapp_user:password@localhost:5432/memoapp_db
```

1. `asyncpg` をインストールする

```bash
uv sync --extra prod
```

1. テーブルを初期化する

```bash
uv run python init_database.py
```

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

```
fast_api_memoapp/
├── main.py               # アプリ起動・ミドルウェア・ルーター登録
├── config.py             # 設定管理（.env 読み込み）
├── db.py                 # DB エンジン・セッション（SQLite/PostgreSQL 自動判別）
├── init_database.py      # テーブル初期化スクリプト
├── pyproject.toml        # 依存パッケージ定義（uv sync 用）
├── .env                  # 環境設定（git 管理外）
├── .env.example          # 環境設定テンプレート
│
├── models/
│   └── memo.py           # SQLAlchemy モデル（memos / memo_histories）
│
├── schemas/
│   └── memo.py           # Pydantic スキーマ（入出力バリデーション）
│
├── cruds/
│   └── memo.py           # CRUD 処理（トランザクション・論理削除・履歴記録）
│
├── routers/
│   ├── memo.py           # REST API エンドポイント（/api/memos）
│   └── pages.py          # Jinja2 ページルーター（/）
│
├── templates/
│   ├── base.html         # ベーステンプレート
│   ├── index.html        # 一覧・作成フォーム
│   └── edit.html         # 編集フォーム・変更履歴
│
├── static/
│   └── styles.css        # サイト全体のスタイル
│
├── tests/
│   ├── conftest.py       # テスト共通フィクスチャ
│   ├── unit/             # 単体テスト（スキーマ）
│   ├── integration/      # 結合テスト（API）
│   └── e2e/              # E2E テスト（Playwright）
│
└── docs/                 # ドキュメント
    ├── 仕様書.md
    └── テスト仕様書・報告書.md
```

---

## ドキュメント

- [仕様書](docs/仕様書.md) — ER 図・API 一覧・処理フロー・ファイル依存関係
- [テスト仕様書・報告書](docs/テスト仕様書・報告書.md) — テスト仕様・実行結果
