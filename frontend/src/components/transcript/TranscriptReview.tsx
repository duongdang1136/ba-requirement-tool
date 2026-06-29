import React, { useState, useEffect } from 'react'
import { meetingsApi, transcriptApi, exportApi, aiSettingsApi } from '../../api'
import type { TranscriptSegment, ProcessingStatus, Speaker, AISettings } from '../../types'

interface Props {
  meetingId: string
  meetingTitle: string
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function TranscriptReview({ meetingId, meetingTitle }: Props) {
  const [status, setStatus] = useState<ProcessingStatus | null>(null)
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [speakers, setSpeakers] = useState<Speaker[]>([])
  const [speakerNames, setSpeakerNames] = useState<Record<string, string>>({})
  const [aiSettings, setAiSettings] = useState<AISettings | null>(null)
  const [geminiKey, setGeminiKey] = useState('')
  const [geminiModel, setGeminiModel] = useState('gemini-2.0-flash')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadStatus()
    loadAISettings()
  }, [meetingId])

  async function loadStatus() {
    try {
      const s = await meetingsApi.status(meetingId)
      setStatus(s)
      if (s.status === 'completed') {
        loadTranscript()
      } else if (s.status === 'running' || s.status === 'queued') {
        setTimeout(loadStatus, 2000) // poll
      }
    } catch {
      // No job yet
    }
  }

  async function loadTranscript() {
    const segs = await transcriptApi.get(meetingId)
    const speakerList = await transcriptApi.speakers(meetingId)
    setSegments(segs)
    setSpeakers(speakerList)
    setSpeakerNames(Object.fromEntries(speakerList.map(s => [s.speaker_label, s.display_name])))
  }

  async function loadAISettings() {
    const settings = await aiSettingsApi.get()
    setAiSettings(settings)
    setGeminiModel(settings.model)
  }

  function startEdit(seg: TranscriptSegment) {
    setEditingId(seg.id)
    setEditText(seg.edited_text ?? seg.refined_text ?? seg.original_text)
  }

  async function saveEdit(segId: string) {
    setLoading(true)
    const updated = await transcriptApi.update(segId, { edited_text: editText })
    setSegments(prev => prev.map(s => s.id === segId ? updated : s))
    setEditingId(null)
    setLoading(false)
  }

  async function downloadExport(format: 'markdown' | 'txt') {
    const blob = format === 'markdown'
      ? await exportApi.transcriptMarkdown(meetingId)
      : await exportApi.transcriptTxt(meetingId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transcript-${meetingId}.${format === 'markdown' ? 'md' : 'txt'}`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function clearTranscript() {
    const confirmed = window.confirm('Clear transcript segments for this meeting? This does not delete the meeting or uploaded file.')
    if (!confirmed) return

    setLoading(true)
    await transcriptApi.clear(meetingId)
    setSegments([])
    setSpeakers([])
    setSpeakerNames({})
    setEditingId(null)
    setEditText('')
    setLoading(false)
  }

  async function saveSpeakerName(speakerLabel: string) {
    setLoading(true)
    const displayName = speakerNames[speakerLabel]?.trim() ?? ''
    await transcriptApi.renameSpeaker(meetingId, speakerLabel, displayName)
    setSpeakers(prev => prev.map(s => s.speaker_label === speakerLabel ? { ...s, display_name: displayName } : s))
    setLoading(false)
  }

  async function saveGeminiSettings() {
    setLoading(true)
    const settings = await aiSettingsApi.update({ api_key: geminiKey || undefined, model: geminiModel })
    setAiSettings(settings)
    setGeminiKey('')
    setLoading(false)
  }

  async function refineAll() {
    if (!aiSettings?.has_api_key) {
      window.alert('Configure your Gemini API key first.')
      return
    }

    setLoading(true)
    await aiSettingsApi.refineMeeting(meetingId)
    await loadTranscript()
    setLoading(false)
  }

  async function refineOne(segmentId: string) {
    if (!aiSettings?.has_api_key) {
      window.alert('Configure your Gemini API key first.')
      return
    }

    setLoading(true)
    const updated = await aiSettingsApi.refineSegment(segmentId)
    setSegments(prev => prev.map(s => s.id === segmentId ? updated : s))
    setLoading(false)
  }

  function speakerDisplay(label: string) {
    return speakerNames[label]?.trim() || label
  }

  if (!status) {
    return (
      <div style={{ padding: 24 }}>
        <h2>{meetingTitle}</h2>
        <p style={{ color: '#888' }}>No processing job found. Upload a file and start processing.</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, maxWidth: 900 }}>
      <h2 style={{ marginBottom: 8 }}>{meetingTitle}</h2>

      {/* Status bar */}
      <div style={{
        padding: '8px 16px',
        borderRadius: 8,
        marginBottom: 24,
        background: status.status === 'completed' ? '#e6f4ea' : status.status === 'failed' ? '#fce8e6' : '#fff3cd',
        border: `1px solid ${status.status === 'completed' ? '#34a853' : status.status === 'failed' ? '#ea4335' : '#fbbc04'}`,
      }}>
        <strong>Status:</strong> {status.step} — {status.status}
        {status.progress > 0 && status.progress < 100 && (
          <span> ({status.progress}%)</span>
        )}
        {status.error && <span style={{ color: 'red' }}> Error: {status.error}</span>}
      </div>

      {/* Export buttons */}
      {status.status === 'completed' && segments.length > 0 && (
        <div style={{ marginBottom: 24, display: 'flex', gap: 8 }}>
          <button onClick={() => downloadExport('markdown')} style={btnStyle}>Export Markdown</button>
          <button onClick={() => downloadExport('txt')} style={btnStyle}>Export TXT</button>
          <button onClick={refineAll} disabled={loading} style={btnStyle}>Refine with Gemini</button>
          <button onClick={clearTranscript} disabled={loading} style={btnDanger}>Clear Transcript</button>
        </div>
      )}

      <div style={{ ...panelStyle, marginBottom: 24 }}>
        <div style={{ fontWeight: 600, marginBottom: 12 }}>Gemini</div>
        <div style={{ display: 'grid', gap: 10 }}>
          <div style={{ fontSize: 13, color: '#555' }}>
            Status: {aiSettings?.has_api_key ? 'API key configured' : 'No API key configured'}
          </div>
          <input
            type="password"
            value={geminiKey}
            onChange={e => setGeminiKey(e.target.value)}
            placeholder="Gemini API key"
            style={inputStyle}
          />
          <input
            value={geminiModel}
            onChange={e => setGeminiModel(e.target.value)}
            placeholder="gemini-2.0-flash"
            style={inputStyle}
          />
          <div>
            <button onClick={saveGeminiSettings} disabled={loading} style={btnOutline}>Save Gemini Settings</button>
          </div>
        </div>
      </div>

      {status.status === 'completed' && speakers.length > 0 && (
        <div style={{ ...panelStyle, marginBottom: 24 }}>
          <div style={{ fontWeight: 600, marginBottom: 12 }}>Speakers</div>
          <div style={{ display: 'grid', gap: 10 }}>
            {speakers.map(speaker => (
              <div key={speaker.speaker_label} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ width: 90, fontSize: 12, color: '#555' }}>{speaker.speaker_label}</span>
                <input
                  value={speakerNames[speaker.speaker_label] ?? ''}
                  onChange={e => setSpeakerNames(prev => ({ ...prev, [speaker.speaker_label]: e.target.value }))}
                  placeholder="Client, BA, PM..."
                  style={inputStyle}
                />
                <button onClick={() => saveSpeakerName(speaker.speaker_label)} disabled={loading} style={btnOutline}>
                  Rename
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transcript */}
      <div>
        {segments.map(seg => (
          <div key={seg.id} style={{
            display: 'flex',
            gap: 16,
            padding: '12px 0',
            borderBottom: '1px solid #eee',
          }}>
            <div style={{ minWidth: 120, color: '#666', fontSize: 13, paddingTop: 2 }}>
              <span>{formatTime(seg.start)} – {formatTime(seg.end)}</span>
              <br />
              <span style={{ fontSize: 11, background: '#f0f0f0', borderRadius: 4, padding: '2px 6px' }}>
                {speakerDisplay(seg.speaker_label)}
              </span>
            </div>
            <div style={{ flex: 1 }}>
              {editingId === seg.id ? (
                <div>
                  <textarea
                    value={editText}
                    onChange={e => setEditText(e.target.value)}
                    rows={3}
                    style={{ width: '100%', fontSize: 14, padding: 8, borderRadius: 4, border: '1px solid #aaa' }}
                  />
                  <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                    <button onClick={() => saveEdit(seg.id)} disabled={loading} style={btnStyle}>Save</button>
                    <button onClick={() => setEditingId(null)} style={btnOutline}>Cancel</button>
                  </div>
                </div>
              ) : (
                <div style={{ position: 'relative' }}>
                  <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>
                    {seg.display_text}
                    {seg.refined_text && !seg.edited_text && (
                      <span style={{ marginLeft: 8, fontSize: 11, color: '#1a73e8' }}>refined</span>
                    )}
                    {seg.edited_text && (
                      <span style={{ marginLeft: 8, fontSize: 11, color: '#34a853' }}>✏ edited</span>
                    )}
                  </p>
                  {seg.refined_text && (
                    <details style={{ marginTop: 6, fontSize: 12, color: '#666' }}>
                      <summary>Raw ASR</summary>
                      <div style={{ marginTop: 4 }}>{seg.original_text}</div>
                    </details>
                  )}
                  <button
                    onClick={() => startEdit(seg)}
                    style={{ ...btnOutline, fontSize: 11, padding: '2px 8px', marginTop: 4 }}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => refineOne(seg.id)}
                    disabled={loading}
                    style={{ ...btnOutline, fontSize: 11, padding: '2px 8px', marginTop: 4, marginLeft: 6 }}
                  >
                    Refine
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '8px 16px',
  background: '#1a73e8',
  color: 'white',
  border: 'none',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 13,
}

const btnOutline: React.CSSProperties = {
  padding: '8px 16px',
  background: 'white',
  color: '#1a73e8',
  border: '1px solid #1a73e8',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 13,
}

const btnDanger: React.CSSProperties = {
  padding: '8px 16px',
  background: '#b3261e',
  color: 'white',
  border: 'none',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 13,
}

const panelStyle: React.CSSProperties = {
  background: 'white',
  border: '1px solid #e0e0e0',
  borderRadius: 8,
  padding: 16,
}

const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: '7px 10px',
  border: '1px solid #ccc',
  borderRadius: 6,
  fontSize: 13,
}
