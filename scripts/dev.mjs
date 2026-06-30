import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const isWindows = process.platform === 'win32'
const venvPython = isWindows
  ? join(root, 'backend', '.venv', 'Scripts', 'python.exe')
  : join(root, 'backend', '.venv', 'bin', 'python')

if (!existsSync(venvPython)) {
  console.error('Backend virtual environment not found. Run npm run setup first.')
  process.exit(1)
}

function quoteArg(value) {
  return `"${String(value).replaceAll('"', '\\"')}"`
}

const concurrentlyBin = join(root, 'node_modules', 'concurrently', 'dist', 'bin', 'concurrently.js')
const backendCommand = [
  isWindows ? `cd /d ${quoteArg(join(root, 'backend'))} &&` : `cd ${quoteArg(join(root, 'backend'))} &&`,
  quoteArg(venvPython),
  '-m',
  'uvicorn',
  'app.main:app',
  '--host',
  '0.0.0.0',
  '--port',
  '8099',
  '--reload',
].join(' ')

const workerCommand = [
  isWindows ? `cd /d ${quoteArg(join(root, 'backend'))} &&` : `cd ${quoteArg(join(root, 'backend'))} &&`,
  quoteArg(venvPython),
  '-m',
  'app.worker',
].join(' ')

const frontendCommand = `${isWindows ? 'npm.cmd' : 'npm'} --prefix ${quoteArg(join(root, 'frontend'))} run dev`

const result = spawnSync(
  process.execPath,
  [
    concurrentlyBin,
    '--kill-others-on-fail',
    '--names',
    'backend,worker,frontend',
    '--prefix-colors',
    'blue,magenta,green',
    backendCommand,
    workerCommand,
    frontendCommand,
  ],
  {
    cwd: root,
    stdio: 'inherit',
    shell: false,
    env: {
      ...process.env,
      DATABASE_URL: process.env.DATABASE_URL ?? 'sqlite:///./ba_tool.db',
      UPLOAD_DIR: process.env.UPLOAD_DIR ?? './uploads',
      MODELS_DIR: process.env.MODELS_DIR ?? '../models',
      ASR_MODEL_DIR: process.env.ASR_MODEL_DIR ?? '../models/asr/sherpa-onnx-whisper-small',
      ASR_LANGUAGE: process.env.ASR_LANGUAGE ?? 'vi',
      ASR_NUM_THREADS: process.env.ASR_NUM_THREADS ?? '8',
      VAD_MODEL_PATH: process.env.VAD_MODEL_PATH ?? '../models/vad/silero_vad.onnx',
      DIARIZATION_SEGMENTATION_MODEL: process.env.DIARIZATION_SEGMENTATION_MODEL ?? '../models/diarization/sherpa-onnx-pyannote-segmentation-3-0/model.onnx',
      DIARIZATION_EMBEDDING_MODEL: process.env.DIARIZATION_EMBEDDING_MODEL ?? '../models/diarization/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx',
      DIARIZATION_CHUNK_MINUTES: process.env.DIARIZATION_CHUNK_MINUTES ?? '25',
      WORKER_POLL_INTERVAL_SECONDS: process.env.WORKER_POLL_INTERVAL_SECONDS ?? '2.0',
      JOB_TIMEOUT_MINUTES: process.env.JOB_TIMEOUT_MINUTES ?? '240',
      CORS_ORIGINS: process.env.CORS_ORIGINS ?? '["http://localhost:5173","http://localhost:3000"]',
    },
  },
)

if (result.error) {
  console.error(result.error.message)
}

process.exit(result.status ?? 1)
