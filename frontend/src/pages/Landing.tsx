import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"

export default function Landing() {
  const navigate = useNavigate()
  const { user, signIn, signUp } = useAuth()
  const [showAuth, setShowAuth] = useState(false)
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  if (user) {
    navigate("/dashboard")
    return null
  }

  async function handleAuth(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    const { error: authError } = isSignUp
      ? await signUp(email, password)
      : await signIn(email, password)
    setLoading(false)
    if (authError) {
      setError(authError.message)
    } else {
      navigate("/dashboard")
    }
  }

  const features = [
    {
      label: "SPEECH METRICS",
      title: "Deep Analysis",
      desc: "Fluency, clarity, rhythm, and pacing — scored objectively on every recording.",
      iconBg: "#eef2ff",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
      ),
    },
    {
      label: "AI COACHING",
      title: "4 Specialized Coaches",
      desc: "Flow Master, Rhythm Keeper, Clarity Coach, and Articulation Artist.",
      iconBg: "#fff7ed",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ea580c" strokeWidth="2">
          <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
          <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
        </svg>
      ),
    },
    {
      label: "LIVE FEEDBACK",
      title: "Color-Coded Transcripts",
      desc: "See exactly where you stumble with highlighted mistakes and hover-to-hear playback.",
      iconBg: "#eff6ff",
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      ),
    },
  ]

  const stats = [
    { value: "94%", label: "ACCURACY RATE" },
    { value: "3 min", label: "TO COMPLETE" },
    { value: "12+", label: "SPEECH METRICS" },
  ]

  return (
    <div className="min-h-screen bg-[#edeaf8]">
      {/* Nav */}
      <nav className="h-[82px] px-8 flex items-center justify-between"
        style={{ background: "rgba(255,255,255,0.55)", borderBottom: "1px solid rgba(255,255,255,0.6)" }}>
        <div className="flex items-end gap-0.5">
          <span className="font-['Outfit'] font-extrabold text-[27px] leading-[27px] text-[#4338ca] tracking-[-0.54px]">Speakeas</span>
          <svg width="22" height="36" viewBox="0 0 22 29" fill="none">
            <path d="M11 3a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z" fill="#4338ca"/>
            <path d="M18 13v1a7 7 0 0 1-14 0v-1" stroke="#4338ca" strokeWidth="2" strokeLinecap="round"/>
            <line x1="11" y1="21" x2="11" y2="27" stroke="#4338ca" strokeWidth="2" strokeLinecap="round"/>
            <line x1="7" y1="27" x2="15" y2="27" stroke="#4338ca" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <button
          onClick={() => setShowAuth(true)}
          className="bg-[#4338ca] text-white font-['Outfit'] font-semibold text-[14px] h-[41px] px-5 rounded-[14px] cursor-pointer hover:bg-[#3730a3] transition-colors"
        >
          Get Started
        </button>
      </nav>

      {/* Hero */}
      <div className="max-w-[1152px] mx-auto px-8 pt-16 pb-20 flex items-start gap-16">
        {/* Left */}
        <div className="flex-1 pt-16">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 h-[28px] px-3 rounded-[40px] mb-14"
            style={{ background: "rgba(99,102,241,0.12)" }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="#6366f1">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" stroke="#6366f1" strokeWidth="2" fill="none"/>
            </svg>
            <span className="font-['Outfit'] font-bold text-[11px] text-[#6366f1] tracking-[1.1px] uppercase">AI-Powered Analysis</span>
          </div>

          {/* Heading */}
          <h1 className="font-['DM_Serif_Display'] text-[76px] leading-[79.8px] text-[#1e1b4b] mb-8">
            Speak<br />
            <span className="text-[#4338ca]">with</span>{" "}confidence.
          </h1>

          {/* Subtitle */}
          <p className="font-['Outfit'] font-normal text-[17px] leading-[28px] text-[#6b6b8a] max-w-[400px] mb-12">
            Record a short speech sample and get instant, objective scores on fluency, clarity, rhythm, and pacing — powered by AI.
          </p>

          {/* CTA */}
          {!showAuth ? (
            <div className="flex items-center gap-4 mb-14">
              <button
                onClick={() => setShowAuth(true)}
                className="flex items-center gap-2 bg-[#4338ca] text-white font-['Outfit'] font-semibold text-[16px] h-[56px] px-8 rounded-[18px] cursor-pointer hover:bg-[#3730a3] transition-colors"
                style={{ boxShadow: "0px 8px 16px rgba(67,56,202,0.32)" }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                  <line x1="12" y1="18" x2="12" y2="22"/>
                  <line x1="8" y1="22" x2="16" y2="22"/>
                </svg>
                Start Assessment
              </button>
              <span className="font-['Outfit'] font-medium text-[13px] text-[#9896b0]">Free · No account needed</span>
            </div>
          ) : (
            <div
              className="rounded-[28px] p-8 mb-14 max-w-sm"
              style={{ background: "rgba(255,255,255,0.82)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 4px 12px rgba(99,102,241,0.08)" }}
            >
              <h2 className="font-['DM_Serif_Display'] text-[24px] text-[#1e1b4b] mb-6">
                {isSignUp ? "Create account" : "Sign in"}
              </h2>
              <form onSubmit={handleAuth} className="flex flex-col gap-4">
                <div>
                  <label className="block font-['Outfit'] text-[13px] text-[#9896b0] mb-1">Email</label>
                  <input
                    type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                    className="w-full bg-[#f8f7ff] rounded-[14px] px-4 py-3 font-['Outfit'] text-[14px] text-[#1e1b4b] outline-none focus:ring-2 focus:ring-[#4338ca]/20 border-0"
                    placeholder="you@example.com"
                  />
                </div>
                <div>
                  <label className="block font-['Outfit'] text-[13px] text-[#9896b0] mb-1">Password</label>
                  <input
                    type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                    className="w-full bg-[#f8f7ff] rounded-[14px] px-4 py-3 font-['Outfit'] text-[14px] text-[#1e1b4b] outline-none focus:ring-2 focus:ring-[#4338ca]/20 border-0"
                    placeholder="••••••••"
                  />
                </div>
                {error && <p className="font-['Outfit'] text-sm text-red-500">{error}</p>}
                <button
                  type="submit" disabled={loading}
                  className="w-full h-[54px] bg-[#4338ca] text-white font-['Outfit'] font-semibold text-[15px] rounded-[18px] cursor-pointer hover:bg-[#3730a3] transition-colors disabled:opacity-50"
                  style={{ boxShadow: "0px 6px 12px rgba(67,56,202,0.28)" }}
                >
                  {loading ? "Please wait…" : isSignUp ? "Create account" : "Sign in"}
                </button>
              </form>
              <p className="font-['Outfit'] text-[13px] text-[#9896b0] mt-4 text-center">
                {isSignUp ? "Already have an account?" : "No account yet?"}{" "}
                <button type="button" onClick={() => { setIsSignUp(!isSignUp); setError("") }}
                  className="text-[#4338ca] hover:underline cursor-pointer">
                  {isSignUp ? "Sign in" : "Sign up"}
                </button>
              </p>
            </div>
          )}

          {/* Stats */}
          <div className="flex gap-8">
            {stats.map((s) => (
              <div key={s.label}>
                <p className="font-['DM_Serif_Display'] text-[26px] text-[#1e1b4b] leading-[26px]">{s.value}</p>
                <p className="font-['Outfit'] font-semibold text-[10px] text-[#9896b0] tracking-[1px] uppercase mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right — decorative mockup */}
        <div className="w-[520px] shrink-0 relative h-[480px] hidden lg:block">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="absolute w-[360px] h-[360px] rounded-[180px] bg-[rgba(99,102,241,0.07)] left-[80px] top-[60px]" />
            <div className="absolute w-[240px] h-[240px] rounded-[120px] bg-[rgba(99,102,241,0.06)] left-[140px] top-[120px]" />
          </div>
          {/* Fluency card */}
          <div className="absolute left-[120px] top-[0px] w-[280px] h-[161px] rounded-[28px] flex flex-col justify-between p-6"
            style={{ background: "linear-gradient(158deg, #5b4fcf 6%, #4338ca 94%)", boxShadow: "0px 20px 30px rgba(67,56,202,0.38)" }}>
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 bg-white/95 rounded-[22px] flex items-center justify-center" style={{ boxShadow: "0px 4px 8px rgba(0,0,0,0.12)" }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                  <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                </svg>
              </div>
              <div className="flex gap-1 opacity-60">
                {[12,20,14,28,18,24,10,22,16,26].map((h, i) => (
                  <div key={i} className="w-[3px] rounded-[4px] bg-white/70" style={{ height: h }} />
                ))}
              </div>
            </div>
            <div>
              <p className="font-['DM_Serif_Display'] text-[28px] text-white leading-[30px]">Fluency Score</p>
              <p className="font-['Outfit'] font-semibold text-[11px] tracking-[1.1px] uppercase mt-1" style={{ color: "rgba(200,195,255,0.9)" }}>Achievement unlocked</p>
            </div>
          </div>
          {/* Dashboard card */}
          <div className="absolute left-[110px] top-[170px] w-[300px] rounded-[28px] p-5"
            style={{ background: "rgba(255,255,255,0.92)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 12px 24px rgba(99,102,241,0.12)" }}>
            <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1.2px] uppercase mb-3">Dashboard</p>
            <div className="flex gap-3 mb-3">
              <div className="flex-1 bg-[#f8f7ff] rounded-[18px] p-4">
                <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1px] uppercase mb-2">Current Streak</p>
                <div className="flex items-baseline gap-1">
                  <span className="font-['DM_Serif_Display'] text-[36px] text-[#1e1b4b]">7</span>
                  <span className="font-['Outfit'] font-medium text-[14px] text-[#6b6b8a]">days</span>
                </div>
              </div>
              <div className="flex-1 bg-[#f8f7ff] rounded-[18px] p-4">
                <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1px] uppercase mb-2">Avg Score</p>
                <div className="flex items-baseline gap-1">
                  <span className="font-['DM_Serif_Display'] text-[36px] text-[#1e1b4b]">84</span>
                  <span className="font-['Outfit'] font-medium text-[14px] text-[#6b6b8a]">/100</span>
                </div>
              </div>
            </div>
            <div className="bg-[#f8f7ff] rounded-[18px] p-4">
              <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1px] uppercase mb-2">Sessions completed</p>
              <div className="flex items-center gap-3">
                <span className="font-['DM_Serif_Display'] text-[34px] text-[#1e1b4b]">12</span>
                <div className="flex gap-1">
                  {[0,0,0,0,1,0,0].map((active, i) => (
                    <div key={i} className="w-1.5 h-1.5 rounded-full" style={{ background: active ? "#4338ca" : "#d4d0ee" }} />
                  ))}
                </div>
              </div>
            </div>
          </div>
          {/* Improvement chip */}
          <div className="absolute left-[370px] top-[308px] w-[150px] rounded-[24px] p-5"
            style={{ background: "rgba(255,255,255,0.92)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 8px 16px rgba(99,102,241,0.14)" }}>
            <div className="w-10 h-10 rounded-[20px] flex items-center justify-center mb-4"
              style={{ background: "linear-gradient(135deg, #fdba74 0%, #fb923c 100%)", boxShadow: "0px 4px 8px rgba(251,146,60,0.3)" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
              </svg>
            </div>
            <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1px] uppercase mb-1">Improvement</p>
            <p className="font-['DM_Serif_Display'] text-[28px] text-[#1e1b4b]">+18%</p>
            <p className="font-['Outfit'] font-medium text-[10px] text-[#b5b3cc]">This week</p>
          </div>
          {/* AI Feedback pill */}
          <div className="absolute left-0 top-[110px] flex items-center gap-2 h-[52px] px-4 rounded-[16px]"
            style={{ background: "rgba(255,255,255,0.92)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 6px 12px rgba(99,102,241,0.12)" }}>
            <div className="w-7 h-7 bg-[#eef2ff] rounded-[14px] flex items-center justify-center">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
              </svg>
            </div>
            <div>
              <p className="font-['Outfit'] font-bold text-[11px] text-[#1e1b4b]">AI Feedback</p>
              <p className="font-['Outfit'] font-medium text-[9px] text-[#9896b0]">Ready</p>
            </div>
          </div>
        </div>
      </div>

      {/* Features section */}
      <div className="max-w-[1152px] mx-auto px-8 pb-20">
        <p className="font-['Outfit'] font-bold text-[11px] text-[#9896b0] tracking-[1.32px] uppercase text-center mb-3">What you get</p>
        <h2 className="font-['DM_Serif_Display'] text-[50px] text-[#1e1b4b] text-center leading-[75px] mb-12">
          Everything you need<br />to improve
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {features.map((f) => (
            <div key={f.label} className="rounded-[28px] p-7"
              style={{ background: "rgba(255,255,255,0.8)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 4px 12px rgba(99,102,241,0.08)" }}>
              <div className="w-12 h-12 rounded-[16px] flex items-center justify-center mb-10" style={{ background: f.iconBg }}>
                {f.icon}
              </div>
              <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1.2px] uppercase mb-2">{f.label}</p>
              <p className="font-['DM_Serif_Display'] text-[24px] text-[#1e1b4b] mb-3">{f.title}</p>
              <p className="font-['Outfit'] font-normal text-[14px] leading-[22px] text-[#6b6b8a]">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA banner */}
      <div className="max-w-[1088px] mx-auto mb-20 rounded-[32px] overflow-hidden px-8 py-20 text-center relative"
        style={{ background: "linear-gradient(157deg, #4338ca 0%, #5b4fcf 60%, #6d64d6 100%)", boxShadow: "0px 24px 80px rgba(67,56,202,0.35)" }}>
        <div className="absolute top-[-80px] right-[-50px] w-[300px] h-[300px] rounded-[150px] bg-white/[0.04]" />
        <div className="absolute bottom-[-81px] left-[-40px] w-[200px] h-[200px] rounded-[100px] bg-white/[0.05]" />
        <p className="font-['Outfit'] font-bold text-[11px] tracking-[1.32px] uppercase mb-8" style={{ color: "rgba(200,195,255,0.85)" }}>Start today</p>
        <h2 className="font-['DM_Serif_Display'] text-[54px] text-white leading-[59px] mb-6">
          Your voice deserves<br />to be heard clearly.
        </h2>
        <p className="font-['Outfit'] font-normal text-[16px] leading-[26px] mb-12 max-w-[400px] mx-auto" style={{ color: "rgba(200,195,255,0.85)" }}>
          Take a 3-minute assessment and discover exactly what to work on.
        </p>
        <button
          onClick={() => setShowAuth(true)}
          className="flex items-center gap-2 bg-white text-[#4338ca] font-['Outfit'] font-bold text-[16px] h-[56px] px-10 rounded-[18px] mx-auto cursor-pointer hover:bg-white/90 transition-colors"
          style={{ boxShadow: "0px 8px 16px rgba(0,0,0,0.15)" }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
            <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
            <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
            <line x1="8" y1="22" x2="16" y2="22"/>
          </svg>
          Begin My Assessment
        </button>
      </div>
    </div>
  )
}
