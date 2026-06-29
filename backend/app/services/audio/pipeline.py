"""
Audio processing pipeline:
normalize → ASR (sherpa-onnx Whisper small, Vietnamese) → store segments
"""
import subprocess
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.meeting import ProcessingJob, MediaFile
from app.models.transcript import TranscriptSegment


def run_pipeline(meeting_id: str, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        media = (
            db.query(MediaFile)
            .filter(MediaFile.meeting_id == meeting_id)
            .order_by(MediaFile.created_at.desc())
            .first()
        )

        if not media:
            job.status = "failed"
            job.error = "No media file found"
            db.commit()
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.step = "normalize"
        job.progress = 10
        db.commit()

        # Step 1: Normalize audio → 16kHz mono WAV
        normalized_path = _normalize_audio(media.stored_path, meeting_id)
        if not normalized_path:
            job.status = "failed"
            job.error = "ffmpeg normalization failed"
            db.commit()
            return

        media.normalized_path = str(normalized_path)
        job.progress = 35
        job.step = "asr"
        db.commit()

        # Step 2: Run Whisper ASR
        segments = _run_whisper_asr(normalized_path)
        if segments is None:
            job.status = "failed"
            job.error = "ASR failed — check model path"
            db.commit()
            return

        job.progress = 85
        job.step = "merge"
        db.commit()

        # Step 3: Store transcript segments (clear old ones first)
        db.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == meeting_id).delete()

        for i, seg in enumerate(segments):
            text = seg["text"].strip()
            if not text:
                continue
            db.add(TranscriptSegment(
                meeting_id=meeting_id,
                start=seg["start"],
                end=seg["end"],
                speaker_label="SPEAKER_00",
                original_text=text,
                sequence=i,
            ))

        job.status = "completed"
        job.progress = 100
        job.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def _normalize_audio(input_path: str, meeting_id: str) -> Path | None:
    """Convert any audio/video to 16kHz mono WAV using ffmpeg."""
    out_dir = Path(settings.upload_dir) / meeting_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "normalized.wav"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"[ffmpeg] {result.stderr[-300:]}")
            return None
        return out_path
    except FileNotFoundError:
        print("[ffmpeg] Not found. Install: sudo apt install ffmpeg")
        return None
    except Exception as e:
        print(f"[ffmpeg] {e}")
        return None


def _run_whisper_asr(audio_path: Path) -> list | None:
    """
    Run sherpa-onnx Whisper small ASR — supports Vietnamese.
    Returns list of {start, end, text} dicts.
    """
    try:
        import sherpa_onnx
        import soundfile as sf

        model_dir = Path(settings.asr_model_dir)
        encoder = model_dir / "small-encoder.int8.onnx"
        decoder = model_dir / "small-decoder.int8.onnx"
        tokens  = model_dir / "small-tokens.txt"

        if not encoder.exists():
            print(f"[ASR] Whisper model not found at {model_dir}")
            return _mock_asr()

        recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(encoder),
            decoder=str(decoder),
            tokens=str(tokens),
            num_threads=4,
            decoding_method="greedy_search",
            language=settings.asr_language,  # "vi"
            task="transcribe",
        )

        # Load audio
        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)
        duration = len(samples) / sample_rate

        # Whisper works best with 30s chunks
        chunk_sec = 28
        chunk_size = chunk_sec * sample_rate
        overlap_sec = 1
        overlap = overlap_sec * sample_rate

        segments = []
        pos = 0
        seq = 0

        while pos < len(samples):
            chunk = samples[pos: pos + chunk_size]
            start_sec = round(pos / sample_rate, 2)
            end_sec   = round(min((pos + len(chunk)) / sample_rate, duration), 2)

            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, chunk)
            recognizer.decode_stream(stream)
            text = stream.result.text.strip()

            if text:
                segments.append({"start": start_sec, "end": end_sec, "text": text})
                seq += 1

            pos += chunk_size - overlap
            if pos >= len(samples):
                break

        return segments if segments else [{"start": 0.0, "end": duration, "text": "(Không nhận dạng được âm thanh)"}]

    except ImportError:
        print("[ASR] sherpa-onnx not installed")
        return _mock_asr()
    except Exception as e:
        print(f"[ASR error] {e}")
        return None


def _mock_asr() -> list:
    return [
        {"start": 0.0, "end": 5.0, "text": "[Chưa cài model ASR — đây là transcript mẫu]"},
        {"start": 5.1, "end": 10.0, "text": "[Cài sherpa-onnx và download model Whisper small để nhận transcript thật]"},
    ]
