import { existsSync, rmSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const args = new Set(process.argv.slice(2))

function removePath(path) {
  if (!existsSync(path)) return
  rmSync(path, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 })
  console.log(`Removed ${path}`)
}

function removeContents(path) {
  if (!existsSync(path)) return
  for (const entry of readdirSync(path, { withFileTypes: true })) {
    removePath(join(path, entry.name))
  }
  console.log(`Cleaned ${path}`)
}

function walk(dir, visitor) {
  if (!existsSync(dir)) return
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) {
      if (['.git', '.venv', 'node_modules', 'models'].includes(entry.name)) {
        continue
      }
      visitor(path, entry.name)
      walk(path, visitor)
    }
  }
}

function folderSize(path) {
  if (!existsSync(path)) return 0
  const stat = statSync(path)
  if (stat.isFile()) return stat.size
  let size = 0
  for (const entry of readdirSync(path, { withFileTypes: true })) {
    size += folderSize(join(path, entry.name))
  }
  return size
}

function removeProjectArtifacts() {
  removePath(join(root, 'frontend', 'dist'))
  removePath(join(root, '.pytest_cache'))
  removePath(join(root, 'backend', '.pytest_cache'))
  removePath(join(root, 'htmlcov'))
  removePath(join(root, '.coverage'))

  walk(root, (path, name) => {
    if (name === '__pycache__') {
      removePath(path)
    }
  })
}

function removeSystemCaches() {
  const home = process.env.USERPROFILE || process.env.HOME
  const temp = process.env.TEMP || process.env.TMPDIR
  const candidates = [
    temp,
    home ? join(home, 'AppData', 'Local', 'npm-cache') : '',
    home ? join(home, 'AppData', 'Local', 'pip', 'Cache') : '',
    home ? join(home, '.npm') : '',
    home ? join(home, '.cache', 'pip') : '',
  ].filter(Boolean)

  for (const path of candidates) {
    removeContents(path)
  }
}

removeProjectArtifacts()

if (args.has('--system-cache')) {
  removeSystemCaches()
} else {
  console.log('Skipped system caches. Run `npm run cleanup -- --system-cache` to clear npm/pip/temp caches.')
}

const remaining = folderSize(join(root, 'frontend', 'dist'))
if (remaining > 0) {
  process.exitCode = 1
}
