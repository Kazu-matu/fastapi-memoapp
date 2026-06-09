"""
Jinja2 ページルーター
PRG (Post-Redirect-Get) パターンを採用。
フォーム送信 → 処理 → リダイレクト → GET でページ表示。
"""
from pathlib import Path
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Annotated

import cruds.memo as memo_crud
import db as app_db
from config import get_login_user, PRIORITY_CHOICES
from schemas.memo import InsertAndUpdateMemoSchema, MemoStatusSchema

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


# -------------------------------------------------------
# トップページ（一覧 + 新規作成フォーム）
# -------------------------------------------------------
@router.get("/")
async def index(
    request: Request,
    msg: str = "",
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    memos = await memo_crud.get_memos(session)
    return templates.TemplateResponse(request, "index.html", {
        "memos":      memos,
        "msg":        msg,
        "priorities": PRIORITY_CHOICES,
        "login_user": get_login_user(),
    })


# -------------------------------------------------------
# 新規登録（POST → Redirect）
# -------------------------------------------------------
@router.post("/memos")
async def create_memo(
    request:      Request,
    title:        Annotated[str,  Form()],
    description:  Annotated[str,  Form()] = "",
    priority:     Annotated[str,  Form()] = "低",
    due_date:     Annotated[str,  Form()] = "",
    is_completed: Annotated[bool, Form()] = False,
    session:      AsyncSession = Depends(app_db.get_dbsession),
):
    due = _parse_date(due_date)
    memo_data = InsertAndUpdateMemoSchema(
        title=title,
        description=description,
        status=MemoStatusSchema(
            priority=priority,
            due_date=due,
            is_completed=is_completed,
        ),
    )
    await memo_crud.insert_memo(session, memo_data, get_login_user())
    return RedirectResponse("/?msg=created", status_code=303)


# -------------------------------------------------------
# 編集フォーム表示
# -------------------------------------------------------
@router.get("/memos/{memo_id}/edit")
async def edit_form(
    request: Request,
    memo_id: int,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    memo = await memo_crud.get_memo_by_id(session, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="メモが見つかりません")
    histories = await memo_crud.get_histories_by_memo_id(session, memo_id)
    return templates.TemplateResponse(request, "edit.html", {
        "memo":       memo,
        "histories":  histories,
        "priorities": PRIORITY_CHOICES,
        "login_user": get_login_user(),
    })


# -------------------------------------------------------
# 更新（POST → Redirect）
# -------------------------------------------------------
@router.post("/memos/{memo_id}/edit")
async def update_memo(
    request:      Request,
    memo_id:      int,
    title:        Annotated[str,  Form()],
    description:  Annotated[str,  Form()] = "",
    priority:     Annotated[str,  Form()] = "低",
    due_date:     Annotated[str,  Form()] = "",
    is_completed: Annotated[bool, Form()] = False,
    session:      AsyncSession = Depends(app_db.get_dbsession),
):
    due = _parse_date(due_date)
    memo_data = InsertAndUpdateMemoSchema(
        title=title,
        description=description,
        status=MemoStatusSchema(
            priority=priority,
            due_date=due,
            is_completed=is_completed,
        ),
    )
    updated = await memo_crud.update_memo(session, memo_id, memo_data, get_login_user())
    if not updated:
        raise HTTPException(status_code=404, detail="更新対象が見つかりません")
    return RedirectResponse("/?msg=updated", status_code=303)


# -------------------------------------------------------
# 論理削除（POST → Redirect）
# -------------------------------------------------------
@router.post("/memos/{memo_id}/delete")
async def delete_memo(
    request: Request,
    memo_id: int,
    session: AsyncSession = Depends(app_db.get_dbsession),
):
    result = await memo_crud.delete_memo(session, memo_id, get_login_user())
    if not result:
        raise HTTPException(status_code=404, detail="削除対象が見つかりません")
    return RedirectResponse("/?msg=deleted", status_code=303)


# -------------------------------------------------------
# ヘルパー
# -------------------------------------------------------
def _parse_date(value: str) -> datetime | None:
    """フォームの date 文字列 (YYYY-MM-DD) を datetime に変換。空の場合は None。"""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
