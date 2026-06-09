import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
from datetime import datetime
from pydantic import ValidationError
from schemas.memo import (
    MemoStatusSchema,
    InsertAndUpdateMemoSchema,
    MemoSchema,
    ResponseSchema,
)

# UT-S-01: 全フィールドが正しい値
def test_insert_schema_valid():
    schema = InsertAndUpdateMemoSchema(
        title="テストタイトル",
        description="詳細内容",
        status=MemoStatusSchema(priority="高", due_date=datetime(2025, 12, 31), is_completed=False),
    )
    assert schema.title == "テストタイトル"
    assert schema.status.priority == "高"

# UT-S-02: title が空文字
def test_insert_schema_empty_title():
    with pytest.raises(ValidationError):
        InsertAndUpdateMemoSchema(
            title="",
            description="詳細",
            status=MemoStatusSchema(priority="低"),
        )

# UT-S-03: title が未指定
def test_insert_schema_missing_title():
    with pytest.raises(ValidationError):
        InsertAndUpdateMemoSchema(
            description="詳細",
            status=MemoStatusSchema(priority="低"),
        )

# UT-S-04: is_completed のデフォルト値は False
def test_status_schema_is_completed_default():
    status = MemoStatusSchema(priority="中")
    assert status.is_completed is False

# UT-S-05: due_date が None でもバリデーション通過
def test_status_schema_due_date_none():
    status = MemoStatusSchema(priority="低", due_date=None)
    assert status.due_date is None

# UT-S-06: due_date に日付文字列を渡すと datetime 型に変換される
def test_status_schema_due_date_string():
    status = MemoStatusSchema(priority="低", due_date="2025-12-31T00:00:00")
    assert isinstance(status.due_date, datetime)

# UT-S-07: MemoSchema に memo_id あり
def test_memo_schema_valid():
    schema = MemoSchema(
        memo_id=1,
        title="タイトル",
        description="詳細",
        status=MemoStatusSchema(priority="高"),
    )
    assert schema.memo_id == 1

# UT-S-08: ResponseSchema の message
def test_response_schema_valid():
    schema = ResponseSchema(message="メモが正常に登録されました")
    assert schema.message == "メモが正常に登録されました"
