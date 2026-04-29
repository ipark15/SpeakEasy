import { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"

export default function Auth() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { user, signIn, signUp } = useAuth()

  const [isSignUp, setIsSignUp] = useState(params.get("mode") === "signup")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true })
  }, [user])

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

  return (
    <div className="min-h-screen bg-[#edeaf8] flex flex-col">
      {/* Nav */}
      <nav
        className="h-[74px] px-8 flex items-center justify-between shrink-0"
        style={{ background: "rgba(255,255,255,0.55)", borderBottom: "1px solid rgba(255,255,255,0.6)" }}
      >
        <button
          onClick={() => navigate("/")}
          className="flex items-end gap-0.5 cursor-pointer hover:opacity-80 transition-opacity"
        >
          <span className="font-['Quicksand'] font-extrabold text-[27px] leading-[27px] text-[#4338ca] tracking-[-0.54px]">speakeas</span>
          <svg className="-ml-1" width="15" height="33" viewBox="0 0 22 27" fill="none">
            <path d="M11 3a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z" fill="#A8A9AD"/>
            <path d="M18 13v1a7 7 0 0 1-14 0v-1" stroke="#4338ca" strokeWidth="4" strokeLinecap="round"/>
            <line x1="11" y1="21" x2="11" y2="32" stroke="#4338ca" strokeWidth="4" strokeLinecap="round"/>
          </svg>
        </button>
        <p className="font-['Quicksand'] text-[13px] text-[#9896b0]">
          {isSignUp ? "Already have an account?" : "New here?"}{" "}
          <button
            onClick={() => { setIsSignUp(!isSignUp); setError("") }}
            className="text-[#4338ca] font-semibold hover:underline cursor-pointer"
          >
            {isSignUp ? "Sign in" : "Sign up"}
          </button>
        </p>
      </nav>

      {/* Body */}
      <div className="flex-1 flex items-center justify-center px-8 py-16">
        <div className="w-full max-w-[420px]">

          {/* Header */}
          <div className="mb-8 text-center">
            <div
              className="inline-flex items-center gap-2 h-[28px] px-3 rounded-[40px] mb-6"
              style={{ background: "rgba(99,102,241,0.12)" }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="#6366f1">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1" stroke="#6366f1" strokeWidth="2" fill="none" />
              </svg>
              <span className="font-['Quicksand'] font-bold text-[11px] text-[#6366f1] tracking-[1.1px] uppercase">
                AI-Powered Analysis
              </span>
            </div>
            <h1 className="font-['Quicksand'] font-extrabold text-[38px] leading-[42px] text-[#1e1b4b] mb-3">
              {isSignUp ? "Create your account." : "Welcome back."}
            </h1>
            <p className="font-['Quicksand'] font-normal text-[15px] text-[#6b6b8a]">
              {isSignUp
                ? "Start improving your speech today."
                : "Sign in to continue your progress."}
            </p>
          </div>

          {/* Card */}
          <div
            className="rounded-[28px] p-8"
            style={{
              background: "rgba(255,255,255,0.82)",
              border: "1px solid rgba(255,255,255,0.9)",
              boxShadow: "0px 4px 24px rgba(99,102,241,0.10)",
            }}
          >
            <form onSubmit={handleAuth} className="flex flex-col gap-5">
              <div>
                <label className="block font-['Quicksand'] font-semibold text-[12px] text-[#9896b0] tracking-[0.8px] uppercase mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  className="w-full bg-[#f8f7ff] rounded-[14px] px-4 py-3 font-['Quicksand'] text-[14px] text-[#1e1b4b] outline-none transition-all"
                  style={{ border: "1.5px solid rgba(229,231,235,0.8)" }}
                  onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
                />
              </div>

              <div>
                <label className="block font-['Quicksand'] font-semibold text-[12px] text-[#9896b0] tracking-[0.8px] uppercase mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-[#f8f7ff] rounded-[14px] px-4 py-3 font-['Quicksand'] text-[14px] text-[#1e1b4b] outline-none transition-all"
                  style={{ border: "1.5px solid rgba(229,231,235,0.8)" }}
                  onFocus={(e) => (e.target.style.borderColor = "#4338ca")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(229,231,235,0.8)")}
                />
              </div>

              {error && (
                <div
                  className="rounded-[14px] px-4 py-3"
                  style={{ background: "rgba(254,242,242,0.8)" }}
                >
                  <p className="font-['Quicksand'] text-[13px] text-red-500">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full h-[54px] bg-[#4338ca] text-white font-['Quicksand'] font-bold text-[15px] rounded-[18px] cursor-pointer hover:bg-[#3730a3] transition-colors disabled:opacity-50 mt-1"
                style={{ boxShadow: "0px 6px 12px rgba(67,56,202,0.28)" }}
              >
                {loading ? "Please wait…" : isSignUp ? "Create account" : "Sign in"}
              </button>
            </form>

            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px" style={{ background: "rgba(99,102,241,0.1)" }} />
              <span className="font-['Quicksand'] text-[12px] text-[#9896b0]">or</span>
              <div className="flex-1 h-px" style={{ background: "rgba(99,102,241,0.1)" }} />
            </div>

            <p className="font-['Quicksand'] text-[13px] text-[#9896b0] text-center">
              {isSignUp ? "Already have an account?" : "No account yet?"}{" "}
              <button
                type="button"
                onClick={() => { setIsSignUp(!isSignUp); setError("") }}
                className="text-[#4338ca] font-semibold hover:underline cursor-pointer"
              >
                {isSignUp ? "Sign in" : "Sign up free"}
              </button>
            </p>
          </div>

          {/* Footer note */}
          <p className="font-['Quicksand'] text-[12px] text-[#9896b0] text-center mt-6">
            Your audio never leaves your device. Scores are private.
          </p>
        </div>
      </div>
    </div>
  )
}