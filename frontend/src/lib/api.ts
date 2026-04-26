const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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

export type SessionData = {
  id: string
  user_id: string
  overall_score: number
  assessments: Array<{ task: string; scores: Record<string, number> }>
}

export async function startSession(userId: string): Promise<{ session_id: string }> {
  return post("/api/session/start", { user_id: userId })
}

export async function submitAssessment(form: FormData): Promise<AssessmentResponse> {
  const res = await fetch(`${BASE}/api/assess`, { method: "POST", body: form })
  if (!res.ok) throw new Error(`POST /api/assess → ${res.status}`)
  return res.json()
}

export async function getSession(sessionId: string): Promise<SessionData> {
  return get(`/api/session/${sessionId}`)
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
}

export type HistoryData = {
  sessions: SessionDetail[]
  improvement: number
  best_score: number
}

export async function getHistory(userId: string): Promise<HistoryData> {
  return get(`/api/history/${userId}`)
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
