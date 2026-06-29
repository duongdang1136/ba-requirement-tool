from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.settings import AISettings
from app.models.transcript import TranscriptSegment
from app.services.ai.gemini import refine_vietnamese_transcript

router = APIRouter()


class AISettingsOut(BaseModel):
    provider: str
    model: str
    has_api_key: bool


class AISettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    model: str = "gemini-2.0-flash"


class RefineResult(BaseModel):
    refined_count: int


def _get_or_create_settings(db: Session) -> AISettings:
    settings = db.query(AISettings).filter(AISettings.provider == "gemini").first()
    if settings:
        return settings

    settings = AISettings(provider="gemini", model="gemini-2.0-flash", api_key="")
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("", response_model=AISettingsOut)
def get_ai_settings(db: Session = Depends(get_db)):
    settings = _get_or_create_settings(db)
    return AISettingsOut(
        provider=settings.provider,
        model=settings.model,
        has_api_key=bool(settings.api_key.strip()),
    )


@router.put("", response_model=AISettingsOut)
def update_ai_settings(payload: AISettingsUpdate, db: Session = Depends(get_db)):
    settings = _get_or_create_settings(db)
    if payload.api_key is not None:
        settings.api_key = payload.api_key.strip()
    settings.model = payload.model.strip() or "gemini-2.0-flash"
    db.commit()
    db.refresh(settings)
    return AISettingsOut(
        provider=settings.provider,
        model=settings.model,
        has_api_key=bool(settings.api_key.strip()),
    )


@router.post("/transcript-segments/{segment_id}/refine")
def refine_segment(segment_id: str, db: Session = Depends(get_db)):
    settings = _get_or_create_settings(db)
    if not settings.api_key.strip():
        raise HTTPException(status_code=400, detail="Gemini API key is not configured")

    segment = db.query(TranscriptSegment).filter(TranscriptSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    try:
        segment.refined_text = refine_vietnamese_transcript(
            api_key=settings.api_key,
            model=settings.model,
            text=segment.original_text,
            speaker=segment.speaker_label,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini refine failed: {e}") from e

    db.commit()
    db.refresh(segment)
    return segment


@router.post("/meetings/{meeting_id}/refine-transcript", response_model=RefineResult)
def refine_meeting_transcript(meeting_id: str, db: Session = Depends(get_db)):
    settings = _get_or_create_settings(db)
    if not settings.api_key.strip():
        raise HTTPException(status_code=400, detail="Gemini API key is not configured")

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.sequence)
        .all()
    )
    if not segments:
        return RefineResult(refined_count=0)

    refined_count = 0
    for segment in segments:
        if not segment.original_text.strip():
            continue
        try:
            segment.refined_text = refine_vietnamese_transcript(
                api_key=settings.api_key,
                model=settings.model,
                text=segment.original_text,
                speaker=segment.speaker_label,
            )
            refined_count += 1
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=502, detail=f"Gemini refine failed: {e}") from e

    db.commit()
    return RefineResult(refined_count=refined_count)
