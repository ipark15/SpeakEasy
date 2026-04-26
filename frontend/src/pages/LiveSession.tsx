import { useEffect, useRef, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useRecorder } from "../hooks/useRecorder"
import { coachWebSocket } from "../lib/api"

type Message = { from: "coach" | "user"; text: string }

const POST_ASSESSMENT_INTRO =
  "Hi! I've reviewed your assessment results and I'm ready to give you personalised feedback. What would you like to work on first — or just say hello and we'll start from your scores."

const HISTORY_INTRO =
  "Welcome back! I've looked at your session history and I'm here to help you keep improving. What's been feeling hardest lately, or would you like me to highlight what your scores suggest?"

export default function LiveSession() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get("sessionId")
  const isPostAssessment = !!sessionId

  const intro = isPostAssessment ? POST_ASSESSMENT_INTRO : HISTORY_INTRO

  const [messages, setMessages] = useState<Message[]>([
    { from: "coach", text: intro },
  ])
  const [wsReady, setWsReady] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const wsSessionId = useRef(sessionId ?? `history-${user?.id ?? Date.now()}`)

  const { start, stop, isRecording, blob } = useRecorder()

  useEffect(() => {
    const ws = coachWebSocket(wsSessionId.current)
    wsRef.current = ws

    ws.onopen = () => setWsReady(true)
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        const text = data.text ?? data.message ?? String(e.data)
        setMessages((prev) => [...prev, { from: "coach", text }])
      } catch {
        setMessages((prev) => [...prev, { from: "coach", text: String(e.data) }])
      }
    }
    ws.onerror = () => {}

    return () => ws.close()
  }, [])

  useEffect(() => {
    if (!blob) return
    if (wsReady && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(blob)
    }
  }, [blob, wsReady])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  function handleEnd() {
    wsRef.current?.close()
    navigate(isPostAssessment ? `/results/${sessionId}` : "/dashboard")
  }

  function handleMic() {
    if (isRecording) stop()
    else start()
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
            <p className="text-[10px] font-semibold tracking-[0.15em] text-[#6a7282] uppercase">
              {isPostAssessment ? "Post-Assessment" : "Ongoing Support"}
            </p>
            <p className="text-[15px] font-semibold text-[#1e2939] font-['Quicksand']">Speech Coach</p>
          </div>
        </div>

        <button
          onClick={handleEnd}
          className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-red-500 border border-red-200 hover:bg-red-50 transition-colors"
        >
          End session
        </button>
      </div>

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
                    Speech Coach
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

      {/* Bottom mic bar */}
      <div
        className="px-6 py-5 flex items-center justify-center gap-6"
        style={{ background: "rgba(255,255,255,0.85)", borderTop: "1px solid rgba(229,231,235,0.4)", backdropFilter: "blur(8px)" }}
      >
        <span className="text-[13px] text-[#6a7282] font-['Quicksand']">Tap to speak</span>

        <button
          onClick={handleMic}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
            isRecording
              ? "bg-red-500 scale-110 shadow-lg shadow-red-200"
              : "bg-[#4338ca] hover:bg-[#3730a3] shadow-lg shadow-indigo-200"
          }`}
        >
          {isRecording ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="8" y1="22" x2="16" y2="22" />
            </svg>
          )}
        </button>

        <span className="text-[13px] text-[#6a7282] font-['Quicksand']">
          {isRecording ? "Recording…" : "Click to start"}
        </span>
      </div>
    </div>
  )
}
