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

const backendCommand = [
  JSON.stringify(venvPython),
  '-m',
  'uvicorn',
  'app.main:app',
  '--host',
  '0.0.0.0',
  '--port',
  '8099',
  '--reload',
].join(' ')

const frontendCommand = 'npm --prefix frontend run dev'

const result = spawnSync(
  isWindows ? 'npx.cmd' : 'npx',
  [
    'concurrently',
    '--kill-others-on-fail',
    '--names',
    'backend,frontend',
    '--prefix-colors',
    'blue,green',
    `cd backend && ${backendCommand}`,
    frontendCommand,
  ],
  {
    cwd: root,
    stdio: 'inherit',
    shell: isWindows,
    env: {
      ...process.env,
      DATABASE_URL: process.env.DATABASE_URL ?? 'sqlite:///./ba_tool.db',
      UPLOAD_DIR: process.env.UPLOAD_DIR ?? './uploads',
      MODELS_DIR: process.env.MODELS_DIR ?? '../models',
      ASR_MODEL_DIR: process.env.ASR_MODEL_DIR ?? '../models/asr/sherpa-onnx-whisper-small',
      ASR_LANGUAGE: process.env.ASR_LANGUAGE ?? 'vi',
      CORS_ORIGINS: process.env.CORS_ORIGINS ?? '["http://localhost:5173","http://localhost:3000"]',
    },
  },
)

process.exit(result.status ?? 1)
