# 事例で学ぶ Web 開発入門

| 項目 | 内容 |
| --- | --- |
| 作成日 | 2026-06-10 |
| 最終更新日 | 2026-06-10 |
| 版数 | v1.0 |
| 作成者 | Kazu-matu |

> **対象読者**: Python の文法（関数・クラス・型ヒント）は理解しているが、  
> Web アプリを作ったことがない方  
> **学習方針**: このメモアプリのコードを「答え」として読みながら、  
> 「なぜこう書くのか」を理解する

---

## 目次

1. [Web アプリとは何か](#1-web-アプリとは何か)
2. [アーキテクチャ：MVC パターン](#2-アーキテクチャmvc-パターン)
3. [このアプリの全体構造](#3-このアプリの全体構造)
4. [必要なライブラリと役割](#4-必要なライブラリと役割)
5. [FastAPI のルーティング](#5-fastapi-のルーティング)
6. [REST API とは何か](#6-rest-api-とは何か)
7. [Jinja2 テンプレートと連携の仕組み](#7-jinja2-テンプレートと連携の仕組み)
8. [フォーム送信の完全な流れ（PRG パターン）](#8-フォーム送信の完全な流れprgパターン)
9. [データベースとの非同期通信](#9-データベースとの非同期通信)
10. [依存性注入（Depends）](#10-依存性注入depends)
11. [Pydantic によるバリデーション](#11-pydantic-によるバリデーション)
12. [まとめ：リクエストからレスポンスまでの全経路](#12-まとめリクエストからレスポンスまでの全経路)

---

## 1. Web アプリとは何か

### 1-1. ブラウザとサーバーの会話

Web アプリは、**ブラウザ（クライアント）** と **サーバー** が会話することで動きます。  
会話のルールを **HTTP（HyperText Transfer Protocol）** と言います。

```
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

| メソッド | 意味 | Python の比喩 |
| --- | --- | --- |
| `GET` | データを取得する | `read()` |
| `POST` | 新しいデータを送る | `create()` |
| `PUT` | 既存データを書き換える | `update()` |
| `DELETE` | データを消す | `delete()` |

このアプリでは全部使います。

### 1-3. URL の構造

```
http://localhost:8000/memos/3/edit
│      │              │     │  └─ パス末尾（操作名）
│      │              │     └───── パスパラメータ（ID = 3）
│      │              └─────────── パス名
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

```
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

> **補足**: MVC の「亜種」として MVVM（Model-View-ViewModel）もよく聞きます。  
> React / Vue などのフロントフレームワークがこれに近い考え方です。  
> このアプリは**サーバー側で HTML を生成する**（SSR: Server Side Rendering）ため  
> 純粋な MVC に近い構成です。

---

## 3. このアプリの全体構造

```
ブラウザが「/」にアクセスする
         │
         ↓ HTTP GET
┌─────────────────────────────────────────────────────┐
│  main.py                                            │
│  FastAPI アプリの入り口                              │
│  ・ミドルウェア（ログ記録）を登録                    │
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
    "fastapi>=0.115.0",        # Web フレームワーク本体
    "uvicorn[standard]>=0.30.0", # Web サーバー
    "sqlalchemy>=2.0.0",       # ORM（DB 操作ライブラリ）
    "aiosqlite>=0.20.0",       # SQLite の非同期ドライバ
    "pydantic>=2.0.0",         # データバリデーション
    "jinja2>=3.1.0",           # HTML テンプレートエンジン
    "python-multipart>=0.0.9", # フォームデータの受け取り
    "python-dotenv>=1.0.0",    # .env ファイルの読み込み
]
```

### ライブラリの役割図

```
リクエスト
    │
    ↓
[uvicorn]           サーバー。「80番窓口を開けてリクエストを待つ係」
    │
    ↓
[FastAPI]           ルーティング・バリデーション・レスポンス生成の総合管理
    │
    ├──[Pydantic]   受け取ったデータの型チェック・変換
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
    ...
):
    # memo_id = 3 なら /memos/3/edit にアクセスされたとき
    memo = await memo_crud.get_memo_by_id(session, memo_id)
```

`{memo_id}` の部分は URL の「穴あき」です。  
`/memos/3/edit` にアクセスすると `memo_id = 3` が関数に渡されます。  
`: int` を書くと FastAPI が自動で文字列 `"3"` を整数 `3` に変換してくれます。

### 5-3. クエリパラメータ（URL の `?` 以降）

```python
# routers/pages.py
@router.get("/")
async def index(
    request: Request,
    msg: str = "",      # ← デフォルト値があるのでクエリパラメータ
    ...
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

# ルーターを登録する（include_router）
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

> **ポイント**: `prefix="/api/memos"` を使うと、  
> 各エンドポイントに毎回 `/api/memos` を書かなくて済みます。

### 5-5. ルーティングの一覧（このアプリ）

```
main.py
 ├── pages_router（prefix なし）
 │     GET  /                   → index()        一覧画面
 │     POST /memos              → create_memo()  登録
 │     GET  /memos/{id}/edit    → edit_form()    編集画面
 │     POST /memos/{id}/edit    → update_memo()  更新
 │     POST /memos/{id}/delete  → delete_memo()  削除
 │
 └── memo_api_router（prefix="/api/memos"）
       POST   /api/memos/             → create_memo()    登録 API
       GET    /api/memos/             → get_memos_list() 全件取得 API
       GET    /api/memos/{id}         → get_memo_detail() 1件取得 API
       PUT    /api/memos/{id}         → modify_memo()    更新 API
       DELETE /api/memos/{id}         → remove_memo()    削除 API
       GET    /api/memos/{id}/histories → get_memo_histories() 履歴 API
```

---

## 6. REST API とは何か

### 6-1. REST の考え方

**REST（Representational State Transfer）** は、Web API を設計するためのルールです。  
「リソース（データ）」を「URL」で表し、「操作」を「HTTP メソッド」で表します。

```
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

Python で例えると:
- URL = 変数名
- HTTP メソッド = 操作（読む・書く・消す）

### 6-2. JSON レスポンス

REST API は **JSON** 形式でデータをやり取りします。

```python
# routers/memo.py
from schemas.memo import InsertAndUpdateMemoSchema, MemoSchema, ResponseSchema

@router.post("/", response_model=ResponseSchema, status_code=201)
async def create_memo(
    memo: InsertAndUpdateMemoSchema,   # ← JSON ボディを自動でパース
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    await memo_crud.insert_memo(session, memo, get_login_user())
    return ResponseSchema(message="メモが正常に登録されました")
    # ↑ Python オブジェクトを返すと FastAPI が自動で JSON に変換する
```

ブラウザや他のプログラムから見るとこうなります:

```
POST /api/memos/ HTTP/1.1
Content-Type: application/json

{
  "title": "買い物",
  "description": "牛乳を買う",
  "status": {"priority": "高", "due_date": null, "is_completed": false}
}

--- レスポンス ---
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
raise HTTPException(status_code=404, detail="メモが見つかりません")  # 存在しない
raise HTTPException(status_code=422)  # バリデーションエラー（FastAPI が自動で返す）
```

---

## 7. Jinja2 テンプレートと連携の仕組み

### 7-1. テンプレートとは

Jinja2 は「**穴あき HTML**」を完成させるエンジンです。

```html
<!-- templates/index.html（穴あき部分が {{ }} と {% %} で囲まれている） -->
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

# テンプレートの場所を指定（絶対パスで指定する）
templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent / "templates")
)

@router.get("/")
async def index(request: Request, msg: str = "", session=Depends(...)):
    memos = await memo_crud.get_memos(session)

    # TemplateResponse でテンプレートとデータを渡す
    return templates.TemplateResponse(
        request,           # ← 第1引数: リクエストオブジェクト（必須）
        "index.html",      # ← 第2引数: テンプレートファイル名
        {                  # ← 第3引数: テンプレートに渡すデータ（辞書）
            "memos":      memos,         # → {{ memos }} / {% for memo in memos %}
            "msg":        msg,           # → {{ msg }}
            "priorities": PRIORITY_CHOICES,  # → {% for p in priorities %}
            "login_user": get_login_user(),  # → {{ login_user }}
        }
    )
```

辞書のキーがテンプレートの変数名になります。

### 7-3. テンプレートの継承（base.html）

毎回ヘッダーやフッターを書かなくていいように、**テンプレートを継承**できます。

```html
<!-- templates/base.html: 共通レイアウト -->
<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}メモアプリ{% endblock %}</title>
  <!--      ↑ 子テンプレートが上書きできる「穴」 -->
</head>
<body>
  <header>
    <h1>📝 メモアプリ</h1>
    <span>ログイン: {{ login_user }}</span>  ← 全ページ共通
  </header>

  <main>
    {% block content %}{% endblock %}  ← 各ページの内容が入る「穴」
  </main>
</body>
</html>
```

```html
<!-- templates/index.html: base.html を継承 -->
{% extends "base.html" %}          ← 「base.html を使う」宣言

{% block title %}メモ一覧{% endblock %}   ← base の title を上書き

{% block content %}                ← base の content 穴に入る内容
  <h2>メモ一覧</h2>
  ...
{% endblock %}
```

**継承のイメージ（Python クラスと同じ）**:

```python
# Python のクラス継承と同じ発想
class BasePage:
    def title(self): return "メモアプリ"
    def content(self): return ""  # 空（穴）

class IndexPage(BasePage):
    def title(self): return "メモ一覧"   # 上書き
    def content(self): return "<h2>メモ一覧</h2>..."  # 上書き
```

### 7-4. Jinja2 の主要構文

```html
<!-- 変数の表示 -->
{{ memo.title }}
{{ memo.due_date.strftime('%Y-%m-%d') if memo.due_date else '—' }}
<!--  ↑ Python の三項演算子と同じ書き方 -->

<!-- ループ -->
{% for memo in memos %}
  <tr class="{{ 'row--completed' if memo.is_completed else '' }}">
    <td>{{ memo.title }}</td>
  </tr>
{% endfor %}

<!-- 条件分岐 -->
{% if memos %}
  <table>...</table>
{% else %}
  <p>メモがありません。</p>
{% endif %}

<!-- フィルター（| でデータを加工） -->
{{ memos | length }}   ← リストの要素数
{{ memo.title | upper }}  ← 大文字に変換
```

---

## 8. フォーム送信の完全な流れ（PRG パターン）

### 8-1. 問題：フォーム送信後のリロードで二重登録

```
ユーザーが「登録」ボタンを押す
  → POST リクエスト
  → サーバーが DB に INSERT
  → サーバーが HTML を返す（ここが問題！）
  
ユーザーがブラウザを更新（F5）
  → もう一度 POST が送られる（二重登録！）
```

### 8-2. 解決策：PRG（Post-Redirect-Get）

```
ユーザーが「登録」ボタンを押す
  → POST /memos
  → サーバーが DB に INSERT
  → サーバーが「302/303 リダイレクト」を返す ← ここが PRG
  → ブラウザが自動で GET / にアクセス
  → サーバーが HTML を返す
  
ユーザーがブラウザを更新（F5）
  → GET / が再送される（POST ではないので二重登録しない）
```

### 8-3. コードで見る PRG

```python
# routers/pages.py

# ① ブラウザが POST /memos にフォームデータを送る
@router.post("/memos")
async def create_memo(
    request: Request,
    title:   Annotated[str, Form()],      # ← Form() で HTML フォームの値を受け取る
    description: Annotated[str, Form()] = "",
    priority:    Annotated[str, Form()] = "低",
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    # ② DB に登録する
    memo_data = InsertAndUpdateMemoSchema(title=title, ...)
    await memo_crud.insert_memo(session, memo_data, get_login_user())

    # ③ 「GET / に移動してください」とブラウザに伝える（PRG の肝）
    return RedirectResponse("/?msg=created", status_code=303)
    #                        ↑ msg=created でフラッシュメッセージを渡す
    #                                        ↑ 303 が PRG の正式なステータスコード
```

```python
# ④ ブラウザが GET / にアクセス
@router.get("/")
async def index(request: Request, msg: str = ""):
    memos = await memo_crud.get_memos(session)
    return templates.TemplateResponse(request, "index.html", {
        "memos": memos,
        "msg": msg,   # ← "created" が渡される
    })
```

```html
<!-- templates/base.html -->
<!-- ⑤ msg の値によってフラッシュメッセージを表示 -->
{% if msg == "created" %}
  <div class="flash flash--success">✅ メモを登録しました。</div>
{% elif msg == "updated" %}
  <div class="flash flash--success">✅ メモを更新しました。</div>
{% elif msg == "deleted" %}
  <div class="flash flash--info">🗑️ メモを削除しました。</div>
{% endif %}
```

### 8-4. HTML フォームの仕組み

```html
<!-- templates/index.html -->
<form method="post" action="/memos">
<!--  ↑ HTTP メソッド  ↑ 送信先 URL -->

  <input type="text" name="title">
  <!--                ↑ この name が Python の引数名 title と一致する -->

  <select name="priority">
    <option value="低">低</option>
    <option value="高">高</option>
  </select>

  <button type="submit">登録</button>
  <!--     ↑ クリックするとフォームが送信される -->
</form>
```

HTML フォームが送信されると、HTTP リクエストはこうなります:

```
POST /memos HTTP/1.1
Content-Type: application/x-www-form-urlencoded

title=%E3%83%86%E3%82%B9%E3%83%88&priority=%E9%AB%98&description=
（URL エンコードされた「title=テスト&priority=高&description=」）
```

FastAPI の `Form()` がこれを自動でデコードして Python の変数に入れてくれます。

---

## 9. データベースとの非同期通信

### 9-1. ORM とは何か

**ORM（Object-Relational Mapping）** は、DB のテーブルを Python のクラスとして扱えるようにする仕組みです。

```python
# SQL を直接書く場合（ORM なし）
cursor.execute("INSERT INTO memos (title, priority) VALUES (?, ?)", (title, priority))

# ORM（SQLAlchemy）を使う場合
new_memo = Memo(title=title, priority=priority)
db.add(new_memo)
await db.commit()
```

ORM を使うと:
- SQL を知らなくても DB 操作できる
- SQL インジェクション（セキュリティの脆弱性）を防げる
- DB を SQLite から PostgreSQL に変えてもコードを変えなくていい

### 9-2. モデル定義（models/memo.py）

```python
# models/memo.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime


class Memo(Base):           # ← Base を継承すると SQLAlchemy のテーブルになる
    __tablename__ = "memos" # ← DB のテーブル名

    # カラム定義
    memo_id     = Column(Integer, primary_key=True, autoincrement=True)
    # ↑ 整数型   ↑ 主キー（一意な ID）  ↑ 自動採番
    title       = Column(String(50),  nullable=False)
    # ↑ 文字列型  ↑ 最大50文字          ↑ NULL禁止
    is_deleted  = Column(Boolean, default=False, nullable=False)
    # ↑ 真偽値型               ↑ デフォルト値

    # 関連テーブルとの関係を定義
    histories = relationship(
        "MemoHistory",           # ← 関連するクラス名
        back_populates="memo",   # ← MemoHistory 側の変数名
        cascade="all, delete-orphan"  # ← Memo 削除時に履歴も削除
    )
```

Python クラスとの対応:

```python
# 通常の Python クラス
class Memo:
    def __init__(self):
        self.memo_id = None    # 自動採番
        self.title   = ""      # 最大50文字
        self.is_deleted = False

# SQLAlchemy モデル（上の Memo と同じ意味だが DB と連動する）
class Memo(Base):
    __tablename__ = "memos"
    memo_id     = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(50), nullable=False)
    is_deleted  = Column(Boolean, default=False)
```

### 9-3. CRUD 操作（cruds/memo.py）

**新規登録：INSERT**

```python
# cruds/memo.py
async def insert_memo(db: AsyncSession, memo_data, user: str):
    try:
        # Python オブジェクトを作る
        new_memo = Memo(
            title=memo_data.title,
            priority=memo_data.status.priority,
            created_by=user,
            updated_by=user,
        )
        db.add(new_memo)         # ← INSERT の予約（まだ DB に送らない）
        await db.flush()         # ← DB に送るが、コミット（確定）はしない
        # ↑ flush() で memo_id が確定する（履歴作成に必要）

        db.add(_build_history(new_memo, "CREATE", user))  # 履歴も追加

        await db.commit()        # ← ここで初めて DB に確定保存
        await db.refresh(new_memo)  # ← DB から最新状態を読み込む
        return new_memo
    except Exception:
        await db.rollback()      # ← 失敗したら全部なかったことにする
        raise
```

**flush() と commit() の違い**:

```
db.add(new_memo)
    │
    ↓ flush() ← SQL は送るが確定しない（ロールバック可能な状態）
   DB: INSERT（仮）→ memo_id が採番される
    │
    ↓ 履歴レコードも add（memo_id が使える）
    │
    ↓ commit() ← 確定（ここから取り消し不可）
   DB: 両方のレコードが確定保存される
```

**全件取得：SELECT**

```python
async def get_memos(db: AsyncSession) -> list[Memo]:
    result = await db.execute(
        select(Memo)                         # ← SELECT * FROM memos
        .where(Memo.is_deleted == False)     # ← WHERE is_deleted = FALSE
        .order_by(Memo.memo_id)              # ← ORDER BY memo_id
    )
    return list(result.scalars().all())
    #                  ↑ 結果を Python のリストに変換
```

**論理削除**:

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

> **論理削除とは**: DB からデータを実際には消さず、  
> `is_deleted = True` というフラグを立てるだけの方法。  
> 「削除したように見せかける」技術。  
> 間違えて消した時に復元できる、削除履歴が残るなどの利点がある。

### 9-4. DB セッションの仕組み（db.py）

```python
# db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# DB エンジンを作る（アプリ起動時に1回だけ）
engine = create_async_engine(
    DATABASE_URL,      # ← "sqlite+aiosqlite:///./memo.db" など
    echo=DEBUG,        # ← True にすると SQL をログ出力
    pool_pre_ping=True # ← 接続が生きているか確認してから使う
)

# セッションファクトリを作る（工場）
async_session = async_sessionmaker(engine, class_=AsyncSession)

# セッションを1リクエストに1つ提供する関数
async def get_dbsession():
    async with async_session() as session:   # ← セッション開始
        yield session                         # ← ルーター関数に渡す
    # ← with ブロックを抜けると自動でセッションを閉じる
```

> **セッション（Session）** とは: DB との「会話の単位」です。  
> 1 回のリクエストで複数の SQL を実行しても、  
> 同じセッション内なら 1 つのトランザクションとして管理できます。

---

## 10. 依存性注入（Depends）

### 10-1. Depends とは

「この関数の引数に、あの処理の結果を自動で渡して」という仕組みです。

```python
# routers/pages.py

@router.get("/")
async def index(
    request: Request,
    msg: str = "",
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
        return templates.TemplateResponse(...)

@router.post("/memos")
async def create_memo():
    async with async_session() as session:   # また書く
        await memo_crud.insert_memo(...)
```

```python
# Depends を使う場合（繰り返しがなくてスッキリ）
@router.get("/")
async def index(session = Depends(app_db.get_dbsession)):
    memos = await memo_crud.get_memos(session)

@router.post("/memos")
async def create_memo(session = Depends(app_db.get_dbsession)):
    await memo_crud.insert_memo(...)
```

Depends は「共通処理の注入」に使います。  
テスト時にはこの `Depends` の中身を差し替えることで、  
本番 DB の代わりにテスト用 DB を使えます。

---

## 11. Pydantic によるバリデーション

### 11-1. Pydantic とは

受け取ったデータの**型チェック・変換・バリデーション**を自動でやってくれます。

```python
# schemas/memo.py
from pydantic import BaseModel, Field

class InsertAndUpdateMemoSchema(BaseModel):
    title:       str = Field(..., min_length=1, description="タイトル（必須）")
    # ↑         ↑型   ↑...は必須   ↑1文字以上
    description: str = Field("", description="詳細")
    # ↑         ↑型   ↑"" はデフォルト値（省略可）
    status:      MemoStatusSchema
```

これを使うと FastAPI は自動で:

```json
// 正常なリクエスト
{"title": "買い物", "description": "牛乳", "status": {"priority": "高"}}
// → 問題なし。InsertAndUpdateMemoSchema に変換される。

// title が空のリクエスト
{"title": "", "description": "牛乳", "status": {"priority": "高"}}
// → 422 Unprocessable Entity が自動で返される（min_length=1 に違反）

// title がないリクエスト
{"description": "牛乳", "status": {"priority": "高"}}
// → 422 Unprocessable Entity（必須フィールドなし）
```

### 11-2. スキーマの3つの種類

```python
# ① 登録・更新用（フォームや API リクエストで受け取るデータ）
class InsertAndUpdateMemoSchema(BaseModel):
    title: str = Field(..., min_length=1)  # 外から入力される
    description: str = ""

# ② レスポンス用（DB の値を含めてブラウザや API クライアントに返すデータ）
class MemoSchema(InsertAndUpdateMemoSchema):
    memo_id:    int         # DB が採番した ID
    created_at: datetime    # DB が記録した日時
    created_by: str         # 誰が作ったか

    model_config = {"from_attributes": True}  # SQLAlchemy モデルから変換可能にする

# ③ 操作結果用（成功・失敗のメッセージだけ返す）
class ResponseSchema(BaseModel):
    message: str
```

---

## 12. まとめ：リクエストからレスポンスまでの全経路

### ケース：「登録ボタンを押してからページが表示されるまで」

```
[ブラウザ]
  │ ① フォームに入力して「登録」ボタンを押す
  │
  ↓ POST /memos
  │   Content-Type: application/x-www-form-urlencoded
  │   title=買い物&priority=高&description=牛乳

[main.py]
  │ ② ミドルウェア（ログ記録）が通過する
  │   → ログ: "POST /memos → 処理中..."

[routers/pages.py: create_memo()]
  │ ③ パスが "/memos" にマッチするルーターが呼ばれる
  │ ④ Form() がフォームデータを Python の変数に変換する
  │   title = "買い物", priority = "高", description = "牛乳"
  │ ⑤ Depends(get_dbsession) が DB セッションを作って渡す

[schemas/memo.py: InsertAndUpdateMemoSchema]
  │ ⑥ Pydantic がバリデーションする
  │   title="買い物"（1文字以上 → OK）

[cruds/memo.py: insert_memo()]
  │ ⑦ Memo オブジェクトを作る（まだ DB に入っていない）
  │ ⑧ db.add(new_memo) → INSERT の予約
  │ ⑨ await db.flush() → DB に送るが未確定
  │   （この時点で memo_id が採番される）
  │ ⑩ db.add(history) → 履歴の INSERT も予約
  │ ⑪ await db.commit() → 2つのレコードを同時に確定保存
  │
  ↑ Memo オブジェクトが返ってくる

[routers/pages.py: create_memo()]
  │ ⑫ RedirectResponse("/?msg=created", status_code=303) を返す

[ブラウザ]
  │ ⑬ 303 を受け取り、自動で GET /?msg=created にアクセス

[routers/pages.py: index()]
  │ ⑭ GET / のルーターが呼ばれる
  │ ⑮ memo_crud.get_memos(session) で全件取得
  │   SELECT * FROM memos WHERE is_deleted = FALSE

[templates/index.html]
  │ ⑯ Jinja2 が memos リストを HTML に展開する
  │   {% for memo in memos %} → テーブル行を生成
  │ ⑰ msg="created" → フラッシュメッセージを表示

[ブラウザ]
  ⑱ 完成した HTML が表示される
     「✅ メモを登録しました。」が表示される
     テーブルに新しいメモが追加されている
```

---

## 付録：このアプリで使っているコード一覧

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
| `relationship(...)` | テーブル間の関係定義 | `models/memo.py` |
| `db.add()` | INSERT の予約 | `cruds/memo.py` |
| `db.flush()` | SQL を送るが未確定 | `cruds/memo.py` |
| `db.commit()` | DB に確定保存 | `cruds/memo.py` |
| `db.rollback()` | 失敗時の取り消し | `cruds/memo.py` |
| `select(Model).where(...)` | SELECT クエリの構築 | `cruds/memo.py` |
| `Field(min_length=1)` | バリデーションの定義 | `schemas/memo.py` |
| `model_config` | SQLAlchemy → Pydantic 変換設定 | `schemas/memo.py` |
| `load_dotenv()` | .env ファイルの読み込み | `config.py` |
| `NullPool` | SQLite 用のコネクションプール設定 | `db.py` |
