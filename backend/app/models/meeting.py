import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, DateTime, Date, Text, BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    meeting_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    participants: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500))
    stored_path: Mapped[str] = mapped_column(String(1000))
    normalized_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"), nullable=False)
    step: Mapped[str] = mapped_column(String(100))  # normalize | vad | asr | diarize | merge | extract
    status: Mapped[str] = mapped_column(String(50), default="queued")  # queued | running | completed | failed
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
