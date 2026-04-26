import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { ConversationProvider, useConversation } from "@elevenlabs/react"
import { useAuth } from "../hooks/useAuth"
import { startTherapistSession, type TherapistSession } from "../lib/api"

type Phase = "loading" | "ready" | "connecting" | "connected" | "ended" | "error"

const WAVE_HEIGHTS = [10, 18, 26, 22, 14, 30, 18, 26, 14, 22, 18, 10]

function TherapistChat({ phase, setPhase, systemPrompt }: { phase: Phase; setPhase: (p: Phase) => void; systemPrompt: string }) {
  const conversation = useConversation({
    onConnect: () => setPhase("connected"),
    onDisconnect: () => setPhase("ended"),
    onError: () => setPhase("error"),
  })

  const isSpeaking = conversation.isSpeaking

  async function handleStart() {
    setPhase("connecting")
    try {
      await conversation.startSession({
        overrides: { agent: { prompt: { prompt: systemPrompt } } },
      })
    } catch {
      setPhase("error")
    }
  }

  async function handleEnd() {
    await conversation.endSession()
  }

  return (
    <>
      {phase === "ready" && (
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="rounded-[16px] p-4 w-full text-center"
            style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.12)" }}>
            <p className="text-[13px] text-[#4338ca] font-medium mb-1">Ready to talk</p>
            <p className="text-[12px] text-[#6b6b8a]">
              Alex has reviewed your assessment. Speak naturally — the session is voice-based.
            </p>
          </div>
          <button
            onClick={handleStart}
            className="w-full h-[54px] rounded-[18px] text-white font-['Outfit'] font-semibold text-[16px] cursor-pointer hover:opacity-90 transition-opacity flex items-center justify-center gap-2.5"
            style={{ background: "#4338ca", boxShadow: "0px 6px 16px rgba(67,56,202,0.32)" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
              <line x1="12" y1="18" x2="12" y2="22" />
            </svg>
            Start Session
          </button>
        </div>
      )}

      {phase === "connecting" && (
        <div className="flex flex-col items-center gap-3">
          <div className="flex gap-1.5">
            {[0, 1, 2].map(i => (
              <div key={i} className="w-2 h-2 rounded-full bg-[#4338ca] animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
          <p className="text-[13px] text-[#9896b0]">Connecting to Alex…</p>
        </div>
      )}

      {phase === "connected" && (
        <div className="flex flex-col items-center gap-5 w-full">
          <div className="rounded-[16px] p-4 w-full text-center"
            style={{ background: "rgba(22,163,74,0.07)", border: "1px solid rgba(22,163,74,0.15)" }}>
            <div className="flex items-center justify-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-[#16a34a] animate-pulse" />
              <p className="text-[13px] text-[#16a34a] font-semibold">
                {isSpeaking ? "Alex is speaking…" : "Listening to you…"}
              </p>
            </div>
            <p className="text-[12px] text-[#6b6b8a]">Speak naturally — Alex will respond.</p>
          </div>

          <div className="flex items-center gap-1 h-12">
            {WAVE_HEIGHTS.map((h, i) => (
              <div key={i} className="w-1.5 rounded-full transition-all duration-300"
                style={{
                  background: isSpeaking ? "#4338ca" : "#c7d2fe",
                  height: isSpeaking ? `${h}px` : "8px",
                  animationDelay: `${i * 0.08}s`,
                }}
              />
            ))}
          </div>

          <button
            onClick={handleEnd}
            className="w-full h-[52px] rounded-[18px] font-['Outfit'] font-semibold text-[15px] cursor-pointer hover:opacity-90 transition-opacity"
            style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.2)", color: "#dc2626" }}
          >
            End Session
          </button>
        </div>
      )}
    </>
  )
}

export default function TherapistSession() {
  const navigate = useNavigate()
  const { sessionId } = useParams<{ sessionId?: string }>()
  const { user } = useAuth()

  const [phase, setPhase] = useState<Phase>("loading")
  const [error, setError] = useState("")
  const [sessionData, setSessionData] = useState<TherapistSession | null>(null)

  const missingSessionId = !!user && !sessionId

  useEffect(() => {
    if (!user || !sessionId) return

    startTherapistSession(sessionId, user.id)
      .then((data) => {
        setSessionData(data)
        setPhase("ready")
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Could not start therapist session."
        setError(msg)
        setPhase("error")
      })
  }, [user, sessionId])

  const showError = phase === "error" || missingSessionId
  const errorMsg = missingSessionId
    ? "No session ID provided. Please complete an assessment first."
    : error || "An unexpected error occurred."

  return (
    <div className="min-h-screen bg-[#edeaf8] flex flex-col">
      <nav className="sticky top-0 z-10 sp-nav px-6 py-3 flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2.5 font-['Outfit'] font-bold text-[13px] text-[#4338ca] cursor-pointer hover:opacity-70 transition-opacity"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back
        </button>
        <span className="font-['Outfit'] font-bold text-[13px] text-[#4338ca]">Speech Therapist</span>
        <div className="w-16" />
      </nav>

      <div className="flex-1 flex flex-col items-center justify-center px-5 py-10 max-w-[480px] mx-auto w-full">
        {/* Avatar */}
        <div className="relative mb-8">
          <div className="w-[120px] h-[120px] rounded-full flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #4338ca 0%, #7c3aed 100%)" }}>
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          {phase === "connected" && (
            <div className="absolute bottom-1 right-1 w-4 h-4 rounded-full bg-[#16a34a] border-2 border-white" />
          )}
        </div>

        <h1 className="text-[28px] font-bold text-[#1e1b4b] mb-1" style={{ fontFamily: "'DM Serif Display', serif" }}>
          Alex
        </h1>
        <p className="text-[14px] text-[#6b6b8a] mb-8">Speech Therapist · AI-Powered</p>

        {phase === "loading" && !missingSessionId && (
          <div className="flex flex-col items-center gap-3">
            <div className="flex gap-1.5">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-[#4338ca] animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
            <p className="text-[13px] text-[#9896b0]">Preparing your session…</p>
          </div>
        )}

        {phase === "ended" && (
          <div className="flex flex-col items-center gap-4 w-full">
            <div className="rounded-[16px] p-4 w-full text-center"
              style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.12)" }}>
              <p className="text-[14px] font-semibold text-[#1e1b4b] mb-1">Session complete</p>
              <p className="text-[13px] text-[#6b6b8a]">Great work! Keep practising the exercises Alex recommended.</p>
            </div>
            <div className="grid grid-cols-2 gap-3 w-full">
              <button onClick={() => setPhase("ready")}
                className="h-[50px] rounded-[16px] text-[14px] font-semibold text-[#4338ca] bg-white border border-[rgba(229,231,235,0.8)] hover:bg-[#f0eeff] transition-colors">
                Talk Again
              </button>
              <button onClick={() => navigate("/dashboard")}
                className="h-[50px] rounded-[16px] text-[14px] font-semibold text-white cursor-pointer hover:opacity-90 transition-opacity"
                style={{ background: "#4338ca" }}>
                Dashboard
              </button>
            </div>
          </div>
        )}

        {showError && (
          <div className="flex flex-col items-center gap-4 w-full">
            <div className="rounded-[16px] p-4 w-full text-center"
              style={{ background: "rgba(220,38,38,0.06)", border: "1px solid rgba(220,38,38,0.15)" }}>
              <p className="text-[13px] font-semibold text-[#dc2626] mb-1">Something went wrong</p>
              <p className="text-[12px] text-[#6b6b8a]">{errorMsg}</p>
            </div>
            <button onClick={() => navigate(-1)}
              className="w-full h-[50px] rounded-[16px] text-[14px] font-semibold text-[#4338ca] bg-white border border-[rgba(229,231,235,0.8)] hover:bg-[#f0eeff] transition-colors">
              Go Back
            </button>
          </div>
        )}

        {sessionData && phase !== "loading" && phase !== "error" && (
          <ConversationProvider signedUrl={sessionData.signed_url}>
            <TherapistChat phase={phase} setPhase={setPhase} systemPrompt={sessionData.system_prompt} />
          </ConversationProvider>
        )}
      </div>
    </div>
  )
}
