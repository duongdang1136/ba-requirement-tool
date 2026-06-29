"""
Audio processing pipeline:
normalize → VAD → ASR → diarization → merge → store segments
"""
import subprocess
from pathlib import Path
from datetime import datetime
from typing import TypedDict

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.meeting import ProcessingJob, MediaFile
from app.models.transcript import TranscriptSegment


class TranscriptCandidate(TypedDict):
    start: float
    end: float
    text: str
    speaker: str


class SpeechInterval(TypedDict):
    start: float
    end: float


class SpeakerTurn(TypedDict):
    start: float
    end: float
    speaker: str


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
        job.progress = 30
        job.step = "vad"
        db.commit()

        speech_intervals = _detect_speech_intervals(normalized_path)
        if speech_intervals is None:
            job.status = "failed"
            job.error = "VAD failed — check VAD model path"
            db.commit()
            return

        job.progress = 45
        job.step = "asr"
        db.commit()

        # Step 2: Run Whisper ASR
        segments = _run_whisper_asr(normalized_path, speech_intervals)
        if segments is None:
            job.status = "failed"
            job.error = "ASR failed — check model path"
            db.commit()
            return

        job.progress = 75
        job.step = "diarize"
        db.commit()

        speaker_turns = _run_diarization(normalized_path)
        if speaker_turns:
            for seg in segments:
                seg["speaker"] = _assign_speaker(seg["start"], seg["end"], speaker_turns)

        job.progress = 90
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
                speaker_label=seg.get("speaker", "SPEAKER_00"),
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


def _detect_speech_intervals(audio_path: Path) -> list[SpeechInterval] | None:
    """Return speech intervals in original audio timeline."""
    try:
        import numpy as np
        import sherpa_onnx
        import soundfile as sf

        vad_model = Path(settings.vad_model_path)
        if not vad_model.exists():
            print(f"[VAD] Model not found at {vad_model}")
            return None

        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=True)
        samples = np.ascontiguousarray(samples[:, 0])
        if sample_rate != 16000:
            print(f"[VAD] Expected 16kHz normalized audio, got {sample_rate}")
            return None

        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(vad_model)
        config.silero_vad.threshold = 0.5
        config.silero_vad.min_silence_duration = 0.35
        config.silero_vad.min_speech_duration = 0.25
        config.silero_vad.max_speech_duration = 28
        config.sample_rate = sample_rate

        vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=60)
        window_size = config.silero_vad.window_size
        offset = 0
        intervals: list[SpeechInterval] = []

        while offset + window_size <= len(samples):
            vad.accept_waveform(samples[offset: offset + window_size])
            offset += window_size
            while not vad.empty():
                segment = vad.front
                intervals.append({
                    "start": round(segment.start / sample_rate, 2),
                    "end": round((segment.start + len(segment.samples)) / sample_rate, 2),
                })
                vad.pop()

        if offset < len(samples):
            vad.accept_waveform(samples[offset:])

        vad.flush()
        while not vad.empty():
            segment = vad.front
            intervals.append({
                "start": round(segment.start / sample_rate, 2),
                "end": round((segment.start + len(segment.samples)) / sample_rate, 2),
            })
            vad.pop()

        return _merge_intervals(intervals)

    except ImportError:
        print("[VAD] sherpa-onnx or soundfile not installed")
        return None
    except Exception as e:
        print(f"[VAD error] {e}")
        return None


def _merge_intervals(intervals: list[SpeechInterval], gap: float = 0.4, max_duration: float = 28.0) -> list[SpeechInterval]:
    if not intervals:
        return []

    merged: list[SpeechInterval] = []
    current = dict(intervals[0])
    for interval in intervals[1:]:
        would_merge = interval["start"] - current["end"] <= gap
        would_fit = interval["end"] - current["start"] <= max_duration
        if would_merge and would_fit:
            current["end"] = max(current["end"], interval["end"])
        else:
            merged.append({"start": current["start"], "end": current["end"]})
            current = dict(interval)

    merged.append({"start": current["start"], "end": current["end"]})
    return merged


def _run_whisper_asr(audio_path: Path, speech_intervals: list[SpeechInterval]) -> list[TranscriptCandidate] | None:
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
            return None

        recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(encoder),
            decoder=str(decoder),
            tokens=str(tokens),
            num_threads=4,
            decoding_method="greedy_search",
            language=settings.asr_language,  # "vi"
            task="transcribe",
        )

        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)
        duration = len(samples) / sample_rate

        if not speech_intervals:
            return [{"start": 0.0, "end": duration, "text": "(Không phát hiện giọng nói)", "speaker": "SPEAKER_00"}]

        segments: list[TranscriptCandidate] = []
        for interval in speech_intervals:
            start_sec = max(0.0, interval["start"])
            end_sec = min(duration, interval["end"])
            start_sample = int(start_sec * sample_rate)
            end_sample = int(end_sec * sample_rate)
            chunk = samples[start_sample:end_sample]
            if len(chunk) == 0:
                continue

            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, chunk)
            recognizer.decode_stream(stream)
            text = stream.result.text.strip()

            if text:
                segments.append({
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "text": text,
                    "speaker": "SPEAKER_00",
                })

        return segments if segments else [{"start": 0.0, "end": duration, "text": "(Không nhận dạng được âm thanh)", "speaker": "SPEAKER_00"}]

    except ImportError:
        print("[ASR] sherpa-onnx not installed")
        return None
    except Exception as e:
        print(f"[ASR error] {e}")
        return None


def _run_diarization(audio_path: Path) -> list[SpeakerTurn] | None:
    try:
        import numpy as np
        import sherpa_onnx
        import soundfile as sf

        segmentation_model = Path(settings.diarization_segmentation_model)
        embedding_model = Path(settings.diarization_embedding_model)
        if not segmentation_model.exists() or not embedding_model.exists():
            print(f"[Diarization] Models not found: {segmentation_model}, {embedding_model}")
            return None

        config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
            segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
                pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                    model=str(segmentation_model),
                ),
            ),
            embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
                model=str(embedding_model),
            ),
            clustering=sherpa_onnx.FastClusteringConfig(
                num_clusters=-1,
                threshold=settings.diarization_cluster_threshold,
            ),
            min_duration_on=0.3,
            min_duration_off=0.5,
        )
        if not config.validate():
            print("[Diarization] Invalid config")
            return None

        diarizer = sherpa_onnx.OfflineSpeakerDiarization(config)
        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=True)
        samples = np.ascontiguousarray(samples[:, 0])
        if sample_rate != diarizer.sample_rate:
            print(f"[Diarization] Expected {diarizer.sample_rate}Hz audio, got {sample_rate}")
            return None

        result = diarizer.process(samples).sort_by_start_time()
        return [
            {
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": f"SPEAKER_{int(turn.speaker):02d}",
            }
            for turn in result
        ]

    except ImportError:
        print("[Diarization] sherpa-onnx or soundfile not installed")
        return None
    except Exception as e:
        print(f"[Diarization error] {e}")
        return None


def _assign_speaker(start: float, end: float, speaker_turns: list[SpeakerTurn]) -> str:
    best_speaker = "SPEAKER_00"
    best_overlap = 0.0
    for turn in speaker_turns:
        overlap = max(0.0, min(end, turn["end"]) - max(start, turn["start"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = turn["speaker"]
    return best_speaker
