import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"), nullable=False)
    start: Mapped[float] = mapped_column(Float, nullable=False)
    end: Mapped[float] = mapped_column(Float, nullable=False)
    speaker_label: Mapped[str] = mapped_column(String(50), default="SPEAKER_00")
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def display_text(self) -> str:
        return self.edited_text if self.edited_text is not None else self.original_text


class Speaker(Base):
    __tablename__ = "speakers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id"), nullable=False)
    speaker_label: Mapped[str] = mapped_column(String(50), nullable=False)  # SPEAKER_00
    display_name: Mapped[str] = mapped_column(String(255), default="")       # Client / BA / PM
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
