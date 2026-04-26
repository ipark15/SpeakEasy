import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { ConversationProvider, useConversation } from "@elevenlabs/react"
import { useAuth } from "../hooks/useAuth"
import { startTherapistSession, type TherapistSession } from "../lib/api"

type Phase = "loading" | "ready" | "connecting" | "connected" | "ended" | "error"

const NUM_BARS = 16

function VoiceBars({ active, isSpeaking }: { active: boolean; isSpeaking: boolean }) {
  const [heights, setHeights] = useState<number[]>(Array(NUM_BARS).fill(4))
  const animRef = useRef<number | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    if (!active) {
      setHeights(Array(NUM_BARS).fill(4))
      animRef.current && cancelAnimationFrame(animRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
      return
    }

    let ctx: AudioContext | null = null

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      streamRef.current = stream
      ctx = new AudioContext()
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 64
      source.connect(analyser)
      analyserRef.current = analyser

      const data = new Uint8Array(analyser.frequencyBinCount)
      const tick = () => {
        analyser.getByteFrequencyData(data)
        const slice = Math.floor(data.length / NUM_BARS)
        const next = Array.from({ length: NUM_BARS }, (_, i) => {
          const val = data[i * slice] ?? 0
          return Math.max(4, (val / 255) * 52)
        })
        setHeights(next)
        animRef.current = requestAnimationFrame(tick)
      }
      tick()
    }).catch(() => {})

    return () => {
      animRef.current && cancelAnimationFrame(animRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
      ctx?.close()
    }
  }, [active])

  // AI speaking: animated sine wave
  const [aiHeights, setAiHeights] = useState<number[]>(Array(NUM_BARS).fill(4))
  const aiFrameRef = useRef<number | null>(null)
  const aiTickRef = useRef(0)

  useEffect(() => {
    if (!isSpeaking) {
      setAiHeights(Array(NUM_BARS).fill(4))
      aiFrameRef.current && cancelAnimationFrame(aiFrameRef.current)
      return
    }
    const tick = () => {
      aiTickRef.current += 0.12
      const t = aiTickRef.current
      const next = Array.from({ length: NUM_BARS }, (_, i) => {
        const phase = (i / NUM_BARS) * Math.PI * 2
        return 8 + Math.abs(Math.sin(t + phase)) * 44
      })
      setAiHeights(next)
      aiFrameRef.current = requestAnimationFrame(tick)
    }
    tick()
    return () => { aiFrameRef.current && cancelAnimationFrame(aiFrameRef.current) }
  }, [isSpeaking])

  const displayHeights = isSpeaking ? aiHeights : heights
  const color = isSpeaking ? "#4338ca" : "#a5b4fc"

  return (
    <div className="flex items-center justify-center gap-1 h-16">
      {displayHeights.map((h, i) => (
        <div
          key={i}
          className="w-1.5 rounded-full transition-all"
          style={{
            height: `${h}px`,
            background: color,
            transitionDuration: isSpeaking ? "80ms" : "60ms",
          }}
        />
      ))}
    </div>
  )
}

function TherapistChat({ phase, setPhase, signedUrl }: {
  phase: Phase
  setPhase: (p: Phase) => void
  signedUrl: string
}) {
  const conversation = useConversation({
    onConnect: () => setPhase("connected"),
    onDisconnect: () => setPhase("ended"),
    onError: () => setPhase("error"),
  })

  const isSpeaking = conversation.isSpeaking
  const isConnected = phase === "connected"

  async function handleStart() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop())
    } catch {
      setPhase("error")
      return
    }
    setPhase("connecting")
    try {
      conversation.startSession({ signedUrl })
    } catch {
      setPhase("error")
    }
  }

  function handleEnd() {
    conversation.endSession()
  }

  return (
    <>
      <VoiceBars active={isConnected} isSpeaking={isSpeaking} />

      {phase === "ready" && (
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="rounded-[18px] p-4 w-full text-center"
            style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.12)" }}>
            <p className="font-['Quicksand'] font-semibold text-[13px] text-[#4338ca] mb-1">Ready to talk</p>
            <p className="font-['Quicksand'] text-[12px] text-[#6b6b8a]">
              Your assessment has been reviewed. Speak naturally — the session is voice-based.
            </p>
          </div>
          <button
            onClick={handleStart}
            className="w-full h-[54px] rounded-[18px] text-white font-['Quicksand'] font-bold text-[16px] cursor-pointer hover:opacity-90 transition-opacity flex items-center justify-center gap-2.5"
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
          <p className="font-['Quicksand'] text-[13px] text-[#9896b0]">Connecting to AI…</p>
        </div>
      )}

      {phase === "connected" && (
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="rounded-[18px] p-4 w-full text-center"
            style={{ background: "rgba(22,163,74,0.07)", border: "1px solid rgba(22,163,74,0.15)" }}>
            <div className="flex items-center justify-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-[#16a34a] animate-pulse" />
              <p className="font-['Quicksand'] font-semibold text-[13px] text-[#16a34a]">
                {isSpeaking ? "AI is speaking…" : "Listening to you…"}
              </p>
            </div>
            <p className="font-['Quicksand'] text-[12px] text-[#6b6b8a]">Speak naturally — The coach will respond.</p>
          </div>
          <button
            onClick={handleEnd}
            className="w-full h-[50px] rounded-[18px] font-['Quicksand'] font-semibold text-[15px] cursor-pointer hover:opacity-90 transition-opacity"
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
      .then(data => { setSessionData(data); setPhase("ready") })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Could not start therapist session.")
        setPhase("error")
      })
  }, [user, sessionId])

  const showError = phase === "error" || missingSessionId
  const errorMsg = missingSessionId
    ? "No session ID provided. Please complete an assessment first."
    : error || "An unexpected error occurred."

  return (
    <div className="min-h-screen bg-[#edeaf8] flex flex-col">
      {/* Nav */}
      <nav className="sticky top-0 z-10 px-6 py-4 flex items-center justify-between"
        style={{ background: "rgba(255,255,255,0.7)", backdropFilter: "blur(12px)", borderBottom: "1px solid rgba(255,255,255,0.6)" }}>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 font-['Quicksand'] font-bold text-[13px] text-[#4338ca] cursor-pointer hover:opacity-70 transition-opacity"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back
        </button>
        <span className="font-['Quicksand'] font-bold text-[13px] text-[#4338ca]">AI Therapist</span>
        <div className="w-12" />
      </nav>

      <div className="flex-1 flex flex-col items-center justify-center px-5 py-10 max-w-[440px] mx-auto w-full gap-6">

        {/* Avatar */}
        <div className="relative">
          <div className="w-[108px] h-[108px] rounded-full flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #4338ca 0%, #7c3aed 100%)", boxShadow: "0px 12px 32px rgba(67,56,202,0.28)" }}>
            <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          {phase === "connected" && (
            <div className="absolute bottom-1 right-1 w-4 h-4 rounded-full bg-[#16a34a] border-2 border-white" />
          )}
        </div>

        <div className="text-center">
          <h1 className="font-['Quicksand'] font-extrabold text-[28px] text-[#1e1b4b] mb-1">AI</h1>
          <p className="font-['Quicksand'] text-[13px] text-[#9896b0]">Speech Therapist · AI-Powered</p>
        </div>

        {/* Loading */}
        {phase === "loading" && !missingSessionId && (
          <div className="flex flex-col items-center gap-3">
            <div className="flex gap-1.5">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-[#4338ca] animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
            <p className="font-['Quicksand'] text-[13px] text-[#9896b0]">Preparing your session…</p>
          </div>
        )}

        {/* Session ended */}
        {phase === "ended" && (
          <div className="flex flex-col items-center gap-4 w-full">
            <div className="rounded-[18px] p-5 w-full text-center"
              style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.12)" }}>
              <p className="font-['Quicksand'] font-bold text-[15px] text-[#1e1b4b] mb-1">Session complete</p>
              <p className="font-['Quicksand'] text-[13px] text-[#6b6b8a]">Great work! Keep practising the exercises AI recommended.</p>
            </div>
            <div className="grid grid-cols-2 gap-3 w-full">
              <button onClick={() => setPhase("ready")}
                className="h-[50px] rounded-[16px] font-['Quicksand'] font-semibold text-[14px] text-[#4338ca] bg-white border border-[rgba(229,231,235,0.8)] hover:bg-[#f0eeff] transition-colors cursor-pointer">
                Talk Again
              </button>
              <button onClick={() => navigate("/dashboard")}
                className="h-[50px] rounded-[16px] font-['Quicksand'] font-semibold text-[14px] text-white cursor-pointer hover:opacity-90 transition-opacity"
                style={{ background: "#4338ca", boxShadow: "0px 4px 12px rgba(67,56,202,0.28)" }}>
                Dashboard
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {showError && (
          <div className="flex flex-col items-center gap-4 w-full">
            <div className="rounded-[18px] p-5 w-full text-center"
              style={{ background: "rgba(220,38,38,0.06)", border: "1px solid rgba(220,38,38,0.15)" }}>
              <p className="font-['Quicksand'] font-semibold text-[13px] text-[#dc2626] mb-1">Something went wrong</p>
              <p className="font-['Quicksand'] text-[12px] text-[#6b6b8a]">{errorMsg}</p>
            </div>
            <button onClick={() => navigate(-1)}
              className="w-full h-[50px] rounded-[16px] font-['Quicksand'] font-semibold text-[14px] text-[#4338ca] bg-white border border-[rgba(229,231,235,0.8)] hover:bg-[#f0eeff] transition-colors cursor-pointer">
              Go Back
            </button>
          </div>
        )}

        {/* Active conversation */}
        {sessionData && phase !== "loading" && phase !== "error" && !missingSessionId && (
          <div className="w-full">
            <ConversationProvider>
              <TherapistChat
                phase={phase}
                setPhase={setPhase}
                signedUrl={sessionData.signed_url}
              />
            </ConversationProvider>
          </div>
        )}
      </div>
    </div>
  )
}
