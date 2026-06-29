import httpx


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def refine_vietnamese_transcript(api_key: str, model: str, text: str, speaker: str = "") -> str:
    prompt = f"""
Bạn là trợ lý cho Business Analyst.

Nhiệm vụ: viết lại transcript tiếng Việt bên dưới cho rõ nghĩa, dễ đọc, đúng ngữ cảnh meeting requirement.

Quy tắc bắt buộc:
- Không thêm thông tin mới.
- Không bỏ yêu cầu, ràng buộc, tên riêng, số tiền, ngày tháng, quyết định.
- Không biến câu nói thành requirement formal nếu người nói chưa nói rõ.
- Sửa lỗi nghe sai rõ ràng nếu ngữ cảnh đủ chắc.
- Giữ nguyên ý định của người nói.
- Nếu không chắc, giữ gần với câu gốc.
- Chỉ trả về câu đã viết lại, không giải thích.

Speaker: {speaker or "Unknown"}

Transcript gốc:
{text}
""".strip()

    response = httpx.post(
        GEMINI_ENDPOINT.format(model=model),
        params={"key": api_key},
        json={
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 512,
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    refined = "".join(part.get("text", "") for part in parts).strip()
    if not refined:
        raise ValueError("Gemini returned empty text")
    return refined
