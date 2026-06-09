from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime


class Memo(Base):
    """メモテーブル"""
    __tablename__ = "memos"

    memo_id      = Column(Integer, primary_key=True, autoincrement=True)
    title        = Column(String(50),  nullable=False)
    description  = Column(String(255), nullable=True)
    created_at   = Column(DateTime, default=datetime.now, nullable=False)
    updated_at   = Column(DateTime, nullable=True)
    # ステータス
    priority     = Column(String(10), nullable=False)
    due_date     = Column(DateTime,   nullable=True)
    is_completed = Column(Boolean,    default=False, nullable=False)
    # 論理削除
    is_deleted   = Column(Boolean,    default=False, nullable=False)
    deleted_at   = Column(DateTime,   nullable=True)
    # 担当者（Windowsログインユーザー）
    created_by   = Column(String(100), nullable=False)
    updated_by   = Column(String(100), nullable=True)

    # リレーション
    histories = relationship(
        "MemoHistory", back_populates="memo",
        lazy="select", cascade="all, delete-orphan"
    )


class MemoHistory(Base):
    """
    メモ変更履歴テーブル（監査ログ）
    メモの作成・更新・削除のたびにスナップショットを記録する。
    """
    __tablename__ = "memo_histories"

    history_id   = Column(Integer, primary_key=True, autoincrement=True)
    memo_id      = Column(Integer, ForeignKey("memos.memo_id"), nullable=False)
    action       = Column(String(20), nullable=False)   # CREATE / UPDATE / DELETE
    changed_at   = Column(DateTime, default=datetime.now, nullable=False)
    changed_by   = Column(String(100), nullable=False)
    # 変更前スナップショット
    title        = Column(String(50),  nullable=False)
    description  = Column(String(255), nullable=True)
    priority     = Column(String(10),  nullable=False)
    due_date     = Column(DateTime,    nullable=True)
    is_completed = Column(Boolean,     nullable=False)

    memo = relationship("Memo", back_populates="histories")
