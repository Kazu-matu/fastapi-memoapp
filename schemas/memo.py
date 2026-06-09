from pydantic import BaseModel, Field
from datetime import datetime


# -------------------------------------------------------
# ステータス
# -------------------------------------------------------
class MemoStatusSchema(BaseModel):
    priority:     str           = Field(...,    description="優先度（低/中/高）")
    due_date:     datetime|None = Field(None,   description="期限日")
    is_completed: bool          = Field(False,  description="完了フラグ")


# -------------------------------------------------------
# 登録・更新リクエスト
# -------------------------------------------------------
class InsertAndUpdateMemoSchema(BaseModel):
    title:       str            = Field(...,   min_length=1, description="タイトル（必須）")
    description: str            = Field("",               description="詳細")
    status:      MemoStatusSchema


# -------------------------------------------------------
# 一覧・詳細レスポンス
# -------------------------------------------------------
class MemoSchema(InsertAndUpdateMemoSchema):
    memo_id:    int             = Field(..., description="メモID")
    created_at: datetime|None  = Field(None)
    updated_at: datetime|None  = Field(None)
    created_by: str            = Field("",  description="作成担当者")
    updated_by: str|None       = Field(None, description="更新担当者")
    is_deleted: bool           = Field(False)


# -------------------------------------------------------
# 履歴レスポンス
# -------------------------------------------------------
class MemoHistorySchema(BaseModel):
    history_id:   int
    memo_id:      int
    action:       str           # CREATE / UPDATE / DELETE
    changed_at:   datetime
    changed_by:   str
    title:        str
    description:  str|None
    priority:     str
    due_date:     datetime|None
    is_completed: bool


# -------------------------------------------------------
# 汎用レスポンス
# -------------------------------------------------------
class ResponseSchema(BaseModel):
    message: str = Field(..., description="処理結果メッセージ")
