"""
DB 初期化スクリプト
既存テーブルを DROP してから CREATE し直す。
本番環境では絶対に実行しないこと。
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from models.memo import Base   # Memo + MemoHistory 両モデルを含む
from config import DATABASE_URL


engine = create_async_engine(DATABASE_URL, echo=True)


async def init_db() -> None:
    print("=== DB 初期化開始 ===")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print(">>> 既存テーブルを削除しました")
        await conn.run_sync(Base.metadata.create_all)
        print(">>> テーブルを作成しました（memos, memo_histories）")
    print("=== DB 初期化完了 ===")


if __name__ == "__main__":
    asyncio.run(init_db())
