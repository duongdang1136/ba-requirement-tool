export interface Project {
  id: string
  name: string
  description: string
  client_name: string
  status: string
  language: string
  created_at: string
  updated_at: string
}

export interface Meeting {
  id: string
  project_id: string
  title: string
  meeting_date: string | null
  participants: string
  notes: string
  created_at: string
  updated_at: string
}

export interface ProcessingStatus {
  meeting_id: string
  step: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  error: string | null
  started_at: string | null
  finished_at: string | null
}

export interface TranscriptSegment {
  id: string
  meeting_id: string
  start: number
  end: number
  speaker_label: string
  original_text: string
  edited_text: string | null
  display_text: string
  sequence: number
  updated_at: string
}

export interface Speaker {
  speaker_label: string
  display_name: string
}

export interface MeetingSummary {
  id: string
  meeting_id: string
  summary: string
  key_points: string
  model_name: string
  created_at: string
  updated_at: string
}

export interface RewriteSuggestion {
  segment_id: string
  original: string
  suggestion: string
}

export interface Decision {
  id: string
  project_id: string
  meeting_id: string | null
  title: string
  description: string
  owner: string
  source_quote: string
  created_at: string
}

export interface ActionItem {
  id: string
  project_id: string
  meeting_id: string | null
  task: string
  owner: string
  status: string
  source_quote: string
  created_at: string
}

export interface OpenQuestion {
  id: string
  project_id: string
  meeting_id: string | null
  question: string
  owner: string
  status: string
  source_quote: string
  created_at: string
}

export interface MeetingArtifacts {
  summary: MeetingSummary | null
  decisions: Decision[]
  action_items: ActionItem[]
  open_questions: OpenQuestion[]
}

export interface ClientConfig {
  max_upload_size_mb: number
  allowed_extensions: string[]
  upload_chunk_size_mb: number
}

export interface ChunkUploadStatus {
  meeting_id: string
  file_name: string
  total_chunks: number
  received_chunks: number[]
  complete: boolean
}

export interface DiarizationOptions {
  diarization_num_speakers?: number
  diarization_cluster_threshold?: number
}

export interface RequirementCandidate {
  id: string
  meeting_id: string
  title: string
  description: string
  type: RequirementType
  priority: RequirementPriority
  source_quote: string
  source_segment_ids: string
  review_state: 'pending' | 'approved' | 'rejected'
  created_at: string
}

export interface Requirement {
  id: string
  project_id: string
  meeting_id: string
  title: string
  description: string
  type: RequirementType
  priority: RequirementPriority
  status: string
  actor: string
  business_value: string
  acceptance_criteria: string
  source_quote: string
  created_at: string
}

export type RequirementType =
  | 'functional'
  | 'non_functional'
  | 'business_rule'
  | 'data'
  | 'integration'
  | 'reporting'
  | 'permission'
  | 'edge_case'

export type RequirementPriority = 'must' | 'should' | 'could' | 'wont'
