"""
メモ CRUD 処理
- 全操作はトランザクション内で memo_histories へのスナップショット記録を伴う
- 削除は論理削除（is_deleted=True）
- ユーザー名は呼び出し元から渡す
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import schemas.memo as memo_schema
import models.memo as memo_model


# -------------------------------------------------------
# 内部ヘルパー
# -------------------------------------------------------
def _build_history(
    memo: memo_model.Memo,
    action: str,
    user: str,
) -> memo_model.MemoHistory:
    return memo_model.MemoHistory(
        memo_id=memo.memo_id,
        action=action,
        changed_by=user,
        title=memo.title,
        description=memo.description,
        priority=memo.priority,
        due_date=memo.due_date,
        is_completed=memo.is_completed,
    )


async def _get_active_memo(
    db: AsyncSession, memo_id: int
) -> memo_model.Memo | None:
    """論理削除されていない特定 ID のメモを1件取得する"""
    result = await db.execute(
        select(memo_model.Memo).where(
            memo_model.Memo.memo_id == memo_id,
            memo_model.Memo.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().first()


# -------------------------------------------------------
# 新規登録
# -------------------------------------------------------
async def insert_memo(
    db: AsyncSession,
    memo_data: memo_schema.InsertAndUpdateMemoSchema,
    user: str,
) -> memo_model.Memo:
    try:
        new_memo = memo_model.Memo(
            title=memo_data.title,
            description=memo_data.description,
            priority=memo_data.status.priority,
            due_date=memo_data.status.due_date,
            is_completed=memo_data.status.is_completed,
            created_by=user,
            updated_by=user,
        )
        db.add(new_memo)
        await db.flush()  # memo_id を確定させる（コミットはしない）

        db.add(_build_history(new_memo, "CREATE", user))

        await db.commit()
        await db.refresh(new_memo)
        return new_memo
    except Exception:
        await db.rollback()
        raise


# -------------------------------------------------------
# 全件取得（論理削除済みを除外）
# -------------------------------------------------------
async def get_memos(db: AsyncSession) -> list[memo_model.Memo]:
    result = await db.execute(
        select(memo_model.Memo)
        .where(memo_model.Memo.is_deleted == False)  # noqa: E712
        .order_by(memo_model.Memo.memo_id)
    )
    return list(result.scalars().all())


# -------------------------------------------------------
# 1件取得（論理削除済みを除外）
# -------------------------------------------------------
async def get_memo_by_id(
    db: AsyncSession, memo_id: int
) -> memo_model.Memo | None:
    return await _get_active_memo(db, memo_id)


# -------------------------------------------------------
# 更新
# -------------------------------------------------------
async def update_memo(
    db: AsyncSession,
    memo_id: int,
    target_data: memo_schema.InsertAndUpdateMemoSchema,
    user: str,
) -> memo_model.Memo | None:
    memo = await _get_active_memo(db, memo_id)
    if not memo:
        return None
    try:
        memo.title        = target_data.title
        memo.description  = target_data.description
        memo.priority     = target_data.status.priority
        memo.due_date     = target_data.status.due_date
        memo.is_completed = target_data.status.is_completed
        memo.updated_at   = datetime.now()
        memo.updated_by   = user

        db.add(_build_history(memo, "UPDATE", user))

        await db.commit()
        await db.refresh(memo)
        return memo
    except Exception:
        await db.rollback()
        raise


# -------------------------------------------------------
# 論理削除
# -------------------------------------------------------
async def delete_memo(
    db: AsyncSession, memo_id: int, user: str
) -> memo_model.Memo | None:
    memo = await _get_active_memo(db, memo_id)
    if not memo:
        return None
    try:
        memo.is_deleted = True
        memo.deleted_at = datetime.now()
        memo.updated_by = user

        db.add(_build_history(memo, "DELETE", user))

        await db.commit()
        await db.refresh(memo)
        return memo
    except Exception:
        await db.rollback()
        raise


# -------------------------------------------------------
# 履歴取得
# -------------------------------------------------------
async def get_histories_by_memo_id(
    db: AsyncSession, memo_id: int
) -> list[memo_model.MemoHistory]:
    result = await db.execute(
        select(memo_model.MemoHistory)
        .where(memo_model.MemoHistory.memo_id == memo_id)
        .order_by(memo_model.MemoHistory.changed_at.desc())
    )
    return list(result.scalars().all())
