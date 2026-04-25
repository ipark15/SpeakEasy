import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { getSession, type SessionData } from "../lib/api"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import Button from "../components/Button"
import ScoreBadge from "../components/ScoreBadge"

const DIMENSIONS: { key: string; label: string }[] = [
  { key: "fluency", label: "Fluency" },
  { key: "clarity", label: "Clarity" },
  { key: "rhythm", label: "Rhythm" },
  { key: "prosody", label: "Prosody" },
  { key: "voice_quality", label: "Voice Quality" },
  { key: "pronunciation", label: "Pronunciation" },
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
          <p className="text-[#6a7282]">Loading results…</p>
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

      <div className="max-w-xl mx-auto px-6 py-12">
        <p className="text-sm text-[#6a7282] text-center mb-2 uppercase tracking-wide">Analysis Complete</p>

        {/* Overall score */}
        <Card className="flex flex-col items-center mb-6">
          <p className="text-sm text-[#6a7282] mb-2">Overall Score</p>
          <ScoreBadge score={overall} size="lg" />
          <p className="text-sm text-[#6a7282] mt-1">out of 100</p>
        </Card>

        {/* Dimension bars */}
        <Card className="mb-8">
          <h2 className="text-sm font-semibold text-[#1e2939] mb-5 uppercase tracking-wide">Breakdown</h2>
          <div className="flex flex-col gap-4">
            {DIMENSIONS.map(({ key, label }) => {
              const val = breakdown[key]
              if (val == null) return null
              const barColor = val >= 80 ? "#16a34a" : val >= 60 ? "#d97706" : "#dc2626"
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-[#1e2939]">{label}</span>
                    <span className="font-medium" style={{ color: barColor }}>{val}</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${val}%`, background: barColor }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        {/* CTAs */}
        <div className="flex flex-col gap-3">
          <Button onClick={() => navigate("/coach")} className="w-full h-12">
            Practice with AI Coach
          </Button>
          <Button onClick={() => navigate("/dashboard")} variant="outline" className="w-full h-12">
            Back to Dashboard
          </Button>
        </div>
      </div>
    </div>
  )
}
