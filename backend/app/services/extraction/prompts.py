SUMMARY_SYSTEM = """You are a senior Business Analyst. Extract meeting artifacts from a transcript.
Return only JSON. Do not include markdown."""

SUMMARY_PROMPT = """Analyze this transcript and return JSON with this shape:
{
  "summary": "short meeting summary",
  "key_points": ["important point"],
  "decisions": [{"title": "decision title", "description": "details", "owner": "", "source_quote": "short transcript quote"}],
  "action_items": [{"task": "action task", "owner": "", "due_date": null, "source_quote": "short transcript quote"}],
  "open_questions": [{"question": "question text", "owner": "", "source_quote": "short transcript quote"}]
}

Rules:
- Keep source_quote verbatim and short.
- If no items exist, return an empty array.
- Use null for unknown due_date.

Transcript:
{transcript}
"""

REQUIREMENTS_SYSTEM = """You are a senior Business Analyst. Extract requirement candidates from a transcript.
Return only JSON. Do not include markdown."""

REQUIREMENTS_PROMPT = """Extract requirement candidates from this transcript and return JSON with this shape:
{
  "candidates": [
    {
      "title": "requirement title",
      "description": "clear requirement description",
      "type": "functional",
      "priority": "should",
      "source_quote": "short verbatim transcript quote",
      "source_segment_ids": ["segment-id"]
    }
  ]
}

Allowed type values: functional, non_functional, business_rule, data, integration, reporting, permission, edge_case.
Allowed priority values: must, should, could, wont.
Rules:
- Only extract requirements supported by transcript evidence.
- Keep source_quote verbatim and short.
- Use source_segment_ids from the transcript lines.
- If no requirements exist, return an empty candidates array.

Transcript:
{transcript}
"""

REWRITE_SYSTEM = """You are a careful transcript editor. Improve readability without changing meaning.
Return only JSON. Do not include markdown."""

REWRITE_PROMPT = """Suggest a cleaner rewrite for the target transcript segment.
Return JSON with this shape:
{
  "suggestion": "rewritten segment text"
}

Rules:
- Preserve the original meaning and facts.
- Do not add details that are not present.
- Keep the same language as the target.

Previous context:
{previous_context}

Target:
{target_text}

Next context:
{next_context}
"""
