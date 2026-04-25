import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"
import { useRecorder } from "../hooks/useRecorder"
import { startSession, submitAssessment, type AssessmentResponse } from "../lib/api"
import Navbar from "../components/Navbar"
import Card from "../components/Card"
import Button from "../components/Button"

const STEPS = [
  {
    task: "read_sentence",
    label: "Exercise 01 — Read Aloud",
    instruction: "Read this sentence aloud clearly:",
    prompt: "Please call Stella and ask her to bring these things with her from the store.",
    duration: 10,
  },
  {
    task: "pataka",
    label: "Exercise 02 — Pa-ta-ka",
    instruction: "Repeat pa-ta-ka as fast and clearly as you can:",
    prompt: "pa-ta-ka  pa-ta-ka  pa-ta-ka…",
    duration: 8,
  },
  {
    task: "free_speech",
    label: "Exercise 03 — Free Speech",
    instruction: "Answer this question naturally:",
    prompt: "Tell me one thing you did yesterday.",
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

  // Auto-stop after step duration
  useEffect(() => {
    if (isRecording) {
      autoStopRef.current = setTimeout(() => stop(), STEPS[step].duration * 1000)
    }
    return () => {
      if (autoStopRef.current) clearTimeout(autoStopRef.current)
    }
  }, [isRecording])

  // Submit once blob is ready after recording stops
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
  const progress = ((step + (submitting ? 1 : 0)) / 3) * 100

  return (
    <div className="min-h-screen bg-[#f5f3ff]">
      <Navbar />

      {/* Progress bar */}
      <div className="h-1.5 w-full bg-gray-200/50">
        <div
          className="h-full bg-[#4338ca] transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="max-w-xl mx-auto px-6 py-12">
        <p className="text-sm text-[#6a7282] mb-1">{step + 1} of 3</p>
        <h1 className="text-2xl font-semibold text-[#1e2939] mb-8">{current.label}</h1>

        <Card>
          <p className="text-sm text-[#6a7282] mb-3">{current.instruction}</p>
          <p className="text-lg text-[#1e2939] font-medium mb-8 leading-relaxed">
            "{current.prompt}"
          </p>

          {/* Mic area */}
          <div className="flex flex-col items-center gap-6">
            <div
              className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                isRecording ? "bg-[#4338ca] shadow-lg shadow-indigo-200 scale-110" : "bg-gray-100"
              }`}
            >
              <svg
                width="32"
                height="32"
                viewBox="0 0 24 24"
                fill="none"
                stroke={isRecording ? "white" : "#9ca3af"}
                strokeWidth="2"
              >
                <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="8" y1="22" x2="16" y2="22"/>
              </svg>
            </div>

            {isRecording && (
              <div className="text-center">
                <p className="text-3xl font-bold text-[#4338ca] tabular-nums">{seconds}s</p>
                <p className="text-sm text-[#6a7282]">of {current.duration}s</p>
              </div>
            )}

            {submitting && (
              <p className="text-sm text-[#6a7282]">Analyzing…</p>
            )}

            {error && <p className="text-sm text-red-500">{error}</p>}

            {!isRecording && !submitting && (
              <Button onClick={start} disabled={!sessionId} className="w-48 h-12">
                {blob ? "Re-record" : "Start Speaking"}
              </Button>
            )}

            {isRecording && (
              <Button onClick={stop} variant="outline" className="w-48 h-12">
                Stop Early
              </Button>
            )}
          </div>
        </Card>

        <p className="text-xs text-center text-[#6a7282] mt-6">
          Speak naturally — there are no wrong answers.
        </p>
      </div>
    </div>
  )
}
