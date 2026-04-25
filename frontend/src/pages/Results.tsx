import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { getSession, type SessionData } from "../lib/api"
import Navbar from "../components/Navbar"

const DIMENSIONS = [
  { key: "fluency", label: "Fluency", bg: "rgba(199,210,254,0.4)", color: "#4338ca" },
  { key: "clarity", label: "Clarity", bg: "rgba(191,219,254,0.4)", color: "#0284c7" },
  { key: "rhythm", label: "Rhythm", bg: "rgba(167,243,208,0.4)", color: "#16a34a" },
  { key: "prosody", label: "Prosody", bg: "rgba(254,215,170,0.4)", color: "#ea580c" },
  { key: "voice_quality", label: "Voice Quality", bg: "rgba(233,213,255,0.4)", color: "#7c3aed" },
  { key: "pronunciation", label: "Pronunciation", bg: "rgba(254,202,202,0.4)", color: "#dc2626" },
]

function aggregateScores(session: SessionData): Record<string, number> {
  const totals: Record<string, number[]> = {}
  for (const a of session.assessments) {
    for (const [k, v] of Object.entries(a.scores)) {
      if (k === "overall" || v == null) continue
      if (!totals[k]) totals[k] = []
      totals[k].push(v as number)
    }
  }
  return Object.fromEntries(
    Object.entries(totals).map(([k, vals]) => [k, Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)])
  )
}

function scoreColor(v: number) {
  return v >= 80 ? "#16a34a" : v >= 60 ? "#d97706" : "#dc2626"
}

export default function Results() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) return
    getSession(sessionId).then((s) => {
      setSession(s)
      setLoading(false)
    })
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f5f3ff]">
        <Navbar />
        <div className="flex items-center justify-center h-[80vh]">
          <p className="text-[14px] text-[#6a7282]">Loading results…</p>
        </div>
      </div>
    )
  }

  if (!session) return null

  const overall = session.overall_score ?? 0
  const breakdown = aggregateScores(session)

  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      <Navbar />

      <div className="max-w-xl mx-auto px-6 py-10">

        {/* Header */}
        <p className="text-[11px] font-semibold text-[#6a7282] text-center uppercase tracking-[1.3px] mb-3">
          Analysis Complete
        </p>

        {/* Overall score card */}
        <div
          className="rounded-[24px] p-8 mb-4 flex flex-col items-center"
          style={{ background: "rgba(255,255,255,0.7)", border: "1px solid rgba(229,231,235,0.3)" }}
        >
          <p className="text-[12px] text-[#6a7282] mb-3 tracking-[-0.15px]">Overall Score</p>
          <div className="flex items-end gap-1 mb-1">
            <span
              className="text-[72px] font-normal leading-none tabular-nums"
              style={{ color: scoreColor(overall) }}
            >
              {Math.round(overall)}
            </span>
          </div>
          <p className="text-[12px] text-[#6a7282]">out of 100</p>

          {/* Overall bar */}
          <div className="w-full mt-6">
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${overall}%`, background: scoreColor(overall) }}
              />
            </div>
          </div>
        </div>

        {/* Dimension breakdown */}
        <div
          className="rounded-[24px] p-6 mb-6"
          style={{ background: "rgba(255,255,255,0.7)", border: "1px solid rgba(229,231,235,0.3)" }}
        >
          <p className="text-[11px] font-semibold text-[#6a7282] uppercase tracking-[1.3px] mb-5">Breakdown</p>

          <div className="flex flex-col gap-4">
            {DIMENSIONS.map(({ key, label, color }) => {
              const val = breakdown[key]
              if (val == null) return null
              const c = scoreColor(val)
              return (
                <div key={key}>
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-[14px] text-[#1e2939] tracking-[-0.15px]">{label}</span>
                    <span className="text-[14px] font-medium tabular-nums" style={{ color: c }}>{val}</span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(229,231,235,0.5)" }}>
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${val}%`, background: c }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Score chips row */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {DIMENSIONS.map(({ key, label, bg, color }) => {
            const val = breakdown[key]
            if (val == null) return null
            return (
              <div
                key={key}
                className="rounded-[16px] pt-3 px-3 pb-4"
                style={{ background: bg }}
              >
                <p className="text-[12px] text-[#4a5565] mb-1">{label}</p>
                <p className="text-[20px] font-normal leading-[28px] tabular-nums" style={{ color }}>
                  {val}
                </p>
              </div>
            )
          })}
        </div>

        {/* CTAs */}
        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate("/coach")}
            className="w-full h-14 bg-[#4338ca] text-white rounded-[16px] text-[16px] tracking-[-0.31px] hover:bg-[#3730a3] transition-colors cursor-pointer flex items-center justify-center gap-2"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
            </svg>
            Practice with AI Coach
          </button>
          <button
            onClick={() => navigate("/dashboard")}
            className="w-full h-14 rounded-[16px] text-[16px] text-[#1e2939] tracking-[-0.31px] hover:bg-white/50 transition-colors cursor-pointer flex items-center justify-center"
            style={{ border: "1px solid rgba(209,213,220,0.5)", background: "rgba(255,255,255,0.7)" }}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}
