import api from './client'
import type {
  ClientConfig,
  DiarizationOptions,
  Meeting,
  ProcessingStatus,
  Project,
  Requirement,
  RequirementCandidate,
  Speaker,
  TranscriptSegment,
} from '../types'

export const appConfigApi = {
  client: () => api.get<ClientConfig>('/config/client').then(r => r.data),
}

export const projectsApi = {
  list: () => api.get<Project[]>('/projects').then(r => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (data: { name: string; description?: string; client_name?: string; language?: string }) =>
    api.post<Project>('/projects', data).then(r => r.data),
}

export const meetingsApi = {
  list: (projectId: string) => api.get<Meeting[]>(`/meetings/project/${projectId}`).then(r => r.data),
  get: (id: string) => api.get<Meeting>(`/meetings/${id}`).then(r => r.data),
  create: (data: { project_id: string; title: string; meeting_date?: string }) =>
    api.post<Meeting>('/meetings', data).then(r => r.data),
  uploadMedia: (meetingId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/meetings/${meetingId}/media`, form).then(r => r.data)
  },
  process: (meetingId: string, options?: DiarizationOptions) =>
    api.post(`/meetings/${meetingId}/process`, options ?? {}).then(r => r.data),
  rerunDiarization: (meetingId: string, options?: DiarizationOptions) =>
    api.post(`/meetings/${meetingId}/diarization`, options ?? {}).then(r => r.data),
  status: (meetingId: string) => api.get<ProcessingStatus>(`/meetings/${meetingId}/status`).then(r => r.data),
}

export const transcriptApi = {
  get: (meetingId: string) =>
    api.get<TranscriptSegment[]>(`/transcript-segments/meeting/${meetingId}`).then(r => r.data),
  speakers: (meetingId: string) =>
    api.get<Speaker[]>(`/transcript-segments/meeting/${meetingId}/speakers`).then(r => r.data),
  update: (segmentId: string, data: { edited_text?: string; speaker_label?: string }) =>
    api.patch<TranscriptSegment>(`/transcript-segments/${segmentId}`, data).then(r => r.data),
  clear: (meetingId: string) =>
    api.delete(`/transcript-segments/meeting/${meetingId}`).then(r => r.data),
  renameSpeaker: (meetingId: string, speaker_label: string, display_name: string) =>
    api.post(`/transcript-segments/meeting/${meetingId}/rename-speaker`, { speaker_label, display_name }).then(r => r.data),
}

export const requirementsApi = {
  listCandidates: (meetingId: string) =>
    api.get<RequirementCandidate[]>(`/requirements/candidates/meeting/${meetingId}`).then(r => r.data),
  approve: (candidateId: string, data: { actor?: string; business_value?: string; acceptance_criteria?: string }) =>
    api.post<Requirement>(`/requirements/candidates/${candidateId}/approve`, data).then(r => r.data),
  reject: (candidateId: string, reason: string) =>
    api.post(`/requirements/candidates/${candidateId}/reject`, { reason }).then(r => r.data),
  listApproved: (projectId: string) =>
    api.get<Requirement[]>(`/requirements/project/${projectId}`).then(r => r.data),
}

export const exportApi = {
  transcriptMarkdown: (meetingId: string) =>
    api.get(`/export/meeting/${meetingId}/transcript/markdown`, { responseType: 'blob' }).then(r => r.data),
  transcriptTxt: (meetingId: string) =>
    api.get(`/export/meeting/${meetingId}/transcript/txt`, { responseType: 'blob' }).then(r => r.data),
  requirementsMarkdown: (projectId: string) =>
    api.get(`/export/project/${projectId}/requirements/markdown`, { responseType: 'blob' }).then(r => r.data),
}
