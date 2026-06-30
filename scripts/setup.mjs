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
const vadModelPath = join(root, 'models', 'vad', 'silero_vad.onnx')
const vadModelUrl = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx'
const diarizationDir = join(root, 'models', 'diarization')
const segmentationDir = join(diarizationDir, 'sherpa-onnx-pyannote-segmentation-3-0')
const segmentationArchive = join(diarizationDir, 'sherpa-onnx-pyannote-segmentation-3-0.tar.bz2')
const segmentationUrl = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2'
const embeddingModelPath = join(diarizationDir, '3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx')
const embeddingModelUrl = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx'

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
`], { shell: false })

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
`], { shell: false })
}

mkdirSync(join(root, 'models', 'vad'), { recursive: true })
if (existsSync(vadModelPath)) {
  console.log('VAD model already exists.')
} else {
  console.log('Downloading Silero VAD model...')
  run(venvPython, ['-c', `
from urllib.request import urlretrieve
urlretrieve(${JSON.stringify(vadModelUrl)}, ${JSON.stringify(vadModelPath)})
`], { shell: false })
}

mkdirSync(diarizationDir, { recursive: true })
if (existsSync(join(segmentationDir, 'model.onnx'))) {
  console.log('Speaker segmentation model already exists.')
} else {
  console.log('Downloading speaker segmentation model...')
  run(venvPython, ['-c', `
from urllib.request import urlretrieve
urlretrieve(${JSON.stringify(segmentationUrl)}, ${JSON.stringify(segmentationArchive)})
`], { shell: false })
  console.log('Extracting speaker segmentation model...')
  run(venvPython, ['-c', `
import tarfile
from pathlib import Path
archive = Path(${JSON.stringify(segmentationArchive)})
target = Path(${JSON.stringify(diarizationDir)})
with tarfile.open(archive, 'r:bz2') as f:
    f.extractall(target)
archive.unlink()
`], { shell: false })
}

if (existsSync(embeddingModelPath)) {
  console.log('Speaker embedding model already exists.')
} else {
  console.log('Downloading speaker embedding model...')
  run(venvPython, ['-c', `
from urllib.request import urlretrieve
urlretrieve(${JSON.stringify(embeddingModelUrl)}, ${JSON.stringify(embeddingModelPath)})
`], { shell: false })
}

console.log('')
console.log('Setup complete.')
console.log('Run npm run dev and open http://localhost:5173')
