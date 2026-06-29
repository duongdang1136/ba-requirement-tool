from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment, Speaker

router = APIRouter()


class SegmentOut(BaseModel):
    id: str
    meeting_id: str
    start: float
    end: float
    speaker_label: str
    original_text: str
    refined_text: Optional[str]
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


class SpeakerOut(BaseModel):
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


@router.get("/meeting/{meeting_id}/speakers", response_model=List[SpeakerOut])
def get_speakers(meeting_id: str, db: Session = Depends(get_db)):
    labels = [
        row[0]
        for row in (
            db.query(TranscriptSegment.speaker_label)
            .filter(TranscriptSegment.meeting_id == meeting_id)
            .distinct()
            .order_by(TranscriptSegment.speaker_label)
            .all()
        )
    ]
    speaker_names = {
        speaker.speaker_label: speaker.display_name
        for speaker in db.query(Speaker).filter(Speaker.meeting_id == meeting_id).all()
    }
    return [
        SpeakerOut(speaker_label=label, display_name=speaker_names.get(label, ""))
        for label in labels
    ]


@router.delete("/meeting/{meeting_id}")
def clear_transcript(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    deleted_segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .delete(synchronize_session=False)
    )
    deleted_speakers = (
        db.query(Speaker)
        .filter(Speaker.meeting_id == meeting_id)
        .delete(synchronize_session=False)
    )
    db.commit()

    return {
        "meeting_id": meeting_id,
        "deleted_segments": deleted_segments,
        "deleted_speakers": deleted_speakers,
    }


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
