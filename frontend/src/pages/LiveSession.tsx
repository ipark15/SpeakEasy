import { useEffect, useRef, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { ConversationProvider, useConversation } from "@elevenlabs/react"
import { useAuth } from "../hooks/useAuth"
import { startTherapistSession, type TherapistSession } from "../lib/api"

type Message = { from: "coach" | "user"; text: string }
type Phase = "loading" | "ready" | "connecting" | "connected" | "ended" | "error"

function CoachChat({
  phase,
  setPhase,
  signedUrl,
  firstMessage,
}: {
  phase: Phase
  setPhase: (p: Phase) => void
  signedUrl: string
  firstMessage: string
}) {
  const [messages, setMessages] = useState<Message[]>([
    { from: "coach", text: firstMessage },
  ])
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const conversation = useConversation({
    onConnect: () => setPhase("connected"),
    onDisconnect: () => setPhase("ended"),
    onError: (e) => { console.error("[ElevenLabs]", e); setPhase("error") },
    onMessage: ({ message, role }) => {
      setMessages(prev => [...prev, { from: role === "agent" ? "coach" : "user", text: message }])
    },
  })

  const isSpeaking = conversation.isSpeaking

  async function handleStart() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop())
    } catch {
      setPhase("error")
      return
    }
    setPhase("connecting")
    conversation.startSession({ signedUrl })
  }

  async function handleEnd() {
    await conversation.endSession()
  }

  return (
    <>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 max-w-[720px] w-full mx-auto">
        <div className="flex flex-col gap-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}>
              {msg.from === "coach" && (
                <div className="flex flex-col gap-1 max-w-[85%]">
                  <p className="text-[10px] font-semibold tracking-widest text-[#6a7282] uppercase ml-1 flex items-center gap-1">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="11,5 6,9 2,9 2,15 6,15 11,19 11,5" />
                    </svg>
                    Maya · Speech Coach
                  </p>
                  <div
                    className="rounded-[20px] rounded-tl-[6px] px-5 py-4 text-[14px] text-[#1e2939] leading-relaxed font-['Quicksand']"
                    style={{ background: "rgba(255,255,255,0.9)", border: "1px solid rgba(229,231,235,0.5)", boxShadow: "0 2px 8px rgba(99,102,241,0.06)" }}
                  >
                    {msg.text}
                  </div>
                </div>
              )}
              {msg.from === "user" && (
                <div
                  className="rounded-[20px] rounded-tr-[6px] px-5 py-4 text-[14px] text-white leading-relaxed max-w-[85%] font-['Quicksand']"
                  style={{ background: "#4338ca" }}
                >
                  {msg.text}
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Bottom bar */}
      <div
        className="px-6 py-5 flex items-center justify-center gap-6"
        style={{ background: "rgba(255,255,255,0.85)", borderTop: "1px solid rgba(229,231,235,0.4)", backdropFilter: "blur(8px)" }}
      >
        {phase === "ready" && (
          <button
            onClick={handleStart}
            className="px-8 py-3 rounded-full text-[14px] font-semibold text-white bg-[#4338ca] hover:bg-[#3730a3] shadow-lg shadow-indigo-200 transition-all flex items-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
              <line x1="12" y1="18" x2="12" y2="22" />
            </svg>
            Start talking to Maya
          </button>
        )}

        {phase === "connecting" && (
          <div className="flex items-center gap-3 text-[13px] text-[#6a7282] font-['Quicksand']">
            <div className="flex gap-1">
              {[0,1,2].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-[#4338ca] animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
            Connecting…
          </div>
        )}

        {phase === "connected" && (
          <>
            <span className="text-[13px] text-[#6a7282] font-['Quicksand']">
              {isSpeaking ? "Maya is speaking…" : "Listening…"}
            </span>
            <div className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg ${isSpeaking ? "bg-[#4338ca] shadow-indigo-200" : "bg-[#16a34a] shadow-green-200"}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                <line x1="12" y1="18" x2="12" y2="22" />
              </svg>
            </div>
            <button
              onClick={handleEnd}
              className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-red-500 border border-red-200 hover:bg-red-50 transition-colors"
            >
              End session
            </button>
          </>
        )}

        {phase === "ended" && (
          <span className="text-[13px] text-[#6a7282] font-['Quicksand']">Session ended</span>
        )}

        {phase === "error" && (
          <span className="text-[13px] text-red-500 font-['Quicksand']">Connection failed — please try again</span>
        )}
      </div>
    </>
  )
}

export default function LiveSession() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get("sessionId")

  const [phase, setPhase] = useState<Phase>("loading")
  const [sessionData, setSessionData] = useState<TherapistSession | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!user || !sessionId) {
      setError("No session ID — please complete an assessment first.")
      setPhase("error")
      return
    }
    startTherapistSession(sessionId, user.id)
      .then(data => { setSessionData(data); setPhase("ready") })
      .catch(err => {
        setError(err?.message ?? "Could not start session.")
        setPhase("error")
      })
  }, [user, sessionId])

  function handleEnd() {
    navigate(sessionId ? `/results/${sessionId}` : "/dashboard")
  }

  return (
    <div className="min-h-screen bg-[#f5f3ff] flex flex-col">
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-4 sticky top-0 z-10"
        style={{ background: "rgba(255,255,255,0.85)", borderBottom: "1px solid rgba(229,231,235,0.4)", backdropFilter: "blur(8px)" }}
      >
        <div className="flex items-center gap-4">
          <button
            onClick={handleEnd}
            className="w-9 h-9 rounded-full bg-[#f3f4f6] flex items-center justify-center hover:bg-[#e5e7eb] transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="2.5">
              <polyline points="15,18 9,12 15,6" />
            </svg>
          </button>
          <div className="w-8 h-8 rounded-lg bg-[#c7d2fe] flex items-center justify-center">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
              <polygon points="11,5 6,9 2,9 2,15 6,15 11,19 11,5" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
            </svg>
          </div>
          <div>
            <p className="text-[10px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase">Post-Assessment</p>
            <p className="text-[15px] font-semibold text-[#1e2939] font-['Quicksand']">Maya · Speech Coach</p>
          </div>
        </div>
        {phase === "connected" && (
          <button
            onClick={() => { /* endSession called inside CoachChat */ }}
            className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-red-500 border border-red-200 hover:bg-red-50 transition-colors"
          >
            End session
          </button>
        )}
      </div>

      {/* Loading / error states */}
      {phase === "loading" && (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="flex gap-1.5">
              {[0,1,2].map(i => (
                <div key={i} className="w-2.5 h-2.5 rounded-full bg-[#4338ca] animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
            <p className="text-[13px] text-[#6a7282] font-['Quicksand']">Maya is reviewing your assessment…</p>
          </div>
        </div>
      )}

      {phase === "error" && !sessionData && (
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="text-center">
            <p className="text-[14px] text-red-500 mb-4">{error || "Something went wrong."}</p>
            <button onClick={handleEnd} className="px-6 py-2 rounded-full bg-[#4338ca] text-white text-[13px] font-semibold">
              Go back
            </button>
          </div>
        </div>
      )}

      {/* Main conversation — only render once we have the signed URL */}
      {sessionData && phase !== "loading" && (
        <ConversationProvider>
          <CoachChat
            phase={phase}
            setPhase={setPhase}
            signedUrl={sessionData.signed_url}
            firstMessage={sessionData.first_message}
          />
        </ConversationProvider>
      )}
    </div>
  )
}
