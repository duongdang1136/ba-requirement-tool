from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.transcript import TranscriptSegment
from app.models.requirement import Requirement
from app.models.meeting import Meeting

router = APIRouter()


def _format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


@router.get("/meeting/{meeting_id}/transcript/markdown")
def export_transcript_markdown(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.sequence)
        .all()
    )

    lines = [f"# Meeting Transcript — {meeting.title}\n"]
    if meeting.meeting_date:
        lines.append(f"**Date:** {meeting.meeting_date}\n")
    lines.append("")

    for seg in segments:
        time_str = f"{_format_time(seg.start)} - {_format_time(seg.end)}"
        text = seg.edited_text if seg.edited_text else seg.original_text
        lines.append(f"**{time_str}** `{seg.speaker_label}`")
        lines.append(f"{text}\n")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="transcript-{meeting_id}.md"'},
    )


@router.get("/meeting/{meeting_id}/transcript/txt")
def export_transcript_txt(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.sequence)
        .all()
    )

    lines = [f"Meeting Transcript — {meeting.title}", "=" * 50, ""]
    for seg in segments:
        time_str = f"{_format_time(seg.start)} - {_format_time(seg.end)}"
        text = seg.edited_text if seg.edited_text else seg.original_text
        lines.append(f"[{time_str}] {seg.speaker_label}")
        lines.append(text)
        lines.append("")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="transcript-{meeting_id}.txt"'},
    )


@router.get("/project/{project_id}/requirements/markdown")
def export_requirements_markdown(project_id: str, db: Session = Depends(get_db)):
    reqs = (
        db.query(Requirement)
        .filter(Requirement.project_id == project_id, Requirement.status == "approved")
        .order_by(Requirement.type, Requirement.created_at)
        .all()
    )

    lines = ["# Approved Requirements\n"]
    current_type = None
    for i, req in enumerate(reqs, 1):
        if req.type != current_type:
            current_type = req.type
            lines.append(f"\n## {current_type.replace('_', ' ').title()}\n")
        lines.append(f"### REQ-{i:03d} — {req.title}")
        lines.append(f"**Priority:** {req.priority} | **Status:** {req.status}")
        if req.actor:
            lines.append(f"**Actor:** {req.actor}")
        lines.append(f"\n{req.description}")
        if req.acceptance_criteria:
            lines.append(f"\n**Acceptance Criteria:**\n{req.acceptance_criteria}")
        if req.source_quote:
            lines.append(f"\n> *Source:* {req.source_quote}")
        lines.append("")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="requirements-{project_id}.md"'},
    )
