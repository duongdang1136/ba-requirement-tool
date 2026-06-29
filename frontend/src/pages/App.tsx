import React, { useState, useEffect } from 'react'
import { projectsApi, meetingsApi } from '../api'
import type { Project, Meeting } from '../types'
import UploadPage from './UploadPage'
import TranscriptReview from '../components/transcript/TranscriptReview'

type View = 'projects' | 'meetings' | 'upload' | 'transcript'

export default function App() {
  const [view, setView] = useState<View>('projects')
  const [projects, setProjects] = useState<Project[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [selectedMeetingId, setSelectedMeetingId] = useState<string>('')
  const [selectedMeetingTitle, setSelectedMeetingTitle] = useState<string>('')
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectClient, setNewProjectClient] = useState('')

  useEffect(() => {
    projectsApi.list().then(setProjects)
  }, [])

  async function openProject(project: Project) {
    setSelectedProject(project)
    const m = await meetingsApi.list(project.id)
    setMeetings(m)
    setView('meetings')
  }

  async function createProject(e: React.FormEvent) {
    e.preventDefault()
    const p = await projectsApi.create({ name: newProjectName, client_name: newProjectClient })
    setProjects(prev => [p, ...prev])
    setShowCreateProject(false)
    setNewProjectName('')
    setNewProjectClient('')
  }

  function openTranscript(meeting: Meeting) {
    setSelectedMeetingId(meeting.id)
    setSelectedMeetingTitle(meeting.title)
    setView('transcript')
  }

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', minHeight: '100vh', background: '#f8f9fa' }}>
      {/* Header */}
      <header style={{ background: '#1a73e8', color: 'white', padding: '16px 32px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <h1 style={{ margin: 0, fontSize: 20, cursor: 'pointer' }} onClick={() => setView('projects')}>
          🎙 BA Requirement Tool
        </h1>
        {selectedProject && (
          <>
            <span style={{ opacity: 0.6 }}>/</span>
            <span style={{ cursor: 'pointer', opacity: 0.9 }} onClick={() => setView('meetings')}>
              {selectedProject.name}
            </span>
          </>
        )}
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>

        {/* Projects list */}
        {view === 'projects' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h2 style={{ margin: 0 }}>Projects</h2>
              <button onClick={() => setShowCreateProject(true)} style={btnStyle}>+ New Project</button>
            </div>

            {showCreateProject && (
              <form onSubmit={createProject} style={{ ...cardStyle, marginBottom: 24 }}>
                <input
                  placeholder="Project name"
                  value={newProjectName}
                  onChange={e => setNewProjectName(e.target.value)}
                  style={inputStyle}
                  required
                />
                <input
                  placeholder="Client name (optional)"
                  value={newProjectClient}
                  onChange={e => setNewProjectClient(e.target.value)}
                  style={inputStyle}
                />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="submit" style={btnStyle}>Create</button>
                  <button type="button" onClick={() => setShowCreateProject(false)} style={btnOutline}>Cancel</button>
                </div>
              </form>
            )}

            <div style={{ display: 'grid', gap: 12 }}>
              {projects.map(p => (
                <div key={p.id} style={{ ...cardStyle, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  onClick={() => openProject(p)}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{p.name}</div>
                    {p.client_name && <div style={{ fontSize: 13, color: '#666' }}>Client: {p.client_name}</div>}
                  </div>
                  <span style={{ color: '#1a73e8' }}>→</span>
                </div>
              ))}
              {projects.length === 0 && <p style={{ color: '#888' }}>No projects yet. Create one to start.</p>}
            </div>
          </div>
        )}

        {/* Meetings list */}
        {view === 'meetings' && selectedProject && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h2 style={{ margin: 0 }}>Meetings — {selectedProject.name}</h2>
              <button onClick={() => setView('upload')} style={btnStyle}>+ Upload Meeting</button>
            </div>

            <div style={{ display: 'grid', gap: 12 }}>
              {meetings.map(m => (
                <div key={m.id} style={{ ...cardStyle, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  onClick={() => openTranscript(m)}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{m.title}</div>
                    {m.meeting_date && <div style={{ fontSize: 13, color: '#666' }}>{m.meeting_date}</div>}
                  </div>
                  <span style={{ color: '#1a73e8' }}>View Transcript →</span>
                </div>
              ))}
              {meetings.length === 0 && <p style={{ color: '#888' }}>No meetings yet. Upload one to start.</p>}
            </div>
          </div>
        )}

        {/* Upload */}
        {view === 'upload' && selectedProject && (
          <UploadPage
            projectId={selectedProject.id}
            onMeetingCreated={async (meetingId) => {
              const m = await meetingsApi.list(selectedProject.id)
              setMeetings(m)
              const meeting = m.find(x => x.id === meetingId)
              if (meeting) openTranscript(meeting)
            }}
          />
        )}

        {/* Transcript review */}
        {view === 'transcript' && (
          <TranscriptReview meetingId={selectedMeetingId} meetingTitle={selectedMeetingTitle} />
        )}
      </main>
    </div>
  )
}

const cardStyle: React.CSSProperties = {
  background: 'white',
  border: '1px solid #e0e0e0',
  borderRadius: 10,
  padding: '16px 20px',
}

const btnStyle: React.CSSProperties = {
  padding: '8px 20px',
  background: '#1a73e8',
  color: 'white',
  border: 'none',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 13,
  fontWeight: 600,
}

const btnOutline: React.CSSProperties = {
  padding: '8px 20px',
  background: 'white',
  color: '#1a73e8',
  border: '1px solid #1a73e8',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 13,
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  border: '1px solid #ccc',
  borderRadius: 6,
  fontSize: 14,
  marginBottom: 12,
  boxSizing: 'border-box',
}
