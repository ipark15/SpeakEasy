import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useRecorder } from "../hooks/useRecorder"
import { startSession, submitAssessment } from "../lib/api"

const STEPS = [
  {
    task: "read_sentence",
    label: "Exercise 01 - Type 1",
    subtitle: "Speech Exercise",
    instruction: "What do you use for writing?",
    prompt: "Please call Stella and ask her to bring these things with her from the store.",
    hintWords: ["Please", "call", "Stella", "bring", "things", "store"],
    duration: 10,
    iconBg: "#c7d2fe",
  },
  {
    task: "pataka",
    label: "Exercise 02 - Type 2",
    subtitle: "Speech Exercise",
    instruction: "Repeat as fast and clearly as you can:",
    prompt: "pa-ta-ka",
    hintWords: ["pa", "ta", "ka", "rhythm", "speed", "clarity"],
    duration: 8,
    iconBg: "#fed7aa",
  },
  {
    task: "free_speech",
    label: "Exercise 03 - Type 3",
    subtitle: "Speech Exercise",
    instruction: "Tell us about your day:",
    prompt: "Tell me one thing you did yesterday.",
    hintWords: ["yesterday", "did", "morning", "evening", "activity", "story"],
    duration: 20,
    iconBg: "#bfdbfe",
  },
]

export default function Assess() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { start, stop, blob, isRecording, seconds, reset } = useRecorder()

  const [step, setStep] = useState<0 | 1 | 2>(0)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const autoStopRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!user) return
    startSession(user.id).then(({ session_id }) => setSessionId(session_id))
  }, [user])

  useEffect(() => {
    if (isRecording) {
      autoStopRef.current = setTimeout(() => stop(), STEPS[step].duration * 1000)
    }
    return () => {
      if (autoStopRef.current) clearTimeout(autoStopRef.current)
    }
  }, [isRecording])

  useEffect(() => {
    if (blob && !isRecording && sessionId && user) {
      handleSubmit(blob)
    }
  }, [blob])

  async function handleSubmit(audio: Blob) {
    setSubmitting(true)
    setError("")
    try {
      const form = new FormData()
      form.append("audio", audio, "recording.webm")
      form.append("task", STEPS[step].task)
      form.append("user_id", user!.id)
      form.append("session_id", sessionId!)
      await submitAssessment(form)

      if (step === 2) {
        navigate(`/results/${sessionId}`)
      } else {
        reset()
        setStep((s) => (s + 1) as 0 | 1 | 2)
      }
    } catch {
      setError("Submission failed — please try again.")
    } finally {
      setSubmitting(false)
    }
  }

  const current = STEPS[step]
  const progress = Math.round(((step + 1) / 3) * 100)

  return (
    <div className="min-h-screen bg-[#f5f3ff] flex flex-col">
      {/* Exercise header */}
      <div
        className="h-[93px] px-8 flex items-center justify-between shrink-0"
        style={{ background: "rgba(255,255,255,0.7)", borderBottom: "1px solid rgba(229,231,235,0.4)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-[16px] flex items-center justify-center shrink-0"
            style={{ background: current.iconBg }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
              <line x1="12" y1="18" x2="12" y2="22"/>
              <line x1="8" y1="22" x2="16" y2="22"/>
            </svg>
          </div>
          <div>
            <p className="text-[24px] font-normal text-[#1e2939] tracking-[0.07px] leading-[36px]">{current.label}</p>
            <p className="text-[12px] text-[#6a7282] leading-[16px]">{current.subtitle}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-[14px] bg-[rgba(243,244,246,0.6)] flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6a7282" strokeWidth="2">
              <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
          </div>
          <div className="w-9 h-9 rounded-[14px] bg-[rgba(243,244,246,0.6)] flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6a7282" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div
        className="h-[4px] rounded-full mx-8 mt-4"
        style={{ background: "rgba(229,231,235,0.5)" }}
      >
        <div
          className="h-full bg-[#4338ca] rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Main card */}
      <div className="flex-1 flex items-center justify-center px-8 py-8">
        <div
          className="w-full max-w-[448px] rounded-[24px] p-8"
          style={{ background: "rgba(255,255,255,0.7)", border: "1px solid rgba(229,231,235,0.3)" }}
        >
          {/* Question label */}
          <div className="flex items-center gap-2 mb-4">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6a7282" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <p className="text-[14px] text-[#1e2939] tracking-[-0.15px]">{current.instruction}</p>
          </div>

          {/* Hint words */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-5 h-5 bg-[#fed7aa] rounded-full flex items-center justify-center shrink-0">
                <span className="text-[#ea580c] text-[12px] font-normal leading-none">!</span>
              </div>
              <span className="text-[12px] text-[#4a5565]">Hint Words</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {current.hintWords.map((word) => (
                <span
                  key={word}
                  className="h-7 px-3 rounded-full text-[12px] text-[#364153] flex items-center"
                  style={{ background: "rgba(245,243,255,0.5)" }}
                >
                  {word}
                </span>
              ))}
            </div>
          </div>

          {/* Mic area */}
          <div
            className="w-full h-[192px] rounded-[24px] flex items-center justify-center mb-4"
            style={{ background: "rgba(245,243,255,0.5)" }}
          >
            {isRecording ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 bg-[#4338ca] rounded-full flex items-center justify-center shadow-lg shadow-indigo-200 animate-pulse">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                    <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                    <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                    <line x1="12" y1="18" x2="12" y2="22"/>
                    <line x1="8" y1="22" x2="16" y2="22"/>
                  </svg>
                </div>
                <p className="text-[24px] font-bold text-[#4338ca] tabular-nums">{seconds}s</p>
                <p className="text-[12px] text-[#6a7282]">of {current.duration}s max</p>
              </div>
            ) : submitting ? (
              <p className="text-[14px] text-[#6a7282]">Analyzing…</p>
            ) : (
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="1.5">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="8" y1="22" x2="16" y2="22"/>
              </svg>
            )}
          </div>

          {error && <p className="text-sm text-red-500 mb-3 text-center">{error}</p>}

          {/* Action button */}
          {!isRecording && !submitting && (
            <button
              onClick={start}
              disabled={!sessionId}
              className="w-full h-14 bg-[#4338ca] text-white rounded-[16px] flex items-center justify-center gap-3 text-[16px] tracking-[-0.31px] hover:bg-[#3730a3] transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="8" y1="22" x2="16" y2="22"/>
              </svg>
              {blob ? "Re-record" : "Start Speaking"}
            </button>
          )}

          {isRecording && (
            <button
              onClick={stop}
              className="w-full h-14 border border-[rgba(209,213,220,0.5)] bg-white/70 text-[#1e2939] rounded-[16px] text-[16px] tracking-[-0.31px] hover:bg-gray-50 transition-colors cursor-pointer"
            >
              Stop Early
            </button>
          )}

          <p className="text-[12px] text-[#6a7282] text-center mt-3">
            Press button and speak clearly
          </p>
        </div>
      </div>
    </div>
  )
}
