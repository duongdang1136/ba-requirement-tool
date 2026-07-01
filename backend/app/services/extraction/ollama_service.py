import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.requirement import ActionItem, Decision, MeetingSummary, OpenQuestion, RequirementCandidate
from app.models.transcript import TranscriptSegment
from app.services.extraction.prompts import (
    REQUIREMENTS_PROMPT,
    REQUIREMENTS_SYSTEM,
    REWRITE_PROMPT,
    REWRITE_SYSTEM,
    SUMMARY_PROMPT,
    SUMMARY_SYSTEM,
)
from app.services.llm import get_llm_client

ALLOWED_TYPES = {
    "functional",
    "non_functional",
    "business_rule",
    "data",
    "integration",
    "reporting",
    "permission",
    "edge_case",
}
ALLOWED_PRIORITIES = {"must", "should", "could", "wont"}


def _transcript_text(db: Session, meeting_id: str) -> str:
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.sequence, TranscriptSegment.start)
        .all()
    )
    lines = []
    for seg in segments:
        text = (seg.edited_text if seg.edited_text is not None else seg.original_text).strip()
        if text:
            lines.append(f"[{seg.id}] {seg.speaker_label} {seg.start:.1f}-{seg.end:.1f}: {text}")
    return "\n".join(lines)


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _clean_text(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _parse_due_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def generate_meeting_summary(db: Session, meeting_id: str) -> dict:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise ValueError("Meeting not found")

    transcript = _transcript_text(db, meeting_id)
    if not transcript:
        raise ValueError("No transcript segments found for this meeting")

    llm = get_llm_client()
    result = llm.generate_json(SUMMARY_SYSTEM, SUMMARY_PROMPT.format(transcript=transcript))

    db.query(MeetingSummary).filter(MeetingSummary.meeting_id == meeting_id).delete()
    db.query(Decision).filter(Decision.meeting_id == meeting_id).delete()
    db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).delete()
    db.query(OpenQuestion).filter(OpenQuestion.meeting_id == meeting_id).delete()

    summary = MeetingSummary(
        meeting_id=meeting_id,
        summary=_clean_text(result.get("summary")),
        key_points=json.dumps(_string_list(result.get("key_points"))),
        model_name=getattr(llm, "model", ""),
    )
    db.add(summary)

    for item in result.get("decisions", []) if isinstance(result.get("decisions"), list) else []:
        db.add(Decision(
            project_id=meeting.project_id,
            meeting_id=meeting_id,
            title=_clean_text(item.get("title"), "Decision"),
            description=_clean_text(item.get("description")),
            owner=_clean_text(item.get("owner")),
            source_quote=_clean_text(item.get("source_quote")),
        ))

    for item in result.get("action_items", []) if isinstance(result.get("action_items"), list) else []:
        db.add(ActionItem(
            project_id=meeting.project_id,
            meeting_id=meeting_id,
            task=_clean_text(item.get("task"), "Action item"),
            owner=_clean_text(item.get("owner")),
            due_date=_parse_due_date(item.get("due_date")),
            source_quote=_clean_text(item.get("source_quote")),
        ))

    for item in result.get("open_questions", []) if isinstance(result.get("open_questions"), list) else []:
        db.add(OpenQuestion(
            project_id=meeting.project_id,
            meeting_id=meeting_id,
            question=_clean_text(item.get("question"), "Open question"),
            owner=_clean_text(item.get("owner")),
            source_quote=_clean_text(item.get("source_quote")),
        ))

    db.commit()
    return {"summary": summary.summary}


def extract_requirement_candidates(db: Session, meeting_id: str) -> dict:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise ValueError("Meeting not found")

    transcript = _transcript_text(db, meeting_id)
    if not transcript:
        raise ValueError("No transcript segments found for this meeting")

    llm = get_llm_client()
    result = llm.generate_json(REQUIREMENTS_SYSTEM, REQUIREMENTS_PROMPT.format(transcript=transcript))

    db.query(RequirementCandidate).filter(
        RequirementCandidate.meeting_id == meeting_id,
        RequirementCandidate.review_state == "pending",
    ).delete()

    created = 0
    candidates = result.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []

    for item in candidates:
        req_type = _clean_text(item.get("type"), "functional")
        priority = _clean_text(item.get("priority"), "should")
        if req_type not in ALLOWED_TYPES:
            req_type = "functional"
        if priority not in ALLOWED_PRIORITIES:
            priority = "should"

        title = _clean_text(item.get("title"))
        description = _clean_text(item.get("description"))
        if not title and not description:
            continue

        db.add(RequirementCandidate(
            meeting_id=meeting_id,
            title=title or description[:120],
            description=description,
            type=req_type,
            priority=priority,
            source_quote=_clean_text(item.get("source_quote")),
            source_segment_ids=json.dumps(_string_list(item.get("source_segment_ids"))),
        ))
        created += 1

    db.commit()
    return {"created": created}


def suggest_segment_rewrite(db: Session, segment_id: str) -> dict:
    segment = db.query(TranscriptSegment).filter(TranscriptSegment.id == segment_id).first()
    if not segment:
        raise ValueError("Segment not found")

    target = (segment.edited_text if segment.edited_text is not None else segment.original_text).strip()
    if not target:
        raise ValueError("Segment text is empty")

    previous_segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == segment.meeting_id, TranscriptSegment.sequence < segment.sequence)
        .order_by(TranscriptSegment.sequence.desc())
        .limit(2)
        .all()
    )
    next_segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == segment.meeting_id, TranscriptSegment.sequence > segment.sequence)
        .order_by(TranscriptSegment.sequence)
        .limit(2)
        .all()
    )

    def join_context(items: list[TranscriptSegment]) -> str:
        ordered = sorted(items, key=lambda item: item.sequence)
        return "\n".join(
            (item.edited_text if item.edited_text is not None else item.original_text).strip()
            for item in ordered
            if (item.edited_text if item.edited_text is not None else item.original_text).strip()
        )

    llm = get_llm_client()
    result = llm.generate_json(
        REWRITE_SYSTEM,
        REWRITE_PROMPT.format(
            previous_context=join_context(previous_segments),
            target_text=target,
            next_context=join_context(next_segments),
        ),
    )
    suggestion = _clean_text(result.get("suggestion"))
    if not suggestion:
        raise ValueError("Ollama did not return a rewrite suggestion")
    return {"segment_id": segment_id, "original": target, "suggestion": suggestion}
