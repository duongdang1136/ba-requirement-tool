import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const isWindows = process.platform === 'win32'
const pythonCmd = isWindows ? 'python' : 'python3'
const venvDir = join(root, 'backend', '.venv')
const venvPython = isWindows
  ? join(venvDir, 'Scripts', 'python.exe')
  : join(venvDir, 'bin', 'python')
const modelDir = join(root, 'models', 'asr', 'sherpa-onnx-whisper-small')
const modelUrl = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2'
const archivePath = join(root, 'models', 'asr', 'sherpa-onnx-whisper-small.tar.bz2')

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: 'inherit',
    shell: isWindows,
    ...options,
  })
  if (result.status !== 0) {
    process.exit(result.status ?? 1)
  }
}

function check(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: 'ignore',
    shell: isWindows,
  })
  return result.status === 0
}

console.log('Checking prerequisites...')
if (!check(pythonCmd, ['--version'])) {
  console.error('Python 3.10+ is required. Install Python, then run npm run setup again.')
  process.exit(1)
}

if (!check('ffmpeg', ['-version'])) {
  console.error('ffmpeg is required for audio/video normalization.')
  console.error('Install ffmpeg, then run npm run setup again.')
  process.exit(1)
}

console.log('Installing frontend dependencies...')
run('npm', ['--prefix', 'frontend', 'install'])

if (!existsSync(venvPython)) {
  console.log('Creating backend virtual environment...')
  run(pythonCmd, ['-m', 'venv', venvDir])
}

console.log('Installing backend dependencies...')
run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'])
run(venvPython, ['-m', 'pip', 'install', '-r', join(root, 'backend', 'requirements.txt')])

mkdirSync(join(root, 'models', 'asr'), { recursive: true })
if (
  existsSync(join(modelDir, 'small-encoder.int8.onnx')) &&
  existsSync(join(modelDir, 'small-decoder.int8.onnx')) &&
  existsSync(join(modelDir, 'small-tokens.txt'))
) {
  console.log('ASR model already exists.')
} else {
  console.log('Downloading Whisper small ASR model...')
  run(venvPython, ['-c', `
from pathlib import Path
from urllib.request import urlretrieve
urlretrieve(${JSON.stringify(modelUrl)}, ${JSON.stringify(archivePath)})
`])

  console.log('Extracting ASR model...')
  run(venvPython, ['-c', `
import tarfile
from pathlib import Path
archive = Path(${JSON.stringify(archivePath)})
target = Path(${JSON.stringify(join(root, 'models', 'asr'))})
target.mkdir(parents=True, exist_ok=True)
with tarfile.open(archive, 'r:bz2') as f:
    f.extractall(target)
archive.unlink()
`])
}

console.log('')
console.log('Setup complete.')
console.log('Run npm run dev and open http://localhost:5173')
