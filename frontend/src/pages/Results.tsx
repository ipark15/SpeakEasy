import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { getSession, type SessionData } from "../lib/api"

const TASK_LABELS: Record<string, string> = {
  read_sentence: "Reading Exercise",
  pataka: "Rhythm Exercise (pa-ta-ka)",
  free_speech: "Free Speech Exercise",
}

const DIMS = [
  { key: "fluency",       label: "FLUENCY",      color: "#4338ca" },
  { key: "rhythm",        label: "RHYTHM",       color: "#0d9488" },
  { key: "clarity",       label: "CLARITY",      color: "#d97706" },
  { key: "pronunciation", label: "PRONOUNCIATION",  color: "#7c3aed" },
  { key: "prosody",       label: "PAUSE",        color: "#16a34a" },
]

function scoreLabel(v: number) {
  return v >= 85 ? "Excellent" : v >= 70 ? "Good" : v >= 55 ? "Fair" : "Needs Work"
}

function scoreColor(v: number) {
  if (v >= 85) return "#16a34a"  // green
  if (v >= 70) return "#65a30d"  // lime
  if (v >= 55) return "#d97706"  // amber
  if (v >= 40) return "#ea580c"  // orange
  return "#dc2626"               // red
}

function heroText(score: number): { heading: string; subtitle: string } {
  if (score >= 85) return {
    heading: "Excellent work!",
    subtitle: "Outstanding performance across all speech dimensions.",
  }
  if (score >= 70) return {
    heading: "Great effort!",
    subtitle: "You're showing strong speech skills — a few areas just need a little polish.",
  }
  if (score >= 55) return {
    heading: "Good progress.",
    subtitle: "Solid foundation here. Targeted practice on the areas below will take you further.",
  }
  if (score >= 40) return {
    heading: "Keep at it.",
    subtitle: "There's real potential. Focus on the suggestions below to build consistency.",
  }
  return {
    heading: "Let's build from here.",
    subtitle: "Every speaker starts somewhere. Use these insights to guide your next session.",
  }
}

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

function ScoreRing({ score, color }: { score: number; color: string }) {
  const r = 50
  const circ = 2 * Math.PI * r
  const filled = (Math.min(score, 100) / 100) * circ
  return (
    <svg width="120" height="120" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="9" />
      <circle cx="60" cy="60" r={r} fill="none"
        stroke={color} strokeWidth="9"
        strokeDasharray={`${filled} ${circ}`}
        strokeLinecap="round"
        transform="rotate(-90 60 60)"
      />
    </svg>
  )
}

function RhythmChart({ intervals }: { intervals: number[] }) {
  if (!intervals || intervals.length < 2) {
    return (
      <div className="h-[160px] flex items-center justify-center text-[13px] text-[#9896b0]">
        No rhythm data available
      </div>
    )
  }
  const W = 560, H = 130, PX = 44, PY = 12
  const msIntervals = intervals.map(v => Math.round(v * 1000))
  const max = Math.max(...msIntervals)
  const min = Math.min(...msIntervals)
  const range = max - min || 1
  const pts = msIntervals.map((v, i) => ({
    x: PX + (i / (msIntervals.length - 1)) * (W - PX * 2),
    y: PY + (1 - (v - min) / range) * (H - PY * 2),
    v,
  }))
  const d = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")
  // ideal consistency band: ±15% of mean
  const mean = msIntervals.reduce((a, b) => a + b, 0) / msIntervals.length
  const bandLow = mean * 0.85, bandHigh = mean * 1.15
  const bandY1 = PY + (1 - (bandHigh - min) / range) * (H - PY * 2)
  const bandY2 = PY + (1 - (bandLow  - min) / range) * (H - PY * 2)
  const yTicks = [min, Math.round((min + max) / 2), max]
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H + 20}`} className="w-full h-[160px]">
        {/* Ideal band */}
        <rect x={PX} y={Math.max(PY, bandY1)} width={W - PX * 2}
          height={Math.min(H - PY, bandY2) - Math.max(PY, bandY1)}
          fill="rgba(16,185,129,0.08)" />
        {/* Grid lines + Y labels */}
        {yTicks.map((ms, i) => {
          const y = PY + (1 - (ms - min) / range) * (H - PY * 2)
          return (
            <g key={i}>
              <line x1={PX} y1={y} x2={W - PX} y2={y} stroke="rgba(99,102,241,0.08)" strokeWidth="1" />
              <text x={PX - 6} y={y + 3.5} textAnchor="end" fontSize="9" fill="#9896b0">{ms}ms</text>
            </g>
          )
        })}
        {/* Line */}
        <path d={d} fill="none" stroke="#4338ca" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {/* Dots */}
        {pts.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3.5" fill="#4338ca" />
        ))}
        {/* X-axis label */}
        <text x={W / 2} y={H + 14} textAnchor="middle" fontSize="9" fill="#9896b0">Syllable number</text>
      </svg>
      {/* Legend + caption */}
      <div className="flex items-center gap-4 mt-2 flex-wrap">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-[#4338ca] rounded" />
          <span className="text-[10px] text-[#6b6b8a]">Syllable interval</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-2 rounded-sm bg-[rgba(16,185,129,0.2)]" />
          <span className="text-[10px] text-[#6b6b8a]">Ideal consistency range (±15%)</span>
        </div>
      </div>
      <p className="text-[11px] text-[#9896b0] mt-2 leading-relaxed">
        Each point is the gap between consecutive pa-ta-ka syllables. A flat line means steady rhythm — spikes show hesitations or rushes.
      </p>
    </div>
  )
}

function generateInsights(breakdown: Record<string, number>) {
  const detected: string[] = []
  const suggestions: string[] = []
  if ((breakdown.fluency ?? 0) >= 70) detected.push("Good speech fluency with consistent word flow")
  else suggestions.push("Work on maintaining a more consistent speaking pace")
  if ((breakdown.prosody ?? 0) >= 70) detected.push("Well-paced pauses with natural breathing points")
  else suggestions.push("Focus on breathing at natural sentence breaks rather than mid-phrase")
  if ((breakdown.rhythm ?? 0) >= 70) detected.push("Consistent rhythm pattern in syllable repetition")
  else suggestions.push("Practice pa-ta-ka exercises to improve rhythm regularity")
  if ((breakdown.clarity ?? 0) >= 70) detected.push("Clear pronunciation with minimal errors")
  else suggestions.push("Slow down and enunciate each syllable more clearly")
  return { detected, suggestions }
}

export default function Results() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) return
    getSession(sessionId).then((s) => { setSession(s); setLoading(false) })
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#edeaf8] flex items-center justify-center">
        <p className="text-[14px] text-[#9896b0]">Loading results…</p>
      </div>
    )
  }
  if (!session) return null

  const overall = Math.round(session.overall_score ?? 0)
  const breakdown = aggregateScores(session)
  const readTask   = session.assessments.find(a => a.task === "read_sentence")
  const patakaTask = session.assessments.find(a => a.task === "pataka")
  const freeTask   = session.assessments.find(a => a.task === "free_speech")
  const rhythmIntervals: number[] = patakaTask?.syllable_intervals ?? []
  const { heading, subtitle } = heroText(overall)

  const { detected, suggestions } = generateInsights(breakdown)

  const TASK_ORDER = [
    { key: "read_sentence", task: readTask },
    { key: "pataka",        task: patakaTask },
    { key: "free_speech",   task: freeTask },
  ]

  return (
    <div className="min-h-screen bg-[#edeaf8] dark:bg-[#0f0e1a]">
      {/* Nav */}
      <nav className="sticky top-0 z-10 sp-nav px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9896b0" strokeWidth="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
          </svg>
          <div>
            <p className="text-[9px] font-bold tracking-[1.5px] text-[#9896b0] uppercase leading-none mb-0.5">Results</p>
            <p className="text-[15px] font-bold text-[#1e1b4b] leading-none">Analysis Complete</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => navigate("/assess")}
            className="flex items-center gap-1.5 px-3 py-2 rounded-[10px] text-[12px] font-semibold text-[#4338ca] border border-[#4338ca] hover:bg-[#f0eeff] transition-colors">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/>
            </svg>
            Try Again
          </button>
          <button onClick={() => navigate("/dashboard")}
            className="flex items-center gap-1.5 px-3 py-2 rounded-[10px] text-[12px] font-semibold text-white bg-[#4338ca] hover:bg-[#3730a3] transition-colors">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            Dashboard
          </button>
        </div>
      </nav>

      <div className="max-w-[720px] mx-auto px-5 py-6 flex flex-col gap-5">

        {/* Hero */}
        <div className="rounded-[24px] p-6 flex items-center gap-6" style={{ background: "#4338ca" }}>
          <div className="relative flex-shrink-0 w-[120px] h-[120px] flex items-center justify-center">
            <ScoreRing score={overall} color={scoreColor(overall)} />
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[34px] font-bold text-white leading-none">{overall}</span>
              <span className="text-[9px] text-[rgba(255,255,255,0.6)] font-bold tracking-wider uppercase mt-1">
                {scoreLabel(overall)}
              </span>
            </div>
          </div>
          <div>
            <p className="text-[9px] font-bold tracking-[1.5px] text-[rgba(255,255,255,0.5)] uppercase mb-1">Overall Score</p>
            <h1 className="text-[28px] font-bold text-white leading-tight mb-1.5" style={{ fontFamily: "'DM Serif Display', serif" }}>
              {heading}
            </h1>
            <p className="text-[13px] text-[rgba(255,255,255,0.65)] leading-relaxed">
              {subtitle}
            </p>
          </div>
        </div>

        {/* Score details */}
        <div className="rounded-[24px] p-6 sp-card">
          <p className="text-[9px] font-bold tracking-[1.5px] text-[#9896b0] uppercase mb-1">Breakdown</p>
          <h2 className="text-[20px] font-bold text-[#1e1b4b] mb-5" style={{ fontFamily: "'DM Serif Display', serif" }}>Score details</h2>

          <div className="grid grid-cols-5 gap-2 mb-5">
            {DIMS.map(({ key, label, color }) => {
              const val = breakdown[key] ?? 0
              const numColor = scoreColor(val)
              return (
                <div key={key} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold tracking-[1.1px]" style={{ color }}>{label}</span>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={numColor} strokeWidth="2.5">
                      <polyline points="18 15 12 9 6 15"/>
                    </svg>
                  </div>
                  <span className="text-[34px] font-bold leading-none" style={{ color: numColor, fontFamily: "'DM Serif Display', serif" }}>{val}</span>
                </div>
              )
            })}
          </div>

          {/* Bar chart — pixel heights so bars are accurate */}
          <div className="flex gap-2">
            {/* Y-axis labels */}
            <div className="relative h-[100px] w-7 flex-shrink-0 text-[9px] text-[#9896b0] text-right">
              {[100, 75, 50, 25, 0].map(v => (
                <span key={v} className="absolute right-0 leading-none"
                  style={{ bottom: `${v}px`, transform: "translateY(50%)" }}>
                  {v}
                </span>
              ))}
            </div>
            {/* Chart area */}
            <div className="flex-1">
              <div className="relative h-[100px]">
                {/* Grid lines at exact px positions */}
                {[100, 75, 50, 25, 0].map(v => (
                  <div key={v} className="absolute w-full border-t border-[rgba(99,102,241,0.1)]"
                    style={{ bottom: `${v}px` }} />
                ))}
                {/* Bars */}
                <div className="absolute inset-0 flex items-end gap-2 px-1">
                  {DIMS.map(({ key, color }) => {
                    const val = breakdown[key] ?? 0
                    return (
                      <div key={key} className="flex-1 rounded-t-[6px] transition-all duration-500"
                        style={{ height: `${val}px`, background: color }} />
                    )
                  })}
                </div>
              </div>
              {/* X-axis labels */}
              <div className="flex gap-2 px-1 mt-1.5">
                {DIMS.map(({ key, label }) => (
                  <span key={key} className="flex-1 text-[8px] text-[#9896b0] text-center leading-tight">{label}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Rhythm pattern */}
        <div className="rounded-[24px] p-6 sp-card">
          <p className="text-[9px] font-bold tracking-[1.5px] text-[#9896b0] uppercase mb-1">Analysis</p>
          <h2 className="text-[20px] font-bold text-[#1e1b4b] mb-3" style={{ fontFamily: "'DM Serif Display', serif" }}>Rhythm pattern</h2>
          <div className="flex items-center gap-1">
            <span className="text-[9px] text-[#9896b0] whitespace-nowrap" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}>
              Time (ms)
            </span>
            <div className="flex-1">
              <RhythmChart intervals={rhythmIntervals} />
            </div>
          </div>
        </div>

        {/* Voice samples */}
        <div className="rounded-[24px] p-6 sp-card">
          <p className="text-[9px] font-bold tracking-[1.5px] text-[#9896b0] uppercase mb-1">Transcripts</p>
          <h2 className="text-[20px] font-bold text-[#1e1b4b] mb-5" style={{ fontFamily: "'DM Serif Display', serif" }}>Voice samples</h2>

          {/* Legend */}
          <div className="flex items-center gap-4 mb-4 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-[rgba(251,191,36,0.3)] text-[#92400e]">word</span>
              <span className="text-[11px] text-[#6b6b8a]">Filler / hesitation (um, uh, like…)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-[rgba(251,191,36,0.15)] text-[#1e1b4b]">word</span>
              <span className="text-[11px] text-[#6b6b8a]">Unclear pronunciation (low confidence)</span>
            </div>
          </div>

          <div className="flex flex-col gap-5">
            {TASK_ORDER.map(({ key, task }, idx) => {
              if (!task) return null
              const fillerSet = new Set((task.filler_words ?? []).map(f => f.word.toLowerCase()))
              const lowSet = new Set((task.low_confidence_words ?? []).map(w => w.word.toLowerCase()))
              const words = task.word_timestamps ?? []
              const transcript = task.transcript ?? ""
              const hasHighlights = words.some(w =>
                fillerSet.has(w.word.toLowerCase()) ||
                lowSet.has(w.word.toLowerCase()) ||
                (w.confidence ?? 1) < 0.7
              )

              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[14px] font-semibold text-[#1e1b4b]">{TASK_LABELS[key]}</p>
                    <span className="text-[10px] font-bold tracking-widest text-[#9896b0]">Exercise {idx + 1}</span>
                  </div>
                  <div className="rounded-[14px] p-4 bg-[rgba(245,243,255,0.6)] text-[14px] leading-8 text-[#1e1b4b]">
                    {words.length > 0 ? (
                      words.map((w, i) => {
                        const isFiller = fillerSet.has(w.word.toLowerCase())
                        const isLow = lowSet.has(w.word.toLowerCase()) || (w.confidence ?? 1) < 0.7
                        return (
                          <span key={i} className="inline-block mr-1">
                            <span className="px-1 rounded"
                              style={{
                                background: isFiller
                                  ? "rgba(251,191,36,0.3)"
                                  : isLow ? "rgba(251,191,36,0.15)"
                                  : "transparent",
                                color: isFiller ? "#92400e" : undefined,
                              }}>
                              {w.word}
                            </span>
                          </span>
                        )
                      })
                    ) : (
                      <span className="text-[#9896b0]">{transcript || "No transcript available"}</span>
                    )}
                  </div>
                  {words.length > 0 && !hasHighlights && (
                    <p className="text-[11px] text-[#16a34a] mt-1.5 flex items-center gap-1">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      All words spoken clearly
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* AI insights */}
        <div className="rounded-[24px] p-6 sp-card">
          <p className="text-[9px] font-bold tracking-[1.5px] text-[#9896b0] uppercase mb-1">Feedback</p>
          <h2 className="text-[20px] font-bold text-[#1e1b4b] mb-5" style={{ fontFamily: "'DM Serif Display', serif" }}>AI insights</h2>

          {detected.length > 0 && (
            <div className="mb-5">
              <p className="text-[9px] font-bold tracking-[1.5px] text-[#9896b0] uppercase mb-3">What we detected</p>
              <ul className="flex flex-col gap-2.5">
                {detected.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-[13px] text-[#1e1b4b]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#4338ca] mt-1.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {suggestions.length > 0 && (
            <div>
              <p className="text-[9px] font-bold tracking-[1.5px] text-[#d97706] uppercase mb-3">Suggestions for improvement</p>
              <ul className="flex flex-col gap-2.5">
                {suggestions.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-[13px] text-[#1e1b4b]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#d97706] mt-1.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Bottom CTAs */}
        <div className="grid grid-cols-2 gap-3 pb-8">
          <button onClick={() => navigate("/assess")}
            className="flex items-center justify-center gap-2 h-[52px] rounded-[16px] text-[14px] font-semibold text-[#4338ca] bg-white border border-[rgba(229,231,235,0.8)] hover:bg-[#f0eeff] transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/>
            </svg>
            Try Again
          </button>
          <button onClick={() => navigate("/dashboard")}
            className="flex items-center justify-center gap-2 h-[52px] rounded-[16px] text-[14px] font-semibold text-[#4338ca] bg-white border border-[rgba(229,231,235,0.8)] hover:bg-[#f0eeff] transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            Go to Dashboard
          </button>
        </div>

      </div>
    </div>
  )
}
