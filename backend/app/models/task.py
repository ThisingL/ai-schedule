from datetime import date, time, datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, Boolean, Date, Time, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(2), default="P2")
    status: Mapped[str] = mapped_column(String(20), default="todo")
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_priority_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    children: Mapped[list["Task"]] = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Optional["Task"]] = relationship("Task", back_populates="children", remote_side=[id])
