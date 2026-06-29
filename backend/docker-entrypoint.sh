#!/usr/bin/env sh
set -eu

MODEL_DIR="${ASR_MODEL_DIR:-/app/models/asr/sherpa-onnx-whisper-small}"
MODEL_URL="${ASR_MODEL_URL:-https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2}"
ARCHIVE="/tmp/sherpa-onnx-whisper-small.tar.bz2"
VAD_MODEL_PATH="${VAD_MODEL_PATH:-/app/models/vad/silero_vad.onnx}"
VAD_MODEL_URL="${VAD_MODEL_URL:-https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx}"
DIARIZATION_SEGMENTATION_MODEL="${DIARIZATION_SEGMENTATION_MODEL:-/app/models/diarization/sherpa-onnx-pyannote-segmentation-3-0/model.onnx}"
DIARIZATION_SEGMENTATION_URL="${DIARIZATION_SEGMENTATION_URL:-https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2}"
DIARIZATION_SEGMENTATION_ARCHIVE="/tmp/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
DIARIZATION_EMBEDDING_MODEL="${DIARIZATION_EMBEDDING_MODEL:-/app/models/diarization/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx}"
DIARIZATION_EMBEDDING_URL="${DIARIZATION_EMBEDDING_URL:-https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx}"

mkdir -p /app/data /app/uploads /app/models/asr /app/models/vad /app/models/diarization

if [ ! -f "$MODEL_DIR/small-encoder.int8.onnx" ] || [ ! -f "$MODEL_DIR/small-decoder.int8.onnx" ] || [ ! -f "$MODEL_DIR/small-tokens.txt" ]; then
  echo "ASR model not found at $MODEL_DIR"
  echo "Downloading Whisper small model..."
  curl -L --fail --retry 3 --retry-delay 5 -o "$ARCHIVE" "$MODEL_URL"
  tar -xjf "$ARCHIVE" -C /app/models/asr
  rm -f "$ARCHIVE"
fi

if [ ! -f "$VAD_MODEL_PATH" ]; then
  echo "VAD model not found at $VAD_MODEL_PATH"
  echo "Downloading Silero VAD model..."
  curl -L --fail --retry 3 --retry-delay 5 -o "$VAD_MODEL_PATH" "$VAD_MODEL_URL"
fi

if [ ! -f "$DIARIZATION_SEGMENTATION_MODEL" ]; then
  echo "Speaker segmentation model not found at $DIARIZATION_SEGMENTATION_MODEL"
  echo "Downloading speaker segmentation model..."
  curl -L --fail --retry 3 --retry-delay 5 -o "$DIARIZATION_SEGMENTATION_ARCHIVE" "$DIARIZATION_SEGMENTATION_URL"
  tar -xjf "$DIARIZATION_SEGMENTATION_ARCHIVE" -C /app/models/diarization
  rm -f "$DIARIZATION_SEGMENTATION_ARCHIVE"
fi

if [ ! -f "$DIARIZATION_EMBEDDING_MODEL" ]; then
  echo "Speaker embedding model not found at $DIARIZATION_EMBEDDING_MODEL"
  echo "Downloading speaker embedding model..."
  curl -L --fail --retry 3 --retry-delay 5 -o "$DIARIZATION_EMBEDDING_MODEL" "$DIARIZATION_EMBEDDING_URL"
fi

exec "$@"
