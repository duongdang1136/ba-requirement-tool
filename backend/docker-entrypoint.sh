#!/usr/bin/env sh
set -eu

MODEL_DIR="${ASR_MODEL_DIR:-/app/models/asr/sherpa-onnx-whisper-small}"
MODEL_URL="${ASR_MODEL_URL:-https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2}"
ARCHIVE="/tmp/sherpa-onnx-whisper-small.tar.bz2"

mkdir -p /app/data /app/uploads /app/models/asr

if [ ! -f "$MODEL_DIR/small-encoder.int8.onnx" ] || [ ! -f "$MODEL_DIR/small-decoder.int8.onnx" ] || [ ! -f "$MODEL_DIR/small-tokens.txt" ]; then
  echo "ASR model not found at $MODEL_DIR"
  echo "Downloading Whisper small model..."
  curl -L --fail --retry 3 --retry-delay 5 -o "$ARCHIVE" "$MODEL_URL"
  tar -xjf "$ARCHIVE" -C /app/models/asr
  rm -f "$ARCHIVE"
fi

exec "$@"
