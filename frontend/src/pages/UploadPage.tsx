import React, { useState } from 'react'
import { meetingsApi } from '../api'

interface Props {
  projectId: string
  onMeetingCreated: (meetingId: string) => void
}

export default function UploadPage({ projectId, onMeetingCreated }: Props) {
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [step, setStep] = useState<'form' | 'uploading' | 'processing'>('form')
  const [error, setError] = useState('')
  const [progress, setProgress] = useState('')

  const ALLOWED = ['.mp3', '.wav', '.m4a', '.mp4', '.webm', '.ogg']

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED.includes(ext)) {
      setError(`Unsupported file type. Allowed: ${ALLOWED.join(', ')}`)
      return
    }
    if (f.size > 500 * 1024 * 1024) {
      setError('File exceeds 500MB limit')
      return
    }
    setError('')
    setFile(f)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title || !file) {
      setError('Please enter a title and select a file')
      return
    }

    setStep('uploading')
    setProgress('Creating meeting...')

    try {
      const meeting = await meetingsApi.create({ project_id: projectId, title })
      setProgress('Uploading file...')
      await meetingsApi.uploadMedia(meeting.id, file)
      setProgress('Starting processing...')
      await meetingsApi.process(meeting.id)
      setStep('processing')
      onMeetingCreated(meeting.id)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
      setStep('form')
    }
  }

  return (
    <div style={{ maxWidth: 560, margin: '48px auto', padding: 32, border: '1px solid #e0e0e0', borderRadius: 12 }}>
      <h2 style={{ marginBottom: 8 }}>Upload Meeting</h2>
      <p style={{ color: '#666', marginBottom: 24, fontSize: 14 }}>
        Upload an audio or video file to generate a transcript.
      </p>

      {step === 'form' && (
        <form onSubmit={handleSubmit}>
          <label style={labelStyle}>Meeting Title</label>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Client kickoff — 2026-06-29"
            style={inputStyle}
          />

          <label style={labelStyle}>Audio / Video File</label>
          <input
            type="file"
            accept=".mp3,.wav,.m4a,.mp4,.webm,.ogg"
            onChange={handleFileChange}
            style={{ marginBottom: 16, display: 'block' }}
          />
          {file && (
            <div style={{ fontSize: 12, color: '#555', marginBottom: 16 }}>
              ✓ {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
            </div>
          )}

          {error && (
            <div style={{ color: '#d93025', marginBottom: 12, fontSize: 13 }}>{error}</div>
          )}

          <button type="submit" style={btnStyle}>Upload & Process</button>
        </form>
      )}

      {step === 'uploading' && (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>⏳</div>
          <p>{progress}</p>
        </div>
      )}
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontWeight: 600,
  marginBottom: 4,
  fontSize: 13,
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  border: '1px solid #ccc',
  borderRadius: 6,
  fontSize: 14,
  marginBottom: 16,
  boxSizing: 'border-box',
}

const btnStyle: React.CSSProperties = {
  padding: '10px 24px',
  background: '#1a73e8',
  color: 'white',
  border: 'none',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 600,
}
