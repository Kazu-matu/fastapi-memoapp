"""
REST API ルーター /api/memos
外部クライアント・テスト向けの JSON API エンドポイント。
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.memo import (
    InsertAndUpdateMemoSchema, MemoSchema, MemoHistorySchema, ResponseSchema
)
import cruds.memo as memo_crud
import db as app_db
from config import get_login_user

router = APIRouter(tags=["Memos API"], prefix="/api/memos")


# -------------------------------------------------------
# メモ新規登録
# -------------------------------------------------------
@router.post("/", response_model=ResponseSchema, status_code=201)
async def create_memo(
    memo: InsertAndUpdateMemoSchema,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    await memo_crud.insert_memo(session, memo, get_login_user())
    return ResponseSchema(message="メモが正常に登録されました")


# -------------------------------------------------------
# メモ全件取得
# -------------------------------------------------------
@router.get("/", response_model=list[MemoSchema])
async def get_memos_list(session: AsyncSession = Depends(app_db.get_dbsession)):
    memos = await memo_crud.get_memos(session)
    return [_to_schema(m) for m in memos]


# -------------------------------------------------------
# メモ1件取得
# -------------------------------------------------------
@router.get("/{memo_id}", response_model=MemoSchema)
async def get_memo_detail(
    memo_id: int,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    memo = await memo_crud.get_memo_by_id(session, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="メモが見つかりません")
    return _to_schema(memo)


# -------------------------------------------------------
# メモ更新
# -------------------------------------------------------
@router.put("/{memo_id}", response_model=ResponseSchema)
async def modify_memo(
    memo_id: int,
    memo: InsertAndUpdateMemoSchema,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    updated = await memo_crud.update_memo(session, memo_id, memo, get_login_user())
    if not updated:
        raise HTTPException(status_code=404, detail="更新対象が見つかりません")
    return ResponseSchema(message="メモが正常に更新されました")


# -------------------------------------------------------
# 論理削除
# -------------------------------------------------------
@router.delete("/{memo_id}", response_model=ResponseSchema)
async def remove_memo(
    memo_id: int,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    result = await memo_crud.delete_memo(session, memo_id, get_login_user())
    if not result:
        raise HTTPException(status_code=404, detail="削除対象が見つかりません")
    return ResponseSchema(message="メモが正常に削除されました")


# -------------------------------------------------------
# 履歴取得
# -------------------------------------------------------
@router.get("/{memo_id}/histories", response_model=list[MemoHistorySchema])
async def get_memo_histories(
    memo_id: int,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    return await memo_crud.get_histories_by_memo_id(session, memo_id)


# -------------------------------------------------------
# 内部変換ヘルパー
# -------------------------------------------------------
def _to_schema(memo) -> MemoSchema:
    from schemas.memo import MemoStatusSchema
    return MemoSchema(
        memo_id=memo.memo_id,
        title=memo.title,
        description=memo.description or "",
        status=MemoStatusSchema(
            priority=memo.priority,
            due_date=memo.due_date,
            is_completed=memo.is_completed,
        ),
        created_at=memo.created_at,
        updated_at=memo.updated_at,
        created_by=memo.created_by,
        updated_by=memo.updated_by,
        is_deleted=memo.is_deleted,
    )
