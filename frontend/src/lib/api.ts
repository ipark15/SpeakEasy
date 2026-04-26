const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

let _getToken: (() => Promise<string>) | null = null

export function setApiTokenProvider(fn: () => Promise<string>) {
  _getToken = fn
}

async function authHeaders(): Promise<Record<string, string>> {
  if (!_getToken) return {}
  try {
    const token = await _getToken()
    return { Authorization: `Bearer ${token}` }
  } catch {
    return {}
  }
}

async function get<T>(path: string): Promise<T> {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}${path}`, { headers })
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

// ── Session / Assessment ────────────────────────────────────────────────────

export type AssessmentResponse = {
  task: string
  scores: Record<string, number>
}

export type WordTimestamp = {
  word: string
  start: number
  end: number
  confidence?: number
}

export type PauseEvent = {
  start: number
  end: number
  duration: number
}

export type FillerEvent = {
  word: string
  start: number
  end: number
}

export type LowConfWord = {
  word: string
  confidence: number
  time: number
}

export type Assessment = {
  id: string
  task: string
  scores: Record<string, number | null>
  transcript?: string
  word_timestamps?: WordTimestamp[]
  syllable_intervals?: number[]
  filler_words?: FillerEvent[]
  low_confidence_words?: LowConfWord[]
  pauses?: PauseEvent[]
  pitch_contour?: number[]
  pitch_times?: number[]
  wpm?: number | null
  ddk_rate?: number | null
  word_error_rate?: number | null
  tips?: string[]
}

export type SessionData = {
  id: string
  user_id: string
  overall_score: number
  assessments: Array<{
    task: string
    score_fluency: number | null
    score_clarity: number | null
    score_rhythm: number | null
    score_prosody: number | null
    score_pronunciation: number | null
    score_overall: number | null
    [key: string]: unknown
  }>
}

export async function startSession(userId: string): Promise<{ session_id: string }> {
  return post("/api/session/start", { user_id: userId })
}

export async function submitAssessment(form: FormData): Promise<AssessmentResponse> {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}/api/assess`, { method: "POST", headers, body: form })
  if (!res.ok) throw new Error(`POST /api/assess → ${res.status}`)
  return res.json()
}

export async function getSession(sessionId: string): Promise<SessionData> {
  return get(`/api/session/${sessionId}`)
}

export async function downloadReport(sessionId: string): Promise<void> {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}/api/report/${sessionId}`, { headers })
  if (!res.ok) throw new Error(`GET /api/report/${sessionId} → ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `speech_report_${sessionId.slice(0, 8)}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

// ── Dashboard ───────────────────────────────────────────────────────────────

export type WeeklyScore = { day: string; score: number | null }
export type RecentSession = { id: string; type: string; date: string; score: number }

export type DashboardData = {
  streak: number
  best_streak: number
  avg_score: number
  score_change: number
  total_tests: number
  last_score: number
  last_session_date: string
  weekly_scores: WeeklyScore[]
  recent_sessions: RecentSession[]
}

export async function getDashboard(userId: string): Promise<DashboardData> {
  return get(`/api/dashboard/${userId}`)
}

// ── History ─────────────────────────────────────────────────────────────────

export type SessionDetail = {
  id: string
  type: string
  created_at: string
  overall_score: number
  fluency: number
  clarity: number
  rhythm: number
  prosody: number
  voice_quality: number
  pronunciation: number
}

export type HistoryData = {
  sessions: SessionDetail[]
  improvement: number
  best_score: number
}

export async function getHistory(userId: string): Promise<HistoryData> {
  return get(`/api/history/${userId}`)
}

export type ReportMeta = { session_id: string; generated_at: string; summary: string }

export async function getUserReports(userId: string): Promise<ReportMeta[]> {
  return get(`/api/reports/${userId}`)
}

// ── Profile ─────────────────────────────────────────────────────────────────

export type ProfileData = {
  full_name: string
  email: string
  joined_at: string
  best_score: number
  improvement: number
  total_tests: number
}

export async function getProfile(userId: string): Promise<ProfileData> {
  return get(`/api/profile/${userId}`)
}

export async function updateProfile(userId: string, data: { full_name: string }): Promise<void> {
  return post("/api/profile", { user_id: userId, display_name: data.full_name })
}

// ── WebSocket ────────────────────────────────────────────────────────────────

export function coachWebSocket(sessionId: string): WebSocket {
  const wsBase = BASE.replace(/^http/, "ws")
  return new WebSocket(`${wsBase}/ws/coach/${sessionId}`)
}
