import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import Button from "../components/Button"
import { useAuth } from "../hooks/useAuth"
import { getDashboard, type DashboardData } from "../lib/api"

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

function todayIndex() {
  const d = new Date().getDay()
  return d === 0 ? 6 : d - 1
}

const MOCK: DashboardData = {
  streak: 7,
  best_streak: 15,
  avg_score: 84,
  score_change: 8,
  total_tests: 12,
  last_score: 87,
  last_session_date: "2026-04-24",
  weekly_scores: [
    { day: "Mon", score: 78 },
    { day: "Tue", score: 82 },
    { day: "Wed", score: 85 },
    { day: "Thu", score: 81 },
    { day: "Fri", score: 87 },
    { day: "Sat", score: 84 },
    { day: "Sun", score: 86 },
  ],
  recent_sessions: [
    { id: "1", type: "General", date: "2026-04-24", score: 87 },
    { id: "2", type: "Pattern Analysis", date: "2026-04-20", score: 82 },
    { id: "3", type: "General", date: "2026-04-15", score: 79 },
  ],
}

const QUICK_ACTIONS = [
  {
    label: "View history",
    sub: "All past assessments",
    path: "/history",
    iconBg: "bg-[#c7d2fe]",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
        <circle cx="12" cy="12" r="10" /><polyline points="12,6 12,12 16,14" />
      </svg>
    ),
  },
  {
    label: "My profile",
    sub: "Account & achievements",
    path: "/profile",
    iconBg: "bg-[#fed7aa]",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c2410c" strokeWidth="2">
        <circle cx="12" cy="8" r="4" /><path d="M6 20v-2a6 6 0 0 1 12 0v2" />
      </svg>
    ),
  },
  {
    label: "Settings",
    sub: "Preferences & audio",
    path: "/settings",
    iconBg: "bg-[#bfdbfe]",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" strokeWidth="2">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const today = todayIndex()

  const displayName =
    localStorage.getItem("display_name") ||
    user?.email?.split("@")[0] ||
    "there"

  useEffect(() => {
    if (!user) return
    getDashboard(user.id).then(setData).catch(() => setData(MOCK))
  }, [user])

  if (!data) return (
    <div className="min-h-screen bg-[#f5f3ff]">
      <Navbar />
      <div className="max-w-[1088px] mx-auto px-8 py-8 flex flex-col gap-6">
        <div className="h-8 w-48 rounded-xl bg-[#e0daf7] animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[0,1,2,3].map(i => <div key={i} className="h-28 rounded-[24px] bg-[#e0daf7] animate-pulse" />)}
        </div>
        <div className="h-48 rounded-[24px] bg-[#e0daf7] animate-pulse" />
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-[#f5f3ff] dark:bg-[#0f0e1a]">
      <Navbar />
      <div className="max-w-[1088px] mx-auto px-8 py-8 flex flex-col gap-6">

        {/* Greeting */}
        <div>
          <p className="text-[11px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase mb-2">Dashboard</p>
          <h1 className="text-[32px] font-bold text-[#1e2939] font-['DM_Serif_Display'] leading-tight">
            Welcome back, {displayName}
          </h1>
          <p className="text-[14px] text-[#6a7282] mt-1">Ready to improve your speech today?</p>
        </div>

        {/* 4 Stat cards */}
        <div className="grid grid-cols-4 gap-4">
          {/* Streak */}
          <Card>
            <div className="w-9 h-9 rounded-xl bg-[#fed7aa] flex items-center justify-center mb-3">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#c2410c">
                <path d="M17.66 11.2c-.23-.3-.51-.56-.77-.82-.67-.6-1.43-1.03-2.07-1.66C13.33 7.26 13 4.85 13.95 3c-.95.23-1.78.75-2.49 1.32C8.7 6.45 7.66 9.77 7.9 12.86c.04.5.06 1.01-.08 1.48-.14.47-.43.84-.79 1.14-.2-.93-.21-1.89-.04-2.82C5.34 14.5 4.86 16.81 5 19c.14 2.19 1.23 4.03 3 5.26 1.94 1.36 4.3 1.86 6.53 1.5 2.64-.44 4.97-2.25 6.04-4.72.85-1.95.87-4.31.1-6.31-.45-1.15-1.13-2.12-2.01-2.53z" />
              </svg>
            </div>
            <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Streak</p>
            <div className="flex items-baseline gap-1">
              <span className="text-[30px] font-bold text-[#1e2939]">{data.streak}</span>
              <span className="text-sm text-[#6a7282]">days</span>
            </div>
            <p className="text-[11px] text-[#9ca3af] mt-1">Best: {data.best_streak} days</p>
          </Card>

          {/* Avg Score */}
          <Card>
            <div className="w-9 h-9 rounded-xl bg-[#a5b4fc] flex items-center justify-center mb-3">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                <circle cx="12" cy="8" r="4" /><path d="M6 20v-2a6 6 0 0 1 12 0v2" />
              </svg>
            </div>
            <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Avg Score</p>
            <div className="flex items-baseline gap-1">
              <span className="text-[30px] font-bold text-[#1e2939]">{data.avg_score}</span>
              <span className="text-sm text-[#6a7282]">/100</span>
            </div>
            <span className="inline-block mt-1 text-[11px] font-medium bg-[#d0fae5] text-[#007a55] rounded-full px-2 py-0.5">
              {data.score_change >= 0 ? "+" : ""}{data.score_change}% this month
            </span>
          </Card>

          {/* Total Tests */}
          <Card>
            <div className="w-9 h-9 rounded-xl bg-[#bfdbfe] flex items-center justify-center mb-3">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" strokeWidth="2">
                <circle cx="12" cy="12" r="10" /><polyline points="12,6 12,12 16,14" />
              </svg>
            </div>
            <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Total Tests</p>
            <span className="text-[30px] font-bold text-[#1e2939]">{data.total_tests}</span>
            <p className="text-[11px] text-[#9ca3af] mt-1">Sessions completed</p>
          </Card>

          {/* Last Score */}
          <Card>
            <div className="w-9 h-9 rounded-xl bg-[#fed7aa] flex items-center justify-center mb-3">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c2410c" strokeWidth="2">
                <polyline points="22,7 13.5,15.5 8.5,10.5 2,17" />
                <polyline points="16,7 22,7 22,13" />
              </svg>
            </div>
            <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Last Score</p>
            <span className="text-[30px] font-bold text-[#1e2939]">{data.last_score}</span>
            <p className="text-[11px] text-[#9ca3af] mt-1">{data.last_session_date}</p>
          </Card>
        </div>

        {/* Middle row: chart + actions */}
        <div className="flex gap-4">
          {/* Weekly bar chart */}
          <Card className="flex-[3]">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-xl bg-[#c7d2fe] flex items-center justify-center">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
              </div>
              <div>
                <p className="text-[18px] font-semibold text-[#1e2939]">This Week</p>
                <p className="text-[12px] text-[#6a7282]">Daily performance</p>
              </div>
            </div>
            <div className="flex items-end gap-2" style={{ height: 120 }}>
              {DAYS.map((day, i) => {
                const entry = data.weekly_scores.find((s) => s.day === day)
                const score = entry?.score
                const isToday = i === today
                const heightPct = score ? (score / 100) * 100 : 15
                return (
                  <div key={day} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                    <div
                      className={`w-full rounded-[10px] flex items-center justify-center ${isToday ? "bg-[#6366f1]" : "bg-[#c7d2fe]"}`}
                      style={{ height: `${heightPct}%` }}
                    >
                      <span className={`text-[12px] font-semibold ${isToday ? "text-white" : "text-[#364153]"}`}>
                        {score ?? "—"}
                      </span>
                    </div>
                    <span className={`text-[12px] ${isToday ? "text-[#1e2939] font-semibold" : "text-[#6a7282]"}`}>
                      {day}
                    </span>
                  </div>
                )
              })}
            </div>
          </Card>

          {/* Right action cards */}
          <div className="flex-[2] flex flex-col gap-4">
            <Card>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Assessment</p>
              <h3 className="text-[20px] font-bold text-[#1e2939] mb-1">Start a session</h3>
              <p className="text-[13px] text-[#6a7282] mb-4">3-minute comprehensive speech analysis</p>
              <Button onClick={() => navigate("/assess")} className="w-full flex items-center justify-center gap-2">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                  <line x1="12" y1="18" x2="12" y2="22" />
                </svg>
                Take Assessment
              </Button>
            </Card>
            <Card>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Practice</p>
              <h3 className="text-[20px] font-bold text-[#1e2939] mb-1">AI Coaches</h3>
              <p className="text-[13px] text-[#6a7282] mb-4">Live guided sessions with 4 coaches</p>
              <Button variant="outline" onClick={() => navigate("/coach")} className="w-full flex items-center justify-center gap-2">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                Practice with AI
              </Button>
            </Card>
            <Card>
              <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase mb-1">Therapist</p>
              <h3 className="text-[20px] font-bold text-[#1e2939] mb-1">Talk to Alex</h3>
              <p className="text-[13px] text-[#6a7282] mb-4">Voice session with your AI speech therapist</p>
              <Button onClick={() => navigate("/therapist")} className="w-full flex items-center justify-center gap-2">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                Start Session
              </Button>
            </Card>
          </div>
        </div>

        {/* Bottom row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Recent tests */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[18px] font-semibold text-[#1e2939]">Recent tests</h3>
              <button
                onClick={() => navigate("/history")}
                className="text-[13px] text-[#4338ca] font-medium flex items-center gap-1 hover:underline"
              >
                View all
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="9,18 15,12 9,6" />
                </svg>
              </button>
            </div>
            <div className="flex flex-col gap-2">
              {data.recent_sessions.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between bg-[rgba(245,243,255,0.5)] rounded-[16px] p-3"
                >
                  <div>
                    <p className="text-[14px] font-medium text-[#1e2939]">{s.type}</p>
                    <p className="text-[12px] text-[#6a7282]">{s.date}</p>
                  </div>
                  <span className="text-[24px] font-bold text-[#1e2939]">{s.score}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Quick actions */}
          <Card>
            <h3 className="text-[18px] font-semibold text-[#1e2939] mb-4">Quick actions</h3>
            <div className="flex flex-col gap-3">
              {QUICK_ACTIONS.map(({ label, sub, path, iconBg, icon }) => (
                <button
                  key={path}
                  onClick={() => navigate(path)}
                  className="flex items-center justify-between bg-[rgba(245,243,255,0.5)] rounded-[16px] p-3 hover:bg-[rgba(99,102,241,0.08)] transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-xl ${iconBg} flex items-center justify-center flex-shrink-0`}>
                      {icon}
                    </div>
                    <div>
                      <p className="text-[14px] font-medium text-[#1e2939]">{label}</p>
                      <p className="text-[12px] text-[#6a7282]">{sub}</p>
                    </div>
                  </div>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2.5">
                    <polyline points="9,18 15,12 9,6" />
                  </svg>
                </button>
              ))}
            </div>
          </Card>
        </div>

      </div>
    </div>
  )
}
