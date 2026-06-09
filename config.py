"""
アプリケーション設定
.env ファイルまたは環境変数で上書き可能。未設定時はデフォルト値を使用。

DB 切り替え方法:
  開発: DATABASE_URL=sqlite+aiosqlite:///./memodb.sqlite   (デフォルト)
  本番: DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
"""
import os
import getpass
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込む（存在しない場合は無視）
load_dotenv(Path(__file__).parent / ".env")

# アプリ基本設定
APP_NAME: str = os.getenv("APP_NAME", "メモアプリ")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# データベース設定
_default_db = f"sqlite+aiosqlite:///{Path(__file__).parent / 'memodb.sqlite'}"
DATABASE_URL: str = os.getenv("DATABASE_URL", _default_db)

# 優先度の選択肢（アプリ全体で共有）
PRIORITY_CHOICES: list[str] = ["低", "中", "高"]


def get_login_user() -> str:
    """Windowsのログインユーザー名を返す。取得不可の場合は 'system' を返す。"""
    try:
        return getpass.getuser()
    except Exception:
        return "system"
