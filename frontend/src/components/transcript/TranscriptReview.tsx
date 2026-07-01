import React, { useEffect, useState } from 'react'
import { exportApi, meetingsApi, requirementsApi, transcriptApi } from '../../api'
import type { MeetingArtifacts, ProcessingStatus, RequirementCandidate, Speaker, TranscriptSegment } from '../../types'

interface Props {
  meetingId: string
  meetingTitle: string
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function parseKeyPoints(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.map(String) : []
  } catch {
    return []
  }
}

export default function TranscriptReview({ meetingId, meetingTitle }: Props) {
  const emptyArtifacts: MeetingArtifacts = { summary: null, decisions: [], action_items: [], open_questions: [] }
  const [status, setStatus] = useState<ProcessingStatus | null>(null)
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [speakers, setSpeakers] = useState<Speaker[]>([])
  const [speakerNames, setSpeakerNames] = useState<Record<string, string>>({})
  const [artifacts, setArtifacts] = useState<MeetingArtifacts>(emptyArtifacts)
  const [candidates, setCandidates] = useState<RequirementCandidate[]>([])
  const [activeTab, setActiveTab] = useState<'transcript' | 'summary' | 'requirements'>('transcript')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingCandidateId, setEditingCandidateId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [candidateDraft, setCandidateDraft] = useState<Partial<RequirementCandidate>>({})
  const [rewriteSuggestions, setRewriteSuggestions] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [aiMessage, setAiMessage] = useState('')
  const [speakerCount, setSpeakerCount] = useState('')
  const [diarizationThreshold, setDiarizationThreshold] = useState('')

  useEffect(() => {
    loadStatus()
  }, [meetingId])

  async function loadStatus() {
    try {
      const s = await meetingsApi.status(meetingId)
      setStatus(s)
      if (s.status === 'completed') {
        loadTranscript()
        loadAiArtifacts()
      } else if (s.status === 'running' || s.status === 'queued') {
        setTimeout(loadStatus, 2000)
      }
    } catch {
      // No job yet
    }
  }

  async function loadTranscript() {
    const [segs, speakerList] = await Promise.all([
      transcriptApi.get(meetingId),
      transcriptApi.speakers(meetingId),
    ])
    setSegments(segs)
    setSpeakers(speakerList)
    setSpeakerNames(Object.fromEntries(speakerList.map(s => [s.speaker_label, s.display_name])))
  }

  async function loadAiArtifacts() {
    const [meetingArtifacts, requirementCandidates] = await Promise.all([
      meetingsApi.artifacts(meetingId),
      requirementsApi.listCandidates(meetingId),
    ])
    setArtifacts(meetingArtifacts)
    setCandidates(requirementCandidates)
  }

  function startEdit(seg: TranscriptSegment) {
    setEditingId(seg.id)
    setEditText(seg.edited_text ?? seg.original_text)
  }

  async function saveEdit(segId: string) {
    setLoading(true)
    const updated = await transcriptApi.update(segId, { edited_text: editText })
    setSegments(prev => prev.map(s => s.id === segId ? updated : s))
    setEditingId(null)
    setLoading(false)
  }

  async function suggestRewrite(segId: string) {
    setLoading(true)
    const suggestion = await transcriptApi.suggestRewrite(segId)
    setRewriteSuggestions(prev => ({ ...prev, [segId]: suggestion.suggestion }))
    setLoading(false)
  }

  async function replaceWithSuggestion(segId: string) {
    const suggestion = rewriteSuggestions[segId]
    if (!suggestion) return
    setLoading(true)
    const updated = await transcriptApi.update(segId, { edited_text: suggestion })
    setSegments(prev => prev.map(s => s.id === segId ? updated : s))
    setRewriteSuggestions(prev => {
      const next = { ...prev }
      delete next[segId]
      return next
    })
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

  async function rerunDiarization() {
    setLoading(true)
    await meetingsApi.rerunDiarization(meetingId, {
      diarization_num_speakers: speakerCount ? Number(speakerCount) : undefined,
      diarization_cluster_threshold: diarizationThreshold ? Number(diarizationThreshold) : undefined,
    })
    setLoading(false)
    loadStatus()
  }

  async function saveSpeakerName(speakerLabel: string) {
    setLoading(true)
    const displayName = speakerNames[speakerLabel]?.trim() ?? ''
    await transcriptApi.renameSpeaker(meetingId, speakerLabel, displayName)
    setSpeakers(prev => prev.map(s => s.speaker_label === speakerLabel ? { ...s, display_name: displayName } : s))
    setLoading(false)
  }

  async function generateSummary() {
    setLoading(true)
    setAiMessage('Summary job queued. Keep the worker and Ollama running.')
    await meetingsApi.generateSummary(meetingId)
    setLoading(false)
    loadStatus()
  }

  async function extractRequirements() {
    setLoading(true)
    setAiMessage('Requirement extraction job queued. Candidates will appear after completion.')
    await requirementsApi.extract(meetingId)
    setLoading(false)
    loadStatus()
  }

  function startCandidateEdit(candidate: RequirementCandidate) {
    setEditingCandidateId(candidate.id)
    setCandidateDraft({
      title: candidate.title,
      description: candidate.description,
      type: candidate.type,
      priority: candidate.priority,
      source_quote: candidate.source_quote,
    })
  }

  async function saveCandidate(candidateId: string) {
    setLoading(true)
    const updated = await requirementsApi.update(candidateId, candidateDraft)
    setCandidates(prev => prev.map(c => c.id === candidateId ? updated : c))
    setEditingCandidateId(null)
    setCandidateDraft({})
    setLoading(false)
  }

  async function approveCandidate(candidateId: string) {
    setLoading(true)
    await requirementsApi.approve(candidateId, {})
    await loadAiArtifacts()
    setLoading(false)
  }

  async function rejectCandidate(candidateId: string) {
    const reason = window.prompt('Reject reason', '')
    if (reason === null) return
    setLoading(true)
    await requirementsApi.reject(candidateId, reason)
    await loadAiArtifacts()
    setLoading(false)
  }

  function speakerDisplay(label: string) {
    return speakerNames[label]?.trim() || label
  }

  const hasProcessingWarning = status?.status === 'completed' && Boolean(status.error)
  const statusBackground = hasProcessingWarning ? '#fff3cd' : status?.status === 'completed' ? '#e6f4ea' : status?.status === 'failed' ? '#fce8e6' : '#fff3cd'
  const statusBorder = hasProcessingWarning ? '#fbbc04' : status?.status === 'completed' ? '#34a853' : status?.status === 'failed' ? '#ea4335' : '#fbbc04'

  if (!status) {
    return (
      <div style={{ padding: 24 }}>
        <h2>{meetingTitle}</h2>
        <p style={{ color: '#888' }}>No processing job found. Upload a file and start processing.</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, maxWidth: 980 }}>
      <h2 style={{ marginBottom: 8 }}>{meetingTitle}</h2>

      <div style={{ padding: '8px 16px', borderRadius: 8, marginBottom: 16, background: statusBackground, border: `1px solid ${statusBorder}` }}>
        <strong>Status:</strong> {status.step} - {status.status}
        {status.progress > 0 && status.progress < 100 && <span> ({status.progress}%)</span>}
        {status.error && (
          <div style={{ color: status.status === 'completed' ? '#8a5a00' : 'red', marginTop: 4 }}>
            {status.status === 'completed' ? 'Warning' : 'Error'}: {status.error}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, borderBottom: '1px solid #ddd' }}>
        <button onClick={() => setActiveTab('transcript')} style={activeTab === 'transcript' ? tabActive : tabStyle}>Transcript</button>
        <button onClick={() => setActiveTab('summary')} style={activeTab === 'summary' ? tabActive : tabStyle}>Summary</button>
        <button onClick={() => setActiveTab('requirements')} style={activeTab === 'requirements' ? tabActive : tabStyle}>Requirements</button>
      </div>

      {status.status === 'completed' && activeTab === 'transcript' && segments.length > 0 && (
        <>
          <div style={{ marginBottom: 24, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <button onClick={() => downloadExport('markdown')} style={btnStyle}>Export Markdown</button>
            <button onClick={() => downloadExport('txt')} style={btnStyle}>Export TXT</button>
            <input type="number" min="1" value={speakerCount} onChange={e => setSpeakerCount(e.target.value)} placeholder="Speakers" style={smallInputStyle} />
            <input type="number" min="0" max="1" step="0.05" value={diarizationThreshold} onChange={e => setDiarizationThreshold(e.target.value)} placeholder="Threshold" style={smallInputStyle} />
            <button onClick={rerunDiarization} disabled={loading} style={btnOutline}>Re-run Diarization</button>
            <button onClick={clearTranscript} disabled={loading} style={btnDanger}>Clear Transcript</button>
          </div>

          {speakers.length > 0 && (
            <div style={{ ...panelStyle, marginBottom: 24 }}>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>Speakers</div>
              <div style={{ display: 'grid', gap: 10 }}>
                {speakers.map(speaker => (
                  <div key={speaker.speaker_label} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ width: 90, fontSize: 12, color: '#555' }}>{speaker.speaker_label}</span>
                    <input value={speakerNames[speaker.speaker_label] ?? ''} onChange={e => setSpeakerNames(prev => ({ ...prev, [speaker.speaker_label]: e.target.value }))} placeholder="Client, BA, PM..." style={inputStyle} />
                    <button onClick={() => saveSpeakerName(speaker.speaker_label)} disabled={loading} style={btnOutline}>Rename</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {segments.map(seg => (
            <div key={seg.id} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid #eee' }}>
              <div style={{ minWidth: 120, color: '#666', fontSize: 13, paddingTop: 2 }}>
                <span>{formatTime(seg.start)} - {formatTime(seg.end)}</span><br />
                <span style={{ fontSize: 11, background: '#f0f0f0', borderRadius: 4, padding: '2px 6px' }}>{speakerDisplay(seg.speaker_label)}</span>
              </div>
              <div style={{ flex: 1 }}>
                {editingId === seg.id ? (
                  <div>
                    <textarea value={editText} onChange={e => setEditText(e.target.value)} rows={3} style={textareaStyle} />
                    <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                      <button onClick={() => saveEdit(seg.id)} disabled={loading} style={btnStyle}>Save</button>
                      <button onClick={() => setEditingId(null)} style={btnOutline}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>
                      {seg.display_text}
                      {seg.edited_text && <span style={{ marginLeft: 8, fontSize: 11, color: '#34a853' }}>edited</span>}
                    </p>
                    <button onClick={() => startEdit(seg)} style={{ ...btnOutline, fontSize: 11, padding: '2px 8px', marginTop: 4 }}>Edit</button>
                    <button onClick={() => suggestRewrite(seg.id)} disabled={loading} style={{ ...btnOutline, fontSize: 11, padding: '2px 8px', marginTop: 4, marginLeft: 6 }}>Suggest Rewrite</button>
                    {rewriteSuggestions[seg.id] && (
                      <div style={{ marginTop: 8, padding: 10, border: '1px solid #d7e3fc', borderRadius: 6, background: '#f8fbff' }}>
                        <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>Suggestion</div>
                        <div style={{ fontSize: 14, lineHeight: 1.5 }}>{rewriteSuggestions[seg.id]}</div>
                        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                          <button onClick={() => replaceWithSuggestion(seg.id)} disabled={loading} style={btnStyle}>Replace</button>
                          <button onClick={() => setRewriteSuggestions(prev => ({ ...prev, [seg.id]: '' }))} style={btnOutline}>Dismiss</button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </>
      )}

      {activeTab === 'summary' && (
        <div style={{ display: 'grid', gap: 16 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={generateSummary} disabled={loading || status.status !== 'completed'} style={btnStyle}>Generate Summary</button>
            <button onClick={loadAiArtifacts} disabled={loading} style={btnOutline}>Refresh</button>
            {aiMessage && <span style={{ fontSize: 13, color: '#666' }}>{aiMessage}</span>}
          </div>
          <div style={panelStyle}>
            <h3 style={panelTitle}>Summary</h3>
            <p style={{ lineHeight: 1.6, marginTop: 0 }}>{artifacts.summary?.summary || 'No summary generated yet.'}</p>
            {parseKeyPoints(artifacts.summary?.key_points ?? '[]').length > 0 && (
              <ul>{parseKeyPoints(artifacts.summary?.key_points ?? '[]').map((point, i) => <li key={i}>{point}</li>)}</ul>
            )}
          </div>
          <ArtifactList title="Decisions" items={artifacts.decisions.map(d => ({ title: d.title, body: d.description, owner: d.owner, quote: d.source_quote }))} />
          <ArtifactList title="Action Items" items={artifacts.action_items.map(a => ({ title: a.task, body: a.status, owner: a.owner, quote: a.source_quote }))} />
          <ArtifactList title="Open Questions" items={artifacts.open_questions.map(q => ({ title: q.question, body: q.status, owner: q.owner, quote: q.source_quote }))} />
        </div>
      )}

      {activeTab === 'requirements' && (
        <div style={{ display: 'grid', gap: 16 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={extractRequirements} disabled={loading || status.status !== 'completed'} style={btnStyle}>Extract Requirements</button>
            <button onClick={loadAiArtifacts} disabled={loading} style={btnOutline}>Refresh</button>
            {aiMessage && <span style={{ fontSize: 13, color: '#666' }}>{aiMessage}</span>}
          </div>
          {candidates.length === 0 && <div style={panelStyle}>No requirement candidates yet.</div>}
          {candidates.map(candidate => (
            <div key={candidate.id} style={panelStyle}>
              {editingCandidateId === candidate.id ? (
                <div style={{ display: 'grid', gap: 8 }}>
                  <input value={candidateDraft.title ?? ''} onChange={e => setCandidateDraft(prev => ({ ...prev, title: e.target.value }))} style={fullInputStyle} />
                  <textarea value={candidateDraft.description ?? ''} onChange={e => setCandidateDraft(prev => ({ ...prev, description: e.target.value }))} rows={4} style={textareaStyle} />
                  <input value={candidateDraft.source_quote ?? ''} onChange={e => setCandidateDraft(prev => ({ ...prev, source_quote: e.target.value }))} style={fullInputStyle} />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => saveCandidate(candidate.id)} disabled={loading} style={btnStyle}>Save</button>
                    <button onClick={() => setEditingCandidateId(null)} style={btnOutline}>Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                    <div>
                      <div style={{ fontWeight: 700 }}>{candidate.title}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>{candidate.type} - {candidate.priority} - {candidate.review_state}</div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button onClick={() => startCandidateEdit(candidate)} disabled={loading} style={btnOutline}>Edit</button>
                      <button onClick={() => approveCandidate(candidate.id)} disabled={loading || candidate.review_state === 'approved'} style={btnStyle}>Approve</button>
                      <button onClick={() => rejectCandidate(candidate.id)} disabled={loading || candidate.review_state === 'rejected'} style={btnDanger}>Reject</button>
                    </div>
                  </div>
                  <p style={{ lineHeight: 1.6 }}>{candidate.description}</p>
                  {candidate.source_quote && <blockquote style={quoteStyle}>{candidate.source_quote}</blockquote>}
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ArtifactList({ title, items }: { title: string; items: Array<{ title: string; body: string; owner: string; quote: string }> }) {
  return (
    <div style={panelStyle}>
      <h3 style={panelTitle}>{title}</h3>
      {items.length === 0 && <p style={{ color: '#777' }}>No items yet.</p>}
      {items.map((item, index) => (
        <div key={index} style={{ padding: '10px 0', borderTop: index === 0 ? 'none' : '1px solid #eee' }}>
          <div style={{ fontWeight: 600 }}>{item.title}</div>
          {item.owner && <div style={{ fontSize: 12, color: '#666' }}>Owner: {item.owner}</div>}
          {item.body && <div style={{ fontSize: 13, marginTop: 4 }}>{item.body}</div>}
          {item.quote && <blockquote style={quoteStyle}>{item.quote}</blockquote>}
        </div>
      ))}
    </div>
  )
}

const btnStyle: React.CSSProperties = { padding: '8px 16px', background: '#1a73e8', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }
const btnOutline: React.CSSProperties = { padding: '8px 16px', background: 'white', color: '#1a73e8', border: '1px solid #1a73e8', borderRadius: 6, cursor: 'pointer', fontSize: 13 }
const btnDanger: React.CSSProperties = { padding: '8px 16px', background: '#b3261e', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13 }
const tabStyle: React.CSSProperties = { padding: '10px 14px', background: 'transparent', border: 'none', borderBottom: '2px solid transparent', cursor: 'pointer', fontSize: 14 }
const tabActive: React.CSSProperties = { ...tabStyle, color: '#1a73e8', borderBottomColor: '#1a73e8', fontWeight: 700 }
const panelStyle: React.CSSProperties = { background: 'white', border: '1px solid #e0e0e0', borderRadius: 8, padding: 16 }
const panelTitle: React.CSSProperties = { margin: '0 0 12px', fontSize: 16 }
const inputStyle: React.CSSProperties = { flex: 1, padding: '7px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 13 }
const fullInputStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 13, boxSizing: 'border-box' }
const smallInputStyle: React.CSSProperties = { width: 96, padding: '7px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 13 }
const textareaStyle: React.CSSProperties = { width: '100%', fontSize: 14, padding: 8, borderRadius: 4, border: '1px solid #aaa', boxSizing: 'border-box' }
const quoteStyle: React.CSSProperties = { margin: '8px 0 0', paddingLeft: 12, borderLeft: '3px solid #ddd', color: '#555', fontSize: 13 }
