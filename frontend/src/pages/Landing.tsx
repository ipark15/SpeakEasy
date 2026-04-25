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
      description: "Monitor your speech progress with detailed metrics over time",
      bg: "#c7d2fe",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
      ),
    },
    {
      title: "AI Coaching",
      description: "Get personalized feedback from specialized AI speech coaches",
      bg: "#fed7aa",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ea580c" strokeWidth="2">
          <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
          <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
        </svg>
      ),
    },
    {
      title: "Smart Analysis",
      description: "Deep acoustic analysis of fluency, clarity, rhythm, and more",
      bg: "#bfdbfe",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      ),
    },
  ]

  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      {/* Navbar */}
      <nav
        className="px-6 py-4 flex items-center justify-between"
        style={{ background: "rgba(255,255,255,0.7)", borderBottom: "1px solid rgba(229,231,235,0.5)" }}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-[#4338ca] rounded-lg flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
              <line x1="12" y1="18" x2="12" y2="22"/>
              <line x1="8" y1="22" x2="16" y2="22"/>
            </svg>
          </div>
          <span className="font-['Outfit'] font-extrabold text-xl text-[#1e2939]">SpeakEasy</span>
        </div>
      </nav>

      {/* Hero */}
      <div className="flex flex-col items-center justify-center text-center px-6 pt-20 pb-12">
        <h1 className="text-5xl font-normal text-[#1e2939] mb-4 leading-tight max-w-2xl">
          Improve Your Speech<br />with AI
        </h1>
        <p className="text-lg text-[#4a5565] mb-10 max-w-md">
          Complete a 60-second assessment and get personalized AI coaching to improve your fluency, clarity, and confidence.
        </p>
        {!showAuth ? (
          <Button onClick={() => setShowAuth(true)} className="w-[212px] h-[64px] text-lg">
            Get Started
          </Button>
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
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#4338ca] transition-colors"
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
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[#4338ca] transition-colors"
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto px-6 pb-16">
        {features.map((f) => (
          <Card key={f.title}>
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
              style={{ background: f.bg }}
            >
              {f.icon}
            </div>
            <h3 className="font-semibold text-[#1e2939] mb-1">{f.title}</h3>
            <p className="text-sm text-[#6a7282]">{f.description}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
