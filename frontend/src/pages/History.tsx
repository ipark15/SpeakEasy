import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import { useAuth } from "../hooks/useAuth"
import { getHistory, type HistoryData, type SessionDetail } from "../lib/api"

const MOCK: HistoryData = {
  sessions: [
    { id: "1", type: "General", created_at: "2026-04-24", overall_score: 87, fluency: 89, clarity: 88, rhythm: 84, prosody: 86, voice_quality: 85 },
    { id: "2", type: "Pattern Analysis", created_at: "2026-04-20", overall_score: 82, fluency: 80, clarity: 84, rhythm: 82, prosody: 83, voice_quality: 81 },
    { id: "3", type: "General", created_at: "2026-04-15", overall_score: 79, fluency: 78, clarity: 80, rhythm: 81, prosody: 77, voice_quality: 79 },
    { id: "4", type: "General", created_at: "2026-04-10", overall_score: 76, fluency: 74, clarity: 77, rhythm: 75, prosody: 78, voice_quality: 76 },
    { id: "5", type: "Pattern Analysis", created_at: "2026-04-05", overall_score: 73, fluency: 70, clarity: 74, rhythm: 73, prosody: 74, voice_quality: 74 },
  ],
  improvement: 14,
  best_score: 87,
}

const SUB_SCORE_COLORS: Record<string, string> = {
  fluency: "#c7d2fe",
  clarity: "#bfdbfe",
  rhythm: "#fed7aa",
  prosody: "#d1fae5",
}

function LineChart({ sessions }: { sessions: SessionDetail[] }) {
  if (sessions.length < 2) return null

  const scores = [...sessions].reverse().map((s) => s.overall_score)
  const W = 500
  const H = 80
  const pad = 10

  const min = Math.min(...scores) - 5
  const max = Math.max(...scores) + 5
  const xStep = (W - pad * 2) / (scores.length - 1)

  const points = scores.map((s, i) => ({
    x: pad + i * xStep,
    y: H - pad - ((s - min) / (max - min)) * (H - pad * 2),
  }))

  const polyline = points.map((p) => `${p.x},${p.y}`).join(" ")

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 80 }}>
      <polyline
        points={polyline}
        fill="none"
        stroke="#6366f1"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="4" fill="#6366f1" />
      ))}
    </svg>
  )
}

export default function History() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [data, setData] = useState<HistoryData>(MOCK)

  useEffect(() => {
    if (!user) return
    getHistory(user.id).then(setData).catch(() => {})
  }, [user])

  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      <Navbar />
      <div className="max-w-[760px] mx-auto px-8 py-8 flex flex-col gap-6">

        {/* Back + heading */}
        <div>
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-[13px] text-[#6a7282] hover:text-[#4338ca] transition-colors mb-4"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15,18 9,12 15,6" />
            </svg>
            Back to Dashboard
          </button>
          <p className="text-[11px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-2">History</p>
          <h1 className="text-[32px] font-bold text-[#1e2939] font-['DM_Serif_Display'] leading-tight">
            Your progress.
          </h1>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Sessions", value: data.sessions.length, sub: "Completed" },
            { label: "Improvement", value: `+${data.improvement}`, sub: "Points gained" },
            { label: "Best Score", value: data.best_score, sub: "All time" },
          ].map(({ label, value, sub }) => (
            <Card key={label} className="text-center">
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">{label}</p>
              <p className="text-[30px] font-bold text-[#1e2939]">{value}</p>
              <p className="text-[12px] text-[#9ca3af]">{sub}</p>
            </Card>
          ))}
        </div>

        {/* Performance chart */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Performance</p>
              <h3 className="text-[16px] font-semibold text-[#1e2939]">Performance over time</h3>
            </div>
            <span className="text-[11px] font-medium bg-[#d0fae5] text-[#007a55] rounded-full px-3 py-1">
              +{data.improvement} pts
            </span>
          </div>
          <LineChart sessions={data.sessions} />
        </Card>

        {/* Session list */}
        <div className="flex flex-col gap-3">
          {data.sessions.map((s) => (
            <Card key={s.id} className="p-0 overflow-hidden">
              <div className="p-5">
                {/* Header row */}
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-[15px] font-semibold text-[#1e2939]">{s.type}</p>
                    <p className="text-[12px] text-[#6a7282]">{s.created_at}</p>
                  </div>
                  <span className="text-[28px] font-bold text-[#1e2939]">{s.overall_score}</span>
                </div>

                {/* Sub-scores */}
                <div className="grid grid-cols-4 gap-2">
                  {(["fluency", "clarity", "rhythm", "prosody"] as const).map((key) => (
                    <div
                      key={key}
                      className="rounded-[12px] px-3 py-2 text-center"
                      style={{ background: SUB_SCORE_COLORS[key] ?? "#f3f4f6" }}
                    >
                      <p className="text-[9px] font-semibold tracking-widest uppercase text-[#374151] mb-0.5">
                        {key}
                      </p>
                      <p className="text-[16px] font-bold text-[#1e2939]">{s[key]}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>

      </div>
    </div>
  )
}
