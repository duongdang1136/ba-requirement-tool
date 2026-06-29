from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.transcript import TranscriptSegment, Speaker

router = APIRouter()


class SegmentOut(BaseModel):
    id: str
    meeting_id: str
    start: float
    end: float
    speaker_label: str
    original_text: str
    edited_text: Optional[str]
    display_text: str
    sequence: int
    updated_at: datetime

    class Config:
        from_attributes = True


class SegmentUpdate(BaseModel):
    edited_text: Optional[str] = None
    speaker_label: Optional[str] = None


class SpeakerRename(BaseModel):
    speaker_label: str
    display_name: str


@router.get("/meeting/{meeting_id}", response_model=List[SegmentOut])
def get_transcript(meeting_id: str, db: Session = Depends(get_db)):
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.sequence)
        .all()
    )
    return segments


@router.patch("/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: str, payload: SegmentUpdate, db: Session = Depends(get_db)):
    segment = db.query(TranscriptSegment).filter(TranscriptSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(segment, k, v)
    db.commit()
    db.refresh(segment)
    return segment


@router.post("/meeting/{meeting_id}/rename-speaker")
def rename_speaker(meeting_id: str, payload: SpeakerRename, db: Session = Depends(get_db)):
    speaker = (
        db.query(Speaker)
        .filter(Speaker.meeting_id == meeting_id, Speaker.speaker_label == payload.speaker_label)
        .first()
    )
    if speaker:
        speaker.display_name = payload.display_name
    else:
        speaker = Speaker(
            meeting_id=meeting_id,
            speaker_label=payload.speaker_label,
            display_name=payload.display_name,
        )
        db.add(speaker)
    db.commit()
    return {"speaker_label": payload.speaker_label, "display_name": payload.display_name}
