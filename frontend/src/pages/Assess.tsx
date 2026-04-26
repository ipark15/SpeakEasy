import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useRecorder } from "../hooks/useRecorder"
import { startSession, submitAssessment } from "../lib/api"

const STEPS = [
  {
    task: "read_sentence",
    navLabel: "Exercise 01 — Type 1",
    heading: "Type 1",
    exerciseLabel: "Exercise 1 of 3",
    instruction: "Please read the following sentence aloud as clearly as you can.",
    duration: 10,
  },
  {
    task: "pataka",
    navLabel: "Exercise 02 — Type 2",
    heading: "Type 2",
    exerciseLabel: "Exercise 2 of 3",
    instruction: `Please repeat "pa-ta-ka" as clearly and consistently as you can.`,
    duration: 8,
  },
  {
    task: "free_speech",
    navLabel: "Exercise 03 — Type 3",
    heading: "Type 3",
    exerciseLabel: "Exercise 3 of 3",
    instruction: "Tell us about one thing you did yesterday, speaking naturally.",
    duration: 20,
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
    return () => { if (autoStopRef.current) clearTimeout(autoStopRef.current) }
  }, [isRecording])

  useEffect(() => {
    if (blob && !isRecording && sessionId && user) handleSubmit(blob)
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

  return (
    <div className="min-h-screen bg-[#edeaf8] flex flex-col">
      {/* Nav */}
      <div className="relative shrink-0"
        style={{ background: "rgba(255,255,255,0.55)", borderBottom: "1px solid rgba(255,255,255,0.6)" }}>
        <div className="h-[74px] max-w-[1100px] mx-auto px-8 flex items-center gap-4">
          <div className="w-[38px] h-[38px] bg-[#eef2ff] rounded-[12px] flex items-center justify-center shrink-0"
            style={{ border: "1px solid rgba(99,102,241,0.1)" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4338ca" strokeWidth="2">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
              <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
              <line x1="12" y1="18" x2="12" y2="22"/>
              <line x1="8" y1="22" x2="16" y2="22"/>
            </svg>
          </div>
          <div>
            <p className="font-['Outfit'] font-semibold text-[13px] text-[#1e1b4b] leading-none mb-0.5">{current.navLabel}</p>
            <p className="font-['Outfit'] font-normal text-[11px] text-[#9896b0] leading-none">Speech Assessment</p>
          </div>
        </div>
        {/* Top progress bar — 3 segments */}
        <div className="absolute bottom-0 left-0 right-0 h-[3px] flex gap-[3px]"
          style={{ background: "rgba(99,102,241,0.1)" }}>
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex-1 h-full rounded-[4px] transition-all duration-500"
              style={{ background: i <= step ? "linear-gradient(90deg, #6366f1, #4338ca)" : "rgba(67,56,202,0.12)" }} />
          ))}
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex items-center justify-center px-8 py-16">
        <div className="w-[520px] rounded-[28px] p-10"
          style={{ background: "rgba(255,255,255,0.82)", border: "1px solid rgba(255,255,255,0.9)", boxShadow: "0px 4px 12px rgba(99,102,241,0.08)" }}>

          {/* Inner progress dots */}
          <div className="flex gap-[6px] mb-8">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex-1 h-1 rounded-[8px] transition-all duration-500"
                style={{ background: i <= step ? "#4338ca" : "rgba(67,56,202,0.12)" }} />
            ))}
          </div>

          {/* Step label */}
          <p className="font-['Outfit'] font-bold text-[10px] text-[#9896b0] tracking-[1.2px] uppercase mb-3">
            {current.exerciseLabel}
          </p>

          {/* Heading */}
          <h1 className="font-['DM_Serif_Display'] text-[28px] text-[#1e1b4b] mb-6">{current.heading}</h1>

          {/* Instruction box */}
          <div className="bg-[#f8f7ff] rounded-[18px] p-4 mb-4 flex gap-3 items-start">
            <svg className="shrink-0 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9896b0" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p className="font-['Outfit'] font-normal text-[14px] leading-[22px] text-[#1e1b4b]">{current.instruction}</p>
          </div>

          {/* Mic area */}
          <div className="bg-[#f8f7ff] rounded-[20px] h-[140px] flex flex-col items-center justify-center gap-3 mb-6">
            {isRecording ? (
              <>
                <div className="w-12 h-12 bg-[#4338ca] rounded-full flex items-center justify-center animate-pulse"
                  style={{ boxShadow: "0px 8px 16px rgba(67,56,202,0.32)" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                    <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                    <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                    <line x1="12" y1="18" x2="12" y2="22"/>
                    <line x1="8" y1="22" x2="16" y2="22"/>
                  </svg>
                </div>
                <p className="font-['DM_Serif_Display'] text-[28px] text-[#4338ca]">{seconds}s</p>
              </>
            ) : submitting ? (
              <p className="font-['Outfit'] font-normal text-[13px] text-[#9896b0]">Analysing…</p>
            ) : (
              <>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d4d0ee" strokeWidth="1.5">
                  <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                  <line x1="12" y1="18" x2="12" y2="22"/>
                  <line x1="8" y1="22" x2="16" y2="22"/>
                </svg>
                <p className="font-['Outfit'] font-normal text-[12px] text-[#9896b0]">Press the button below to start</p>
              </>
            )}
          </div>

          {error && <p className="font-['Outfit'] text-sm text-red-500 text-center mb-4">{error}</p>}

          {/* Button */}
          {!isRecording && !submitting && (
            <button onClick={start} disabled={!sessionId}
              className="w-full h-[54px] bg-[#4338ca] text-white font-['Outfit'] font-semibold text-[15px] rounded-[18px] flex items-center justify-center gap-2 cursor-pointer hover:bg-[#3730a3] transition-colors disabled:opacity-50"
              style={{ boxShadow: "0px 6px 12px rgba(67,56,202,0.28)" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="8" y1="22" x2="16" y2="22"/>
              </svg>
              {blob ? "Re-record" : "Start Speaking"}
            </button>
          )}

          {isRecording && (
            <button onClick={stop}
              className="w-full h-[54px] font-['Outfit'] font-semibold text-[15px] text-[#4338ca] rounded-[18px] cursor-pointer transition-colors"
              style={{ background: "rgba(255,255,255,0.7)", border: "1px solid rgba(99,102,241,0.2)" }}>
              Stop Early
            </button>
          )}

          <p className="font-['Outfit'] font-normal text-[12px] text-[#9896b0] text-center mt-4">
            Speak clearly and at a natural pace
          </p>
        </div>
      </div>
    </div>
  )
}
