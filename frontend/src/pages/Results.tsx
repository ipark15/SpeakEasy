import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { getSession, type SessionData } from "../lib/api"

const DIMS = [
  { key: "fluency", label: "FLUENCY", color: "#4338ca", bg: "rgba(99,102,241,0.1)" },
  { key: "clarity", label: "CLARITY", color: "#0284c7", bg: "rgba(191,219,254,0.4)" },
  { key: "rhythm", label: "RHYTHM", color: "#16a34a", bg: "rgba(167,243,208,0.4)" },
  { key: "prosody", label: "PAUSE", color: "#ea580c", bg: "rgba(254,215,170,0.4)" },
]

type Tab = "Feedback" | "Breakdown" | "AI Insights"

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

function scoreLabel(v: number) {
  return v >= 85 ? "Excellent" : v >= 70 ? "Good" : v >= 55 ? "Fair" : "Needs Work"
}

function scoreColor(v: number) {
  return v >= 80 ? "#16a34a" : v >= 60 ? "#d97706" : "#dc2626"
}

export default function Results() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>("Feedback")

  useEffect(() => {
    if (!sessionId) return
    getSession(sessionId).then((s) => { setSession(s); setLoading(false) })
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#edeaf8] flex items-center justify-center">
        <p className="font-['Outfit'] text-[14px] text-[#9896b0]">Loading results…</p>
      </div>
    )
  }
  if (!session) return null

  const overall = session.overall_score ?? 0
  const breakdown = aggregateScores(session)
  const tabs: Tab[] = ["Feedback", "Breakdown", "AI Insights"]

  return (
    <div className="min-h-screen bg-[#edeaf8] flex flex-col">
      {/* Nav */}
      <nav className="h-[74px] px-8 flex items-center justify-between max-w-[1100px] mx-auto w-full"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.6)" }}>
        <button onClick={() => navigate("/assess")}
          className="flex items-center gap-2 font-['Outfit'] font-bold text-[13px] text-[#4338ca] cursor-pointer hover:opacity-70 transition-opacity">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Try Again
        </button>
        <button onClick={() => navigate("/dashboard")}
          className="bg-[#4338ca] text-white font-['Outfit'] font-bold text-[13px] h-[38px] px-5 rounded-[12px] cursor-pointer hover:bg-[#3730a3] transition-colors"
          style={{ boxShadow: "0px 4px 8px rgba(67,56,202,0.28)" }}>
          Dashboard
        </button>
      </nav>

      <div className="max-w-[1100px] mx-auto px-8 py-12 w-full">
        {/* Header */}
        <p className="font-['Outfit'] font-bold text-[11px] text-[#9896b0] tracking-[1.32px] uppercase text-center mb-4">
          Analysis Complete
        </p>
        <h1 className="font-['DM_Serif_Display'] text-[48px] text-[#1e1b4b] text-center mb-2">Excellent work!</h1>
        <p className="font-['Outfit'] font-normal text-[16px] text-[#6b6b8a] text-center mb-10">
          Outstanding performance across all speech dimensions.
        </p>

        {/* Overall score + dim chips */}
        <div className="flex flex-col items-center mb-10">
          <div className="rounded-[28px] p-10 w-full max-w-xl text-center mb-6"
            style={{ background: "rgba(255,255,255,0.82)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 4px 12px rgba(99,102,241,0.08)" }}>
            <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1.2px] uppercase mb-3">Overall Score</p>
            <p className="font-['DM_Serif_Display'] text-[80px] leading-none mb-1" style={{ color: scoreColor(overall) }}>
              {Math.round(overall)}
            </p>
            <p className="font-['Outfit'] font-semibold text-[13px] text-[#9896b0] mb-8">{scoreLabel(overall)}</p>

            {/* Score bar */}
            <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(99,102,241,0.1)" }}>
              <div className="h-full rounded-full transition-all duration-700"
                style={{ width: `${overall}%`, background: "linear-gradient(90deg, #6366f1, #4338ca)" }} />
            </div>
          </div>

          {/* Dimension chips */}
          <div className="flex gap-3 w-full max-w-xl">
            {DIMS.map(({ key, label, color, bg }) => {
              const val = breakdown[key]
              return (
                <div key={key} className="flex-1 rounded-[18px] p-4" style={{ background: bg }}>
                  <p className="font-['Outfit'] font-bold text-[10px] tracking-[1.1px] uppercase mb-2" style={{ color }}>{label}</p>
                  <p className="font-['DM_Serif_Display'] text-[28px]" style={{ color }}>
                    {val ?? "—"}
                  </p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Tabs */}
        <div className="rounded-[28px] overflow-hidden"
          style={{ background: "rgba(255,255,255,0.82)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 4px 12px rgba(99,102,241,0.08)" }}>
          {/* Tab bar */}
          <div className="flex border-b" style={{ borderColor: "rgba(99,102,241,0.08)" }}>
            {tabs.map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className="flex-1 h-14 font-['Outfit'] font-semibold text-[13px] cursor-pointer transition-colors"
                style={{
                  color: tab === t ? "#4338ca" : "#9896b0",
                  borderBottom: tab === t ? "2px solid #4338ca" : "2px solid transparent",
                  background: "transparent",
                }}>
                {t}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-8">
            {tab === "Feedback" && (
              <div>
                <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1.2px] uppercase mb-4">What we detected</p>
                <div className="flex flex-col gap-3">
                  {DIMS.map(({ key, label, color, bg }) => {
                    const val = breakdown[key]
                    if (val == null) return null
                    return (
                      <div key={key} className="flex items-center justify-between rounded-[16px] p-4" style={{ background: bg }}>
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                          <p className="font-['Outfit'] font-semibold text-[14px]" style={{ color }}>{label}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="w-32 h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.6)" }}>
                            <div className="h-full rounded-full" style={{ width: `${val}%`, background: color }} />
                          </div>
                          <p className="font-['DM_Serif_Display'] text-[20px] w-10 text-right" style={{ color }}>{val}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {tab === "Breakdown" && (
              <div className="flex flex-col gap-5">
                {Object.entries(breakdown).map(([key, val]) => {
                  const c = scoreColor(val)
                  return (
                    <div key={key}>
                      <div className="flex justify-between mb-2">
                        <p className="font-['Outfit'] font-semibold text-[14px] text-[#1e1b4b] capitalize">{key.replace("_", " ")}</p>
                        <p className="font-['Outfit'] font-bold text-[14px]" style={{ color: c }}>{val}</p>
                      </div>
                      <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(99,102,241,0.08)" }}>
                        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${val}%`, background: c }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {tab === "AI Insights" && (
              <div className="text-center py-8">
                <p className="font-['DM_Serif_Display'] text-[24px] text-[#1e1b4b] mb-3">AI coaching is ready</p>
                <p className="font-['Outfit'] font-normal text-[14px] text-[#6b6b8a] mb-8 max-w-sm mx-auto">
                  Pick a specialized AI coach to work on your specific areas of improvement.
                </p>
                <button onClick={() => navigate("/coach")}
                  className="bg-[#4338ca] text-white font-['Outfit'] font-semibold text-[15px] h-[54px] px-10 rounded-[18px] cursor-pointer hover:bg-[#3730a3] transition-colors"
                  style={{ boxShadow: "0px 6px 12px rgba(67,56,202,0.28)" }}>
                  Choose a Coach
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
