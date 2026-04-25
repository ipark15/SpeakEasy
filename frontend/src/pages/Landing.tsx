import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import Card from "../components/Card"
import Button from "../components/Button"

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
      title: "Daily Tracking",
      description: "Monitor your progress over time with detailed analytics and performance metrics",
      bg: "#c7d2fe",
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
      ),
    },
    {
      title: "AI Coaching",
      description: "Practice with specialized AI coaches tailored to different aspects of speech",
      bg: "#fed7aa",
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ea580c" strokeWidth="2">
          <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
          <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
          <line x1="12" y1="18" x2="12" y2="22"/>
          <line x1="8" y1="22" x2="16" y2="22"/>
        </svg>
      ),
    },
    {
      title: "Smart Analysis",
      description: "Receive detailed insights on fluency, clarity, rhythm, and speaking patterns",
      bg: "#bfdbfe",
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      ),
    },
  ]

  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      {/* Navbar */}
      <nav
        className="h-[85px] px-8 flex items-center"
        style={{ background: "rgba(255,255,255,0.7)", borderBottom: "1px solid rgba(229,231,235,0.4)" }}
      >
        <div className="flex items-end gap-0.5">
          <span className="font-['Outfit'] font-extrabold text-[27px] leading-[27px] text-[#4338ca] tracking-[-0.54px]">
            Speakeas
          </span>
          <svg width="22" height="36" viewBox="0 0 24 36" fill="none">
            <path d="M12 4a3 3 0 0 1 3 3v8a3 3 0 0 1-6 0V7a3 3 0 0 1 3-3z" fill="#4338ca"/>
            <path d="M19 14v1a7 7 0 0 1-14 0v-1" stroke="#4338ca" strokeWidth="2" strokeLinecap="round"/>
            <line x1="12" y1="22" x2="12" y2="28" stroke="#4338ca" strokeWidth="2" strokeLinecap="round"/>
            <line x1="8" y1="28" x2="16" y2="28" stroke="#4338ca" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
      </nav>

      {/* Hero */}
      <div className="flex flex-col items-center justify-center text-center px-6 pt-20 pb-16">
        <h1 className="text-[48px] font-normal leading-[48px] text-[#1e2939] mb-6 tracking-[0.35px]">
          Improve Your Speech with AI
        </h1>
        <p className="text-[18px] leading-[28px] text-[#4a5565] mb-10 max-w-lg tracking-[-0.44px]">
          Get instant, objective feedback on your speaking patterns with our advanced AI analysis
        </p>

        {!showAuth ? (
          <button
            onClick={() => setShowAuth(true)}
            className="flex items-center gap-3 bg-[#4338ca] text-white rounded-[16px] h-[64px] px-12 text-[16px] leading-[24px] tracking-[-0.31px] hover:bg-[#3730a3] transition-colors cursor-pointer"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
              <line x1="12" y1="18" x2="12" y2="22"/>
              <line x1="8" y1="22" x2="16" y2="22"/>
            </svg>
            Get Started
          </button>
        ) : (
          <Card className="w-full max-w-sm text-left">
            <h2 className="text-xl font-semibold text-[#1e2939] mb-6">
              {isSignUp ? "Create account" : "Sign in"}
            </h2>
            <form onSubmit={handleAuth} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm text-[#6a7282] mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#4338ca] transition-colors bg-white"
                  placeholder="you@example.com"
                />
              </div>
              <div>
                <label className="block text-sm text-[#6a7282] mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#4338ca] transition-colors bg-white"
                  placeholder="••••••••"
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button type="submit" disabled={loading} className="w-full h-12">
                {loading ? "Please wait…" : isSignUp ? "Create account" : "Sign in"}
              </Button>
            </form>
            <p className="text-sm text-[#6a7282] mt-4 text-center">
              {isSignUp ? "Already have an account?" : "No account yet?"}{" "}
              <button
                type="button"
                onClick={() => { setIsSignUp(!isSignUp); setError("") }}
                className="text-[#4338ca] hover:underline cursor-pointer"
              >
                {isSignUp ? "Sign in" : "Sign up"}
              </button>
            </p>
          </Card>
        )}
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-0 max-w-[1088px] mx-auto px-6 pb-16"
        style={{ gap: "0px" }}
      >
        {features.map((f, i) => (
          <div
            key={f.title}
            className="rounded-[24px] p-8 h-[226px] flex flex-col"
            style={{
              background: "rgba(255,255,255,0.7)",
              border: "1px solid rgba(229,231,235,0.3)",
              marginLeft: i > 0 ? "16px" : 0,
            }}
          >
            <div
              className="w-14 h-14 rounded-[16px] flex items-center justify-center mb-6"
              style={{ background: f.bg }}
            >
              {f.icon}
            </div>
            <h3 className="text-[20px] font-normal text-[#1e2939] mb-2 tracking-[-0.45px]">{f.title}</h3>
            <p className="text-[14px] leading-[20px] text-[#4a5565] tracking-[-0.15px]">{f.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
