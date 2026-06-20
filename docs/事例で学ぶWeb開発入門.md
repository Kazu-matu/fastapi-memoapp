# 事例で学ぶ Web 開発入門

| 項目 | 内容 |
| --- | --- |
| 作成日 | 2026-06-10 |
| 最終更新日 | 2026-06-20 |
| 版数 | v2.1 |
| 作成者 | Kazu-matu |

> **対象読者**: Python の文法（関数・クラス・型ヒント）は理解しているが、
> Web アプリを作ったことがない方
>
> **学習方針**: このメモアプリのコードを「答え」として読みながら、
> 「なぜこう書くのか」を理解する
>
> **ゴール**: この入門書を読みながら開発を進め、情報部門へのデプロイ依頼ができる状態まで到達する

---

## 目次

### バイブコーディング入門

- [0. バイブコーディングとは](#0-バイブコーディングとは)
- [0-A. 指示書（CLAUDE.md）を最初に作る](#0-a-指示書claudemdを最初に作る)
- [0-B. 開発の進め方（会話例）](#0-b-開発の進め方会話例)
- [0-C. 爆速開発を支える3つのコツ](#0-c-爆速開発を支える3つのコツ)

### 技術入門

1. [Web アプリとは何か](#1-web-アプリとは何か)
2. [アーキテクチャ：MVC パターン](#2-アーキテクチャmvc-パターン)
3. [このアプリの全体構造](#3-このアプリの全体構造)
4. [必要なライブラリと役割](#4-必要なライブラリと役割)
5. [FastAPI のルーティング](#5-fastapi-のルーティング)
6. [REST API とは何か](#6-rest-api-とは何か)
7. [Jinja2 テンプレートと連携の仕組み](#7-jinja2-テンプレートと連携の仕組み)
8. [フォーム送信の完全な流れ（PRG パターン）](#8-フォーム送信の完全な流れprg-パターン)
9. [データベースとの非同期通信](#9-データベースとの非同期通信)
10. [依存性注入（Depends）](#10-依存性注入depends)
11. [Pydantic によるバリデーション](#11-pydantic-によるバリデーション)
12. [セキュリティの基本](#12-セキュリティの基本)
13. [エラーハンドリング](#13-エラーハンドリング)
14. [テストの書き方と実行](#14-テストの書き方と実行)
15. [まとめ：リクエストからレスポンスまでの全経路](#15-まとめリクエストからレスポンスまでの全経路)
16. [開発完了チェックリスト](#16-開発完了チェックリスト)
17. [付録：コード一覧](#17-付録コード一覧)

### 仕上げ

- [18. よくある失敗パターンと対策](#18-よくある失敗パターンと対策)
- [19. ステップアップロードマップ](#19-ステップアップロードマップ)

---

## 0. バイブコーディングとは

**バイブコーディング（Vibe Coding）** とは、AI（Claude などの LLM）を"相棒"として使い、
自分はアイデアと方向性を決めるだけで、実装・修正・検証を AI に任せるプログラミングスタイルです。

```text
従来の開発:
  アイデア → 仕様書 → 設計 → 実装 → テスト → 完成（数週間〜）
                        ↑ ここで詰まる人が多い

バイブコーディング:
  アイデア → AI に話す → 動くものが出てくる → フィードバック → 完成（数時間〜）
```

### バイブコーディングの3原則

| 原則 | 説明 |
| --- | --- |
| **伝える** | やりたいことを日本語で AI に話す。コードは書かなくていい |
| **試す** | 動かしてみて「ここが違う」「これを追加して」と会話する |
| **記録する** | 決めたこと・ハマったことをドキュメントに残す。AI との会話はリセットされるため |

> **なぜ「信頼する」ではなく「記録する」が3原則に？**
> AI の出力は常に正しいとは限りません。「動かして確認する」「決定事項を残す」習慣が、
> バイブコーディングを安全で再現可能なものにします。

---

## 0-A. 指示書（\.ithub\copilot-instructions.md）を最初に作る

バイブコーディングで最も重要なのに、最も見落とされがちなのが **指示書** です。

### なぜ指示書が必要か

AI との会話は**毎回リセット**されます。
毎回「このプロジェクトは FastAPI で〜」と説明するのは非効率です。

```text
# 指示書なし
あなた：「エラーが出た」
AI：「どんなアプリですか？技術スタックは？」  ← 毎回これ

# 指示書あり（CLAUDE.md をプロジェクトルートに置くと自動読み込み）
あなた：「このエラーを直して」
AI：「cruds/memo.py の insert_memo ですね、flush() の前に履歴を追加しているのが原因です。」
       ← 即座に文脈把握
```

### このプロジェクトの指示書

`CLAUDE.md` がプロジェクトルートにあります。Claude Code はこれを自動で読み込みます。
他の AI ツールでは `.github/copilot-instructions.md` を参照してください。

```text
Claude Code   → CLAUDE.md をルートに置くと自動読み込み
Cursor        → .cursorrules として配置
GitHub Copilot → .github/copilot-instructions.md として配置
ChatGPT / Gemini → チャット冒頭にファイル内容をコピペ
```

### 指示書に書く7つの要素

| 要素 | 内容 | なぜ必要か |
| --- | --- | --- |
| **① プロジェクト概要** | 目的・実行方法・URL | AI がアプリの「何のため」を理解する |
| **② 技術スタック** | 言語・FW・ライブラリ・バージョン | 意図しない技術の追加を防ぐ |
| **③ ディレクトリ構成** | 各ファイルの役割コメント付き | どこに何を書くかを統一する |
| **④ アーキテクチャ原則** | 守るべきルール・禁止事項 | 設計の一貫性を保つ |
| **⑤ コーディング規約** | 必須パターン（try/rollback/raise 等） | 同じミスを繰り返させない |
| **⑥ やってはいけないこと** | 禁止事項のリスト | AI が悪手を繰り返すのを防ぐ |
| **⑦ 既知の制約・メモ** | ハマりやすい点・代替手段 | 調査済みの知識を引き継ぐ |

### 指示書を育てるタイミング

| タイミング | 追記する内容 |
| --- | --- |
| AI が同じミスを2回したとき | 「やってはいけないこと」に追記 |
| 新しいモジュールを追加したとき | 「ディレクトリ構成」を更新 |
| 設計の判断をしたとき | 「アーキテクチャ原則」に理由とともに追記 |
| ハマった問題を解決したとき | 「既知の制約」に追記 |

> 指示書は**生き物**です。プロジェクトとともに育てることで、
> AI が「初日から最終日まで同じ文脈で動く相棒」になります。

---

## 0-B. 開発の進め方（会話例）

### フェーズ1：最初の一歩「まず動かす」

#### 良い話しかけ方

```text
FastAPI と Jinja2 を使ったメモ管理アプリを作りたい。
CLAUDE.md のルールに従って、まず models/memo.py から作って。
タイトル・内容・優先度（高/中/低）の3項目を持つメモを管理したい。
```

**ポイント:**

- 「何を管理したいか」と「どんな項目があるか」を具体的に
- 「CLAUDE.md のルールに従って」と最初に明示する
- 技術的な詳細（テーブル定義等）は不要。指示書を読んだ AI が判断する

#### 避けたい話しかけ方

```text
メモアプリを作って。
```

抽象的すぎて AI も迷います。「誰が・何を・どう管理する」を意識しましょう。

---

### フェーズ2：機能追加「どんどん足す」

動くものができたら、会話で機能を積み重ねます。

```text
schemas/memo.py を作って。
優先度は「高」「中」「低」の3択で、スペースのみは弾いて。
```

```text
cruds/memo.py を作って。
insert / update / delete は全て try/rollback/raise パターンで。
変更履歴テーブルへの書き込みも入れて。
```

> **大きな変更の前に必ず git コミット**
>
> 新しいレイヤー・モジュールの追加など、複数ファイルが変わる作業の前には必ずセーブポイントを作ります。
>
> ```bash
> git add models/memo.py schemas/memo.py
> git commit -m "feat: add memo model and schema"
> ```
>
> こうすることで「cruds を作ったら models が壊れた」ときにすぐ元に戻せます。

---

### フェーズ3：バグ修正「エラーをそのまま貼る」

エラーが出たらエラーメッセージをそのままコピペするだけです。

```text
こんなエラーが出た：

sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: memos.title
Traceback:
  File "cruds/memo.py", line 28, in insert_memo
    await db.flush()
```

AI が原因（履歴レコードを flush 前に追加している）を特定して、修正まで実行してくれます。

**ポイント:**

- エラーを「恥ずかしい」と思わない。むしろエラーは AI への最高の情報
- 自分でデバッグしようとしない。まず AI に投げる
- 解決後は **CLAUDE.md の「既知の制約」に残す**（同じトラブルを繰り返さないため）

---

### フェーズ4：品質向上「こだわりを伝える」

```text
ページネーションを追加して。
1ページ20件、デフォルトは1ページ目で。
```

```text
routers/pages.py が長くなってきた。
保守性・可読性・拡張性を考えてリファクタリングして。
ただし外部から見た URL と動作は変えないで。
```

> **リファクタリング前のセーブポイント**
>
> ```bash
> git add .
> git commit -m "chore: checkpoint before refactor — pages.py 300 lines"
> ```

---

### フェーズ5：テスト・ドキュメント「完成させる」

```text
テスト仕様書（docs/03_テスト仕様書.md）を作って。
その後 tests/unit/test_schemas.py と tests/integration/test_api.py を書いて実行して。
```

```text
全テストが通ったので docs/04_報告書.md にテスト結果を記録して。
情報部門へのデプロイ依頼書も含めて。
```

**ポイント:**

- 「テストが通ったら完成」ではなく**ドキュメントが揃って完成**
- 報告書・デプロイ依頼書も AI が書いてくれる

---

## 0-C. 爆速開発を支える3つのコツ

### コツ1：「仕様書を先に」ではなく「動かしながら仕様を決める」

```text
バイブコーディング的な仕様決め:
「とりあえず models/memo.py を作って」
→ 動いた → 「優先度カラムも追加して」
→ 動いた → 「履歴テーブルも必要だった」
→ 動いた → 「検索機能も欲しい」
```

完璧な仕様書を書いてから動かすより、**動くものを育てる**方が圧倒的に早い。
ただし、動くたびに仕様書も少しずつ更新していくことで、後から書き直す手間をなくします。

---

### コツ2：「何をしたいか」と「なぜしたいか」をセットで伝える

```text
# NG：何をするかだけ
「エラーハンドリングを追加して」

# OK：なぜするかも添える
「業務中にネットワークエラーでデータが消えた経験があるので、
DB 書き込み時はエラー時に必ずロールバックして、
ユーザーには日本語でエラーメッセージを表示して。
スタックトレースは画面に出さないで。」
```

「なぜ」を伝えると、AI が**意図に合った実装**を選んでくれます。

---

### コツ3：AI を「コードを書く人」ではなく「一緒に考える人」として使う

```text
# 指示するだけの使い方（もったいない）
「ページネーションを実装して」

# 一緒に考える使い方（真のバイブコーディング）
「メモが増えてきたとき一覧が重くなりそう。
どんな対策が考えられる？ ページネーション・無限スクロール・検索絞り込みの
メリット・デメリットを比較して、このアプリに最適な案を提案して」
```

AI は実装だけでなく、**調査・設計・提案**もできます。

---

## 1. Web アプリとは何か

### 1-1. ブラウザとサーバーの会話

Web アプリは、**ブラウザ（クライアント）** と **サーバー** が会話することで動きます。
会話のルールを **HTTP（HyperText Transfer Protocol）** と言います。

```text
ブラウザ                          サーバー（FastAPI）
   │                                  │
   │ ── リクエスト（質問） ──────────→ │
   │   GET /  HTTP/1.1                │  「トップページをください」
   │   Host: localhost:8000           │
   │                                  │
   │ ← レスポンス（返答） ────────────  │
   │   HTTP/1.1 200 OK               │  「はい、どうぞ（HTML を返す）」
   │   Content-Type: text/html       │
   │   <html>...</html>              │
```

Python でいうと「関数を呼び出す → 戻り値が返ってくる」と同じです。
違うのは、**ネットワーク越しに** 呼び出す点だけです。

### 1-2. HTTP メソッド（動詞）

HTTP には「何をしたいか」を伝える **メソッド（動詞）** があります。

| メソッド | 意味 | Python の比喩 | このアプリでの使い方 |
| --- | --- | --- | --- |
| `GET` | データを取得する | `read()` | 一覧・詳細画面の表示 |
| `POST` | 新しいデータを送る | `create()` | フォームの登録・更新・削除 |
| `PUT` | 既存データを書き換える | `update()` | REST API での更新 |
| `DELETE` | データを消す | `delete()` | REST API での削除 |

> **なぜ HTML フォームでは POST しか使えないのか？**
> HTML の `<form>` タグは `method="get"` と `method="post"` しか対応していません。
> PUT・DELETE は JavaScript が必要なため、このアプリのフォーム画面では
> POST に統一し、URL パスで操作を区別しています（`/memos/{id}/delete` など）。

### 1-3. URL の構造

```text
http://localhost:8000/memos/3/edit
│      │              │     │  └─ パス末尾（操作名）
│      │              │     └───── パスパラメータ（ID = 3）
│      │              └─────────── パス名（リソース）
│      └────────────────────────── ホスト:ポート
└───────────────────────────────── プロトコル
```

---

## 2. アーキテクチャ：MVC パターン

### 2-1. MVC とは

コードが大きくなると「全部 1 ファイルに書く」と管理できなくなります。
そこで **役割ごとにファイルを分ける** 考え方が生まれました。それが **MVC** です。

| 文字 | 名前 | 役割 | 比喩 |
| --- | --- | --- | --- |
| **M** | Model（モデル） | データの構造・DB 操作 | 「倉庫と台帳」 |
| **V** | View（ビュー） | 画面の表示 | 「店頭のディスプレイ」 |
| **C** | Controller（コントローラー） | M と V をつなぐ司令塔 | 「店員さん」 |

```text
ブラウザ
  │
  ↓ リクエスト（「メモ一覧をください」）
[Controller]  routers/pages.py
  ↓ 「DB からデータとって」
[Model]       cruds/memo.py + models/memo.py
  ↓ 「データをここに渡すよ」
[Controller]  routers/pages.py
  ↓ 「このデータで HTML 作って」
[View]        templates/index.html
  ↓ HTML
ブラウザ（画面表示）
```

### 2-2. このアプリでの MVC 対応表

| MVC | このアプリのファイル | 具体的な仕事 |
| --- | --- | --- |
| Model | `models/memo.py` | テーブルの構造を定義する |
| Model | `cruds/memo.py` | SELECT / INSERT / UPDATE / DELETE を実行する |
| Model | `schemas/memo.py` | データの型・バリデーションを定義する |
| View | `templates/*.html` | HTML を生成する |
| Controller | `routers/pages.py` | フォームを受け取って CRUD を呼び出し、HTML を返す |
| Controller | `routers/memo.py` | JSON を受け取って CRUD を呼び出し、JSON を返す |

### 2-3. 各レイヤーが守るべき「1 ファイル 1 責任」の原則

| ファイル | やること | やってはいけないこと |
| --- | --- | --- |
| `main.py` | ルーター登録・ミドルウェア設定 | DB 操作・ビジネスロジック |
| `routers/` | URL 受け取り・crud 呼び出し | 直接 DB クエリを書く |
| `cruds/` | DB の読み書き処理 | HTTP レスポンスを作る |
| `schemas/` | 入出力の型定義 | DB クエリを書く |
| `models/` | テーブル定義 | バリデーションロジック |
| `templates/` | データの表示 | fetch/axios など JS での API 呼び出し |

> **なぜ分けるのか？**
> 「一つのファイルが一つの仕事だけをする」ことで、
> バグが起きたとき「どのファイルを見ればいいか」が明確になります。
> また、将来 DB を変えたい・画面だけ変えたいときに、
> 他の部分を触らずに済みます。

---

## 3. このアプリの全体構造

```text
ブラウザが「/」にアクセスする
         │
         ↓ HTTP GET
┌─────────────────────────────────────────────────────┐
│  main.py                                            │
│  FastAPI アプリの入り口                              │
│  ・セキュリティヘッダーなどのミドルウェアを登録      │
│  ・ルーターを登録（pages_router, memo_api_router）   │
└───────────────────┬─────────────────────────────────┘
                    │ どのルーターが処理するか振り分ける
          ┌─────────┴──────────┐
          ↓                    ↓
 routers/pages.py        routers/memo.py
 （画面用）               （REST API 用）
 GET / → HTML            GET /api/memos/ → JSON
          │
          ↓ DB からデータを取る
   cruds/memo.py
          │
          ↓ SQL を実行する
   models/memo.py  ←→  DB（SQLite または PostgreSQL）
          │
          ↑ データを受け取る
   routers/pages.py
          │
          ↓ HTML テンプレートにデータを渡す
   templates/index.html
          │
          ↓ 完成した HTML
        ブラウザ（表示）
```

---

## 4. 必要なライブラリと役割

`pyproject.toml` に書かれている依存パッケージを一つずつ理解しましょう。

```toml
# pyproject.toml（抜粋）
dependencies = [
    "fastapi>=0.115.0",          # Web フレームワーク本体
    "uvicorn[standard]>=0.30.0", # Web サーバー（FastAPI を動かす土台）
    "sqlalchemy>=2.0.0",         # ORM（DB 操作ライブラリ）
    "aiosqlite>=0.20.0",         # SQLite の非同期ドライバ（開発用）
    "pydantic>=2.0.0",           # データバリデーション
    "jinja2>=3.1.0",             # HTML テンプレートエンジン
    "python-multipart>=0.0.9",   # HTML フォームデータの受け取りに必要
    "python-dotenv>=1.0.0",      # .env ファイルの読み込み
]

[project.optional-dependencies]
prod = [
    "asyncpg>=0.29.0",           # PostgreSQL の非同期ドライバ（本番用）
]
```

### ライブラリの役割図

```text
リクエスト
    │
    ↓
[uvicorn]           サーバー。「80番窓口を開けてリクエストを待つ係」
    │
    ↓
[FastAPI]           ルーティング・バリデーション・レスポンス生成の総合管理
    │
    ├──[Pydantic]   受け取ったデータの型チェック・変換・バリデーション
    │
    ├──[Jinja2]     テンプレート + データ → HTML に変換
    │
    └──[SQLAlchemy] Python オブジェクト ↔ DB テーブルの変換（ORM）
           │
           └──[aiosqlite / asyncpg]   実際に SQL を DB に送るドライバ
```

### なぜ「非同期（async）」が必要か

```python
# 同期（普通の Python）
def get_memos():
    result = db.execute(...)   # ← DB の応答を待っている間、他のリクエストを処理できない
    return result

# 非同期（このアプリの書き方）
async def get_memos():
    result = await db.execute(...)  # ← 待っている間、別のリクエストを処理できる
    return result
```

Web アプリは同時に複数のユーザーからリクエストが来ます。
`async / await` を使うと、DB 待ちの間に他のリクエストを処理できて効率的です。

---

## 5. FastAPI のルーティング

### 5-1. ルーティングとは

「この URL にアクセスしたら、この Python 関数を呼ぶ」というマッピングです。

```python
# routers/pages.py
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/")          # ← 「GET /」 にアクセスしたら
async def index(request: Request):   # ← この関数を呼ぶ
    ...
```

`@router.get("/")` は **デコレータ** です。
Python で言うと「この関数を GET / に登録する」という指示書です。

### 5-2. パスパラメータ（URL に ID を含める）

```python
# routers/pages.py
@router.get("/memos/{memo_id}/edit")   # ← {memo_id} が変数部分
async def edit_form(
    request: Request,
    memo_id: int,             # ← URL の {memo_id} が自動でここに入る
):
    # memo_id = 3 なら /memos/3/edit にアクセスされたとき
    memo = await memo_crud.get_memo_by_id(session, memo_id)
```

`{memo_id}` の部分は URL の「穴あき」です。
`/memos/3/edit` にアクセスすると `memo_id = 3` が関数に渡されます。
`: int` を書くと FastAPI が自動で文字列 `"3"` を整数 `3` に変換してくれます。
文字列が来たら（`/memos/abc/edit`）自動で 422 エラーを返します。

### 5-3. クエリパラメータ（URL の `?` 以降）

```python
@router.get("/")
async def index(
    request: Request,
    msg: str = "",      # ← デフォルト値があるのでクエリパラメータ
):
    # /?msg=created でアクセスすると msg = "created"
    # /            でアクセスすると msg = "" （デフォルト）
```

`/?msg=created` の `msg=created` の部分がクエリパラメータです。
PRG パターンでリダイレクト後にフラッシュメッセージを渡すために使います。

### 5-4. ルーターの分割と main.py への登録

複数のルーターファイルに分けて、`main.py` で統合します。

```python
# main.py
from routers.memo  import router as memo_api_router
from routers.pages import router as pages_router

app = FastAPI(...)

app.include_router(pages_router)       # GET /  などの画面用
app.include_router(memo_api_router)    # GET /api/memos/ などの API 用
```

```python
# routers/memo.py
# prefix を付けると、全エンドポイントの URL に自動でプレフィックスが付く
router = APIRouter(tags=["Memos API"], prefix="/api/memos")

@router.get("/")          # ← 実際の URL は /api/memos/
@router.get("/{memo_id}") # ← 実際の URL は /api/memos/{memo_id}
```

### 5-5. ルーティングの一覧（このアプリ）

```text
main.py
 ├── pages_router（prefix なし）
 │     GET  /                   → index()        一覧画面
 │     POST /memos              → create_memo()  登録
 │     GET  /memos/{id}/edit    → edit_form()    編集画面
 │     POST /memos/{id}/edit    → update_memo()  更新
 │     POST /memos/{id}/delete  → delete_memo()  削除
 │
 └── memo_api_router（prefix="/api/memos"）
       POST   /api/memos/               → create_memo()      登録 API
       GET    /api/memos/               → get_memos_list()   全件取得 API
       GET    /api/memos/{id}           → get_memo_detail()  1件取得 API
       PUT    /api/memos/{id}           → modify_memo()      更新 API
       DELETE /api/memos/{id}           → remove_memo()      削除 API
       GET    /api/memos/{id}/histories → get_histories()    履歴 API
```

---

## 6. REST API とは何か

### 6-1. REST の考え方

**REST（Representational State Transfer）** は、Web API を設計するためのルールです。
「リソース（データ）」を「URL」で表し、「操作」を「HTTP メソッド」で表します。

```text
リソース = メモ（memo）
   │
   ├── /api/memos/           メモ「全体」
   │     GET    → 全件取得
   │     POST   → 新規作成
   │
   └── /api/memos/{id}       特定の「1件」のメモ
         GET    → 1件取得
         PUT    → 更新
         DELETE → 削除
```

### 6-2. JSON レスポンス

REST API は **JSON** 形式でデータをやり取りします。

```python
# routers/memo.py
@router.post("/", response_model=ResponseSchema, status_code=201)
async def create_memo(
    memo: InsertAndUpdateMemoSchema,   # ← JSON ボディを自動でパース
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    await memo_crud.insert_memo(session, memo, get_login_user())
    return ResponseSchema(message="メモが正常に登録されました")
    # ↑ Python オブジェクトを返すと FastAPI が自動で JSON に変換する
```

リクエストとレスポンスのやり取り:

```http
POST /api/memos/ HTTP/1.1
Content-Type: application/json

{"title": "買い物", "description": "牛乳を買う", "status": {"priority": "高"}}

─── レスポンス ───
HTTP/1.1 201 Created
Content-Type: application/json

{"message": "メモが正常に登録されました"}
```

### 6-3. ステータスコードの使い分け

```python
# 正常系
status_code=200   # 取得・更新・削除の成功
status_code=201   # 新規作成の成功（Created）

# エラー系
raise HTTPException(status_code=404, detail="メモが見つかりません")   # 存在しない
raise HTTPException(status_code=409, detail="すでに同名のメモがあります")  # 競合
# 422 はバリデーションエラー時に FastAPI が自動で返す

# やってはいけないこと
raise HTTPException(status_code=500, detail=str(e))  # 内部エラーの詳細を外部に漏らさない
```

---

## 7. Jinja2 テンプレートと連携の仕組み

### 7-1. テンプレートとは

Jinja2 は「**穴あき HTML**」を完成させるエンジンです。

```html
<!-- templates/index.html -->
<span class="login-user">ログイン: {{ login_user }}</span>
<!--                               ↑ ここにサーバーから渡した値が入る -->

{% for memo in memos %}
  <tr><td>{{ memo.title }}</td></tr>
{% endfor %}
```

Python のコードで言うと `f"ログイン: {login_user}"` と同じ発想です。

### 7-2. FastAPI から Jinja2 へのデータの渡し方

```python
# routers/pages.py
from fastapi.templating import Jinja2Templates
from pathlib import Path

# テンプレートの場所を絶対パスで指定する（相対パスは uvicorn の起動ディレクトリに依存するため危険）
templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)

@router.get("/")
async def index(request: Request, msg: str = "", session=Depends(...)):
    memos = await memo_crud.get_memos(session)

    return templates.TemplateResponse(
        request,           # ← 第1引数: リクエストオブジェクト（Starlette 1.x の書き方）
        "index.html",      # ← 第2引数: テンプレートファイル名
        {                  # ← 第3引数: テンプレートに渡すデータ（辞書）
            "memos":      memos,
            "msg":        msg,
            "login_user": get_login_user(),
        }
        # ⚠️ "request" をここの辞書に含めてはいけない（Starlette 1.x）
    )
```

### 7-3. テンプレートの継承（base.html）

毎回ヘッダーやフッターを書かなくていいように、**テンプレートを継承**できます。

```html
<!-- templates/base.html: 共通レイアウト -->
<!DOCTYPE html>
<html lang="ja">
<head>
  <title>{% block title %}メモアプリ{% endblock %}</title>
</head>
<body>
  <header>
    <h1>メモアプリ</h1>
    <span>ログイン: {{ login_user }}</span>
  </header>

  <main>
    <!-- フラッシュメッセージ（全ページ共通） -->
    {% if msg == "created" %}
      <div class="flash flash--success" role="alert">登録しました。</div>
    {% elif msg == "updated" %}
      <div class="flash flash--success" role="alert">更新しました。</div>
    {% elif msg == "deleted" %}
      <div class="flash flash--info" role="alert">削除しました。</div>
    {% elif msg == "error" %}
      <div class="flash flash--error" role="alert">エラーが発生しました。</div>
    {% endif %}

    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

```html
<!-- templates/index.html: base.html を継承 -->
{% extends "base.html" %}

{% block title %}メモ一覧{% endblock %}

{% block content %}
  <h2>メモ一覧</h2>
  ...
{% endblock %}
```

### 7-4. Jinja2 の主要構文

```html
<!-- 変数の表示（自動でHTMLエスケープされる） -->
{{ memo.title }}
{{ memo.due_date.strftime('%Y-%m-%d') if memo.due_date else '—' }}

<!-- ループ -->
{% for memo in memos %}
  <tr>
    <td>{{ memo.title }}</td>
  </tr>
{% else %}
  <tr><td colspan="5">メモがありません。</td></tr>
{% endfor %}

<!-- 条件分岐 -->
{% if memos %}
  <table>...</table>
{% else %}
  <p>メモがありません。</p>
{% endif %}

<!-- 絶対にやってはいけないこと -->
{{ memo.title | safe }}
<!-- ↑ ユーザーが入力した値に | safe を使うと XSS（クロスサイトスクリプティング）脆弱性になる -->
<!-- Jinja2 はデフォルトで自動エスケープするので、何もしなくて安全 -->
```

---

## 8. フォーム送信の完全な流れ（PRG パターン）

### 8-1. 問題：フォーム送信後のリロードで二重登録

```text
ユーザーが「登録」ボタンを押す
  → POST リクエスト
  → サーバーが DB に INSERT
  → サーバーが HTML を返す ← ここが問題！

ユーザーがブラウザを更新（F5）
  → もう一度 POST が送られる（二重登録！）
```

### 8-2. 解決策：PRG（Post-Redirect-Get）

```text
ユーザーが「登録」ボタンを押す
  → POST /memos
  → サーバーが DB に INSERT
  → サーバーが「303 リダイレクト」を返す ← PRG
  → ブラウザが自動で GET / にアクセス
  → サーバーが HTML を返す

ユーザーがブラウザを更新（F5）
  → GET / が再送される（POST ではないので二重登録しない）
```

> **なぜ 303 なのか？**
> 302 は「一時的なリダイレクト」ですが、古いブラウザでは POST のまま再送することがあります。
> 303 は「GET で移動してください」という意味で、必ず GET に変換されます。

### 8-3. コードで見る PRG

```python
# routers/pages.py

@router.post("/memos")
async def create_memo(
    request: Request,
    title:       Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    priority:    Annotated[str, Form()] = "低",
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    try:
        memo_data = InsertAndUpdateMemoSchema(title=title, description=description, ...)
        await memo_crud.insert_memo(session, memo_data, get_login_user())
        return RedirectResponse("/?msg=created", status_code=303)
    except Exception:
        # エラーが起きてもリダイレクトする（スタックトレースをユーザーに見せない）
        return RedirectResponse("/?msg=error", status_code=303)
```

### 8-4. HTML フォームの仕組み

```html
<form method="post" action="/memos">
  <input type="text" name="title" required minlength="1" maxlength="50">
  <!--                ↑ Python 側の引数名 title と一致させる -->

  <select name="priority">
    <option value="低">低</option>
    <option value="高">高</option>
  </select>

  <!-- 削除フォームには必ず確認ダイアログを付ける -->
  <form method="post" action="/memos/{{ memo.memo_id }}/delete"
        onsubmit="return confirm('削除してよいですか？この操作は取り消せません。')">
    <button type="submit">削除</button>
  </form>
</form>
```

---

## 9. データベースとの非同期通信

### 9-1. ORM とは何か

**ORM（Object-Relational Mapping）** は、DB のテーブルを Python のクラスとして扱えるようにする仕組みです。

```python
# SQL を直接書く場合（ORM なし）
# 問題点: 文字列を結合すると SQL インジェクション脆弱性になる危険がある
cursor.execute(f"SELECT * FROM memos WHERE title = '{title}'")  # 危険！

# ORM（SQLAlchemy）を使う場合
# SQLAlchemy が安全にパラメータを処理してくれる
select(Memo).where(Memo.title == title)  # 安全
```

ORM を使うと:

- SQL インジェクション（セキュリティの脆弱性）を自動的に防げる
- DB を SQLite から PostgreSQL に変えてもコードをほぼ変えなくていい
- Python のオブジェクトとして直感的に操作できる

### 9-2. モデル定義（models/memo.py）

```python
# models/memo.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from db import Base
from datetime import datetime

class Memo(Base):
    __tablename__ = "memos"  # ← 必ず書く。省略禁止。

    # 主キー
    memo_id = Column(Integer, primary_key=True, autoincrement=True)

    # ビジネスカラム
    title       = Column(String(50),  nullable=False)
    description = Column(String(500), nullable=False, default="")
    priority    = Column(String(10),  nullable=False, default="低")

    # 全テーブル共通の監査カラム（必須）
    is_deleted  = Column(Boolean,  default=False,      nullable=False)  # 論理削除フラグ
    deleted_at  = Column(DateTime, nullable=True)                       # 削除日時
    created_at  = Column(DateTime, default=datetime.now, nullable=False)
    updated_at  = Column(DateTime, onupdate=datetime.now, nullable=True)
    created_by  = Column(String(100), nullable=False)   # 誰が作ったか
    updated_by  = Column(String(100), nullable=True)    # 誰が最後に更新したか
```

> **なぜ `nullable=False` を多用するのか？**
> `nullable=True`（NULL を許可）にすると、値が入っていないのか存在しないのかが区別できず、
> バグの原因になります。業務上 NULL が正当な値でない限り `nullable=False` にします。

### 9-3. CRUD 操作（cruds/memo.py）

#### 新規登録：INSERT

```python
# cruds/memo.py
async def insert_memo(db: AsyncSession, memo_data, user: str):
    try:
        new_memo = Memo(
            title=memo_data.title,
            created_by=user,
            updated_by=user,
        )
        db.add(new_memo)         # ← INSERT の予約（まだ DB に送らない）
        await db.flush()         # ← DB に送るが、コミット（確定）はしない
        # ↑ flush() で memo_id が確定する（履歴レコードに memo_id を使うために必要）

        db.add(_build_history(new_memo, "CREATE", user))

        await db.commit()        # ← 2つのレコードを同時に確定保存
        await db.refresh(new_memo)
        return new_memo
    except Exception:
        await db.rollback()      # ← 失敗したら全部なかったことにする（必須）
        raise                    # ← エラーを握り潰さず再発生させる（必須）
```

#### flush() と commit() の違い（重要）

```text
db.add(new_memo)
    │
    ↓ flush() ← SQL は送るが確定しない（ロールバック可能な状態）
   DB: INSERT（仮）→ memo_id が採番される
    │
    ↓ 履歴レコードも add（memo_id が使える）
    │
    ↓ commit() ← 確定（ここから取り消し不可）
   DB: 両方のレコードが確定保存される
    │
    エラー発生 → rollback() → 両方のレコードが消える
```

#### 全件取得：SELECT

```python
async def get_memos(db: AsyncSession) -> list[Memo]:
    result = await db.execute(
        select(Memo)
        .where(Memo.is_deleted == False)  # ← 削除済みを除外（必須）
        .order_by(Memo.memo_id)
    )
    return list(result.scalars().all())
```

#### 論理削除（物理削除は使わない）

```python
async def delete_memo(db: AsyncSession, memo_id: int, user: str):
    memo = await _get_active_memo(db, memo_id)
    if not memo:
        return None
    try:
        memo.is_deleted = True           # ← フラグを立てるだけ
        memo.deleted_at = datetime.now() # ← 削除日時を記録
        memo.updated_by = user
        db.add(_build_history(memo, "DELETE", user))
        await db.commit()
        return memo
    except Exception:
        await db.rollback()
        raise
```

> **なぜ論理削除を使うのか？**
> 物理削除（`db.delete(memo)`）は完全にデータが消えます。
> 論理削除は `is_deleted = True` にするだけで「見えなくする」技術です。
> 誤操作で消した場合に復元できる、削除履歴が残るなどの利点があります。

### 9-4. DB セッションの仕組み（db.py）

```python
# db.py
async def get_dbsession():
    async with async_session() as session:   # ← セッション開始
        yield session                         # ← ルーター関数に渡す
    # ← with ブロックを抜けると自動でセッションを閉じる（close() 不要）
```

> **セッション（Session）** とは: DB との「会話の単位」です。
> 1 回のリクエストで複数の SQL を実行しても、
> 同じセッション内なら 1 つのトランザクションとして管理できます。

---

## 10. 依存性注入（Depends）

### 10-1. Depends とは

「この関数の引数に、あの処理の結果を自動で渡して」という仕組みです。

```python
@router.get("/")
async def index(
    request: Request,
    session: AsyncSession = Depends(app_db.get_dbsession),
    # ↑ 「get_dbsession() の戻り値を session に自動で渡して」という指示
):
    memos = await memo_crud.get_memos(session)
```

`Depends(app_db.get_dbsession)` と書くだけで:

1. FastAPI が `get_dbsession()` を呼ぶ
2. DB セッションが作られる
3. そのセッションが `session` 引数に入る
4. リクエスト終了後に自動でセッションが閉じられる

### 10-2. なぜ Depends を使うのか

```python
# Depends を使わない場合（毎回同じコードを書く必要がある）
@router.get("/")
async def index():
    async with async_session() as session:   # 毎回書く
        memos = await memo_crud.get_memos(session)

@router.post("/memos")
async def create_memo():
    async with async_session() as session:   # また書く
        await memo_crud.insert_memo(...)

# Depends を使う場合（繰り返しがなくてスッキリ）
@router.get("/")
async def index(session = Depends(app_db.get_dbsession)):
    memos = await memo_crud.get_memos(session)

@router.post("/memos")
async def create_memo(session = Depends(app_db.get_dbsession)):
    await memo_crud.insert_memo(...)
```

### 10-3. Depends のもう一つの使い方：404 処理の共通化

```python
# 「存在するメモを取得する。なければ 404 を返す」を依存として定義する
async def get_memo_or_404(
    memo_id: int,
    session: AsyncSession = Depends(app_db.get_dbsession)
):
    memo = await memo_crud.get_memo_by_id(session, memo_id)
    if memo is None:
        raise HTTPException(status_code=404, detail="メモが見つかりません")
    return memo

# 複数のエンドポイントで再利用できる
@router.get("/{memo_id}")
async def get_memo(memo=Depends(get_memo_or_404)):
    return memo

@router.put("/{memo_id}")
async def update_memo(data: UpdateSchema, memo=Depends(get_memo_or_404)):
    ...
```

---

## 11. Pydantic によるバリデーション

### 11-1. Pydantic とは

受け取ったデータの**型チェック・変換・バリデーション**を自動でやってくれます。

```python
# schemas/memo.py
from pydantic import BaseModel, Field, field_validator

class MemoCreateSchema(BaseModel):
    title:       str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)
    priority:    str = Field(default="低")

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        # "   "（スペースのみ）はmin_length=1を通過してしまうため、明示的に弾く
        if not v.strip():
            raise ValueError("タイトルは空白のみは入力できません")
        return v.strip()   # 前後の空白を除去して保存
```

これを使うと FastAPI は自動で:

```text
正常なリクエスト:
  {"title": "買い物", "description": "牛乳"} → 問題なし

title が空のリクエスト:
  {"title": "", "description": "牛乳"} → 422 Unprocessable Entity（自動）

title がないリクエスト:
  {"description": "牛乳"} → 422 Unprocessable Entity（自動）
```

### 11-2. スキーマの4つの種類

```python
# ① 登録用（外から受け取るデータ）
class MemoCreateSchema(BaseModel):
    title: str = Field(min_length=1, max_length=50)

# ② 更新用（全フィールドがオプション）
class MemoUpdateSchema(BaseModel):
    title:       str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    # None のフィールドは更新しない（部分更新）

# ③ レスポンス用（DB の値を含めて返すデータ）
class MemoSchema(BaseModel):
    model_config = {"from_attributes": True}  # SQLAlchemy → Pydantic 変換に必須

    memo_id:    int
    title:      str
    created_at: datetime
    created_by: str
    # ⚠️ is_deleted・deleted_at など内部フィールドは絶対に含めない

# ④ 操作結果用（成功/失敗のメッセージだけ）
class ResponseSchema(BaseModel):
    message: str
```

---

## 12. セキュリティの基本

> **なぜセキュリティを学ぶ必要があるのか？**
> 業務で使うアプリには社内データが入ります。
> セキュリティの不備は情報漏えいや不正操作につながります。
> このフレームワークの規約を守れば主要な脆弱性は防げます。

### 12-1. SQL インジェクション（SQLAlchemy が自動で防ぐ）

```python
# 危険：文字列結合でクエリを作る
# ユーザーが title に「'; DROP TABLE memos; --」と入力するとDBが破壊される
query = f"SELECT * FROM memos WHERE title = '{title}'"  # 絶対にやってはいけない

# 安全：SQLAlchemy の ORM を使う（パラメータを安全に処理してくれる）
select(Memo).where(Memo.title == title)  # これなら安全
```

### 12-2. XSS（Jinja2 が自動で防ぐ）

```html
<!-- ユーザーが title に "<script>alert('hack')</script>" と入力した場合 -->

<!-- Jinja2 のデフォルト動作（安全） -->
{{ memo.title }}
<!-- 出力: &lt;script&gt;alert('hack')&lt;/script&gt; （無害なテキストになる） -->

<!-- | safe を使うと危険！ -->
{{ memo.title | safe }}
<!-- 出力: <script>alert('hack')</script> （スクリプトが実行される） -->

<!-- ルール: ユーザーが入力した値には絶対に | safe を使わない -->
```

### 12-3. 機密情報の管理（.env ファイル）

```python
# ❌ 絶対にやってはいけないこと：ソースコードに直接書く
DATABASE_URL = "postgresql://admin:password123@db.company.local/app"

# ✅ 正しいやり方：.env ファイルに書いて、コードから読み込む
# .env ファイル（git には含めない）
DATABASE_URL=postgresql://admin:password123@db.company.local/app

# config.py
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

`.gitignore` に必ず含めるもの:

```gitignore
.env        # ← 機密情報（絶対に git に含めない）
*.sqlite    # ← DB ファイル
*.db        # ← DB ファイル
__pycache__/
.venv/
```

### 12-4. エラーメッセージで内部情報を漏らさない

```python
# ❌ やってはいけないこと：エラーの詳細をそのまま返す
raise HTTPException(status_code=500, detail=str(e))
# → "UNIQUE constraint failed: memos.title" などの DB 内部情報が外に漏れる

# ✅ 正しいやり方：利用者向けのメッセージだけを返す
raise HTTPException(status_code=500, detail="処理中にエラーが発生しました")

# 内部エラーはログに記録する（利用者には見せない）
import logging
logger = logging.getLogger(__name__)
logger.exception("メモ登録中にエラー発生 user=%s", user)
```

### 12-5. セキュリティヘッダー（main.py に追加する）

```python
# main.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # 他のサイトがこのアプリを iframe に埋め込めないようにする
        response.headers["X-Frame-Options"] = "DENY"
        # ブラウザが Content-Type を自動判定しないようにする
        response.headers["X-Content-Type-Options"] = "nosniff"
        # リファラー（どこからアクセスしたか）の漏えいを制限する
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

## 13. エラーハンドリング

### 13-1. 基本的な考え方

```text
エラーの種類と対処方法:

① ユーザーの入力ミス（422）
   → FastAPI + Pydantic が自動で処理してくれる

② リソースが見つからない（404）
   → raise HTTPException(status_code=404, ...) で明示的に返す

③ 予期しないエラー（500）
   → ログに記録して、ユーザーには「エラーが発生しました」とだけ伝える
   → スタックトレースや DB 情報は絶対にユーザーに見せない
```

### 13-2. グローバルエラーハンドラ（main.py）

```python
# main.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 内部ログ：詳細なエラー情報を記録する
    logger.exception(
        "予期しないエラー: method=%s path=%s",
        request.method, request.url.path
    )
    # 外部レスポンス：利用者向けのメッセージのみ
    return JSONResponse(
        status_code=500,
        content={"detail": "サーバー内部でエラーが発生しました。管理者にお問い合わせください。"},
    )
```

### 13-3. ログの設定（main.py）

```python
# main.py
import logging

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    # 本番環境ではファイルにも出力する
    # handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
```

**ログレベルの使い分け:**

```python
logger = logging.getLogger(__name__)

logger.info("メモを登録しました memo_id=%d user=%s", memo.memo_id, user)
# → 正常な操作の記録

logger.warning("存在しない ID へのアクセス memo_id=%d", memo_id)
# → 異常だが処理は継続できる場合

logger.exception("メモ登録中にエラーが発生しました")
# → exception() はスタックトレースも一緒に記録してくれる

# ❌ やってはいけないこと
logger.info("DB パスワード: %s", db_password)   # 機密情報をログに出さない
logger.error(str(exc))  # exception() を使えばスタックトレースが自動で付く
```

---

## 14. テストの書き方と実行

### 14-1. なぜテストを書くのか

```text
テストがある → コードを変更しても「壊れていないか」を即座に確認できる
テストがない → 変更するたびに手動で全機能を確認しなければならない
            → 変更が怖くなり、アプリが死蔵される
```

### 14-2. テストの種類

| 種類 | 何をテストするか | このアプリでの場所 |
| --- | --- | --- |
| 単体テスト | スキーマのバリデーションが正しく動くか | `tests/unit/test_schemas.py` |
| 結合テスト | API エンドポイントが正しく動くか（実際の DB を使って） | `tests/integration/test_api.py` |
| E2E テスト | ブラウザ操作で画面が正しく動くか | `tests/e2e/test_memo.py` |

### 14-3. conftest.py（テスト共通設定）

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db import Base, get_db

# テスト用 DB はインメモリ SQLite（本番 DB には絶対に接続しない）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # 同じ接続を再利用（インメモリ SQLite に必要）
)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)  # 全テストで自動実行
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # テーブルを作る
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)     # テーブルを消す（次のテストに影響しない）

@pytest_asyncio.fixture
async def client():
    # 本番 DB の代わりにテスト DB を使うように差し替える
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

### 14-4. テストの書き方

```python
# tests/integration/test_api.py
import pytest

@pytest.mark.asyncio
async def test_create_memo_success(client):
    """正常に登録できること"""
    response = await client.post("/api/memos/", json={
        "title": "テストメモ",
        "description": "テスト内容",
        "status": {"priority": "低"}
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "テストメモ"
    assert "memo_id" in data
    assert "is_deleted" not in data  # 内部フィールドが外部に漏れていないこと

@pytest.mark.asyncio
async def test_create_memo_empty_title(client):
    """タイトルが空の場合は 422 を返すこと"""
    response = await client.post("/api/memos/", json={
        "title": "",
        "description": "テスト",
        "status": {"priority": "低"}
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_deleted_memo_not_in_list(client):
    """削除したメモは一覧に表示されないこと"""
    # 登録
    create = await client.post("/api/memos/", json={"title": "削除テスト", ...})
    memo_id = create.json()["memo_id"]

    # 削除
    await client.delete(f"/api/memos/{memo_id}")

    # 一覧に含まれないことを確認
    list_response = await client.get("/api/memos/")
    ids = [m["memo_id"] for m in list_response.json()]
    assert memo_id not in ids
```

### 14-5. テストの実行コマンド

```bash
# 単体テスト + 結合テストを実行（開発中はこれを繰り返す）
uv run pytest tests/unit/ tests/integration/ -v

# 全テスト（E2E を含む。サーバーを起動した状態で実行）
uv run pytest tests/ -v

# 特定のテストだけ実行
uv run pytest tests/integration/test_api.py::test_create_memo_success -v

# 短いエラー表示
uv run pytest tests/ --tb=short

# テスト結果をファイルに保存（デプロイ依頼書に添付する）
uv run pytest tests/unit/ tests/integration/ -v > tests/test_result.txt 2>&1
```

---

## 15. まとめ：リクエストからレスポンスまでの全経路

### ケース：「登録ボタンを押してからページが表示されるまで」

```text
[ブラウザ]
  │ ① フォームに入力して「登録」ボタンを押す
  ↓ POST /memos
  │   Content-Type: application/x-www-form-urlencoded
  │   title=買い物&priority=高&description=牛乳

[main.py]
  │ ② セキュリティヘッダーミドルウェアが通過する

[routers/pages.py: create_memo()]
  │ ③ URL "/memos" にマッチするルーターが呼ばれる
  │ ④ Form() がフォームデータを Python の変数に変換する
  │ ⑤ Depends(get_dbsession) が DB セッションを自動で作って渡す

[schemas/memo.py: MemoCreateSchema]
  │ ⑥ Pydantic がバリデーション（title が空なら自動で 422 を返す）

[cruds/memo.py: insert_memo()]
  │ ⑦ Memo オブジェクトを作る
  │ ⑧ db.add(new_memo) → INSERT の予約
  │ ⑨ await db.flush() → DB に送るが未確定（memo_id が採番される）
  │ ⑩ db.add(history) → 履歴も予約
  │ ⑪ await db.commit() → 2つのレコードを同時に確定保存
  │   エラーの場合 → await db.rollback() → raise → ルーターへ

[routers/pages.py: create_memo()]
  │ ⑫ 正常: RedirectResponse("/?msg=created", status_code=303)
  │    エラー: RedirectResponse("/?msg=error", status_code=303)

[ブラウザ]
  │ ⑬ 303 を受け取り、自動で GET /?msg=created にアクセス

[routers/pages.py: index()]
  │ ⑭ GET / のルーターが呼ばれる
  │ ⑮ get_memos(session) で is_deleted = False のメモを全件取得

[templates/index.html]
  │ ⑯ Jinja2 が memos リストを HTML に展開
  │ ⑰ msg="created" → フラッシュメッセージを表示

[ブラウザ]
  ⑱ 完成した HTML が表示される
     「登録しました。」が表示される
     テーブルに新しいメモが追加されている
```

---

## 16. 開発完了チェックリスト

リリース前・デプロイ依頼前に必ず確認してください。

### A. 実装品質チェック

```text
□ models/: 全テーブルに is_deleted, created_at, updated_at, created_by, updated_by がある
□ models/: 全メインテーブルに対応する履歴テーブルがある
□ cruds/ : 全書き込み操作に try/except + rollback + raise がある
□ cruds/ : SELECT クエリに is_deleted == False フィルタがある
□ cruds/ : flush() を commit() より前に呼んでいる（履歴 ID 確保のため）
□ routers/: POST の後は必ず RedirectResponse(status_code=303) にしている
□ routers/: ビジネスロジックをルーターに書いていない（cruds/ にある）
□ schemas/: レスポンスに is_deleted / deleted_at / パスワード等を含めていない
□ templates/: ユーザー入力値に | safe を使っていない
□ templates/: 削除フォームに confirm() ダイアログがある
□ templates/: 全ページが base.html を継承している
```

### B. セキュリティチェック

```text
□ .env を git に追加していない（git status で確認）
□ .gitignore に .env / *.sqlite / *.db が含まれている
□ ソースコードに DB パスワード・API キーが書かれていない
□ HTTPException の detail にスタックトレースや DB 情報を含めていない
□ SQL を文字列結合で作っていない（SQLAlchemy ORM のみ使用）
□ エラーログが適切に記録される（logger.exception を使用）
```

### C. テストチェック

```text
□ uv run pytest tests/unit/ tests/integration/ -v が全て PASSED
□ スキーマの正常・異常ケースをテストしている
□ 主要 API エンドポイント（POST/GET/PUT/DELETE）をテストしている
□ 削除後に 404 になることをテストしている
□ 履歴レコードが作成されることをテストしている
```

### D. ドキュメントチェック

```text
□ docs/01_要件定義.md を作成した（何を作るか：目的・機能・制約）
□ docs/02_仕様書.md が最新の状態になっている（ER 図・API 一覧・画面仕様）
□ docs/03_テスト仕様書.md にテストケースを記載した
□ docs/04_報告書.md にテスト結果・不具合・デプロイ依頼を記録した
□ README.md にセットアップ手順を書いた

# テンプレートは docs/テンプレート_0*.md を使うこと
# create_template.py を実行すると 01〜04 の雛形が自動生成される
□ .env.example を最新の状態に保っている
```

---

## 17. 付録：コード一覧

| 技術 | このアプリでの使われ方 | ファイル |
| --- | --- | --- |
| `@router.get()` | URL とルーター関数の紐付け | `routers/pages.py` |
| `@router.post()` | フォーム POST の受け取り | `routers/pages.py` |
| `Depends(...)` | DB セッションを自動で渡す | 全ルーターファイル |
| `Form()` | HTML フォームの値を受け取る | `routers/pages.py` |
| `HTTPException` | 404 などのエラーを返す | `routers/memo.py` |
| `RedirectResponse` | PRG のリダイレクト | `routers/pages.py` |
| `TemplateResponse` | HTML テンプレートを返す | `routers/pages.py` |
| `{% extends %}` | テンプレート継承 | `templates/index.html` |
| `{% for %}` | テンプレートのループ | `templates/index.html` |
| `{{ 変数 }}` | テンプレートへの値の埋め込み | 全テンプレートファイル |
| `Column(...)` | DB テーブルのカラム定義 | `models/memo.py` |
| `db.add()` | INSERT の予約 | `cruds/memo.py` |
| `db.flush()` | SQL を送るが未確定（ID 確保） | `cruds/memo.py` |
| `db.commit()` | DB に確定保存 | `cruds/memo.py` |
| `db.rollback()` | 失敗時の全取り消し | `cruds/memo.py` |
| `select(Model).where(...)` | SELECT クエリの構築 | `cruds/memo.py` |
| `Field(min_length=1)` | バリデーションの定義 | `schemas/memo.py` |
| `field_validator` | カスタムバリデーション | `schemas/memo.py` |
| `model_config` | SQLAlchemy → Pydantic 変換設定 | `schemas/memo.py` |
| `load_dotenv()` | .env ファイルの読み込み | `config.py` |
| `NullPool` | SQLite 用のコネクションプール設定 | `db.py` |
| `logger.exception()` | エラーをスタックトレース付きで記録 | 全 cruds ファイル |

---

## 18. よくある失敗パターンと対策

### 失敗1：AI が「指示書を守っていないコード」を書いた

**起きやすい場面:** 長い会話セッションの後半や、会話をリセットした後

**原因:** AI は会話の最初にしか `CLAUDE.md` を深く読んでいないことがある

**対策:**

```text
「CLAUDE.md のルールを確認して、今書いたコードが守れているかチェックして」
```

会話が長くなってきたと感じたら、新しい会話を始めて `CLAUDE.md` を再読させます。

---

### 失敗2：SQL インジェクション対策ゼロのコードが生成された

**起きやすい場面:** 「手っ取り早く動くものを」と頼んだとき

**原因:** AI が `f"SELECT * FROM memos WHERE title = '{title}'"` のような文字列結合 SQL を書いた

**対策:** 指示書に「SQL は必ず SQLAlchemy ORM で書く」と明記し、生成後に確認する

```text
「生成したコードに文字列結合で SQL を組み立てている箇所がないかチェックして」
```

---

### 失敗3：大きな変更後に「元に戻せない」

**起きやすい場面:** DB スキーマの変更・大規模リファクタリング

**原因:** 変更前に `git commit` を忘れていた

**対策:** 「2ファイル以上が変わる作業」の前は必ずコミット

```bash
git add models/memo.py schemas/memo.py
git commit -m "chore: checkpoint before adding history table"
```

AI はこの習慣を促してくれます。しかし促されなかった場合でも、**自分でセーブポイントを作る癖をつける**のが安全策です。

---

### 失敗4：API キーをソースコードに直書き

**起きやすい場面:** 「とりあえず動かしたい」急いでいるとき

```python
# ❌ 絶対にやってはいけない
ESTAT_APP_ID = "0009876543210987654321"
```

**対策:** `.env` に書いて `python-dotenv` で読み込む。`.gitignore` に `.env` を追加する

```python
# ✅
import os
ESTAT_APP_ID = os.getenv("ESTAT_APP_ID", "")
```

GitHub にプッシュした瞬間、BOT に API キーを抜かれて悪用されるリスクがあります。

---

### 失敗5：ドキュメントを「後で書く」と先送りした

**よくあるパターン:**

```text
実装 → 実装 → 実装 → テスト → 「あとでドキュメント書こう」→ 忘れる → 引き継ぎできない
```

**対策:** ドキュメントを実装と並走させる

| タイミング | 更新するドキュメント |
| --- | --- |
| テーブルを決めたとき | `02_仕様書.md`（ER 図） |
| API を追加したとき | `02_仕様書.md`（API 一覧） |
| テストを追加したとき | `03_テスト仕様書.md` |
| テストを実行したとき | `04_報告書.md`（テスト結果） |
| デプロイ前 | `04_報告書.md`（デプロイ依頼書） |

AI に「ドキュメントも更新して」と頼むだけで書いてくれます。習慣にしましょう。

---

### 失敗6：「物理削除」を使ってしまった

**起きやすい場面:** AI に「削除機能を実装して」と頼んだとき

**原因:** AI が `db.delete(memo)` を書いた（物理削除）

**対策:** 指示書に「物理削除は使わない。`is_deleted = True` で論理削除」と明記

業務アプリでは「間違えて削除した」「復元したい」はよくある要求です。
物理削除は一度実行すると取り消せません。

---

## 19. ステップアップロードマップ

このドキュメントで学んだ内容は「Web アプリ開発の基礎」です。
次のステップとして、以下の方向性でスキルを伸ばせます。

### このドキュメントで習得できること

| スキル | 説明 |
| --- | --- |
| バイブコーディング | AI と会話しながらアプリを作る開発スタイル |
| AI 指示書の作成 | プロジェクトの文脈を AI に引き継ぐ方法 |
| FastAPI ルーティング | URL と Python 関数のマッピング |
| Jinja2 テンプレート | Python の値を HTML に埋め込む |
| SQLAlchemy ORM | Python のコードで DB を操作する |
| Pydantic バリデーション | 入力値の検証と型安全 |
| PRG パターン | フォーム送信後のリダイレクト |
| 論理削除 | データを消さずに「消したことにする」 |
| 変更履歴テーブル | いつ誰が変更したかを追跡する |
| pytest でのテスト | 自動テストを書いて品質を守る |
| ドキュメント整備 | 4 種類のドキュメントを揃えて引き継げる状態にする |

### 次のステップ

| レベル | 学ぶこと | 参考 |
| --- | --- | --- |
| **入門** ← 今ここ | このドキュメントの内容 | |
| **初級** | 認証・認可（ログイン機能） | FastAPI Security |
| **初級** | ファイルアップロード | FastAPI File Upload |
| **中級** | バックグラウンドタスク | Celery + Redis |
| **中級** | PostgreSQL 本番環境 | asyncpg + Docker |
| **中級** | REST API とフロントの分離 | FastAPI + React |
| **上級** | マイクロサービス化 | Docker Compose |
| **上級** | CI/CD パイプライン | GitHub Actions |

### バイブコーディングで学び続けるコツ

```text
1. 「動くもの」を毎回作る
   → チュートリアルを読むより、AI と話しながら作る方が圧倒的に速い

2. エラーを怖がらない
   → エラーは「AI への質問の種」。コピペするだけで解決策が出る

3. CLAUDE.md を育て続ける
   → 同じミスを繰り返さなくなり、開発スピードが加速する

4. ドキュメントを残す
   → 「過去の自分」に感謝されるコードと資料が、チームの財産になる
```
