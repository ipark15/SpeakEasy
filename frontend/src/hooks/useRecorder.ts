import { useRef, useState } from "react"

export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [blob, setBlob] = useState<Blob | null>(null)
  const [seconds, setSeconds] = useState(0)
  const [recorderError, setRecorderError] = useState("")
  const mediaRef = useRef<MediaRecorder | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const chunks = useRef<Blob[]>([])

  async function start() {
    setRecorderError("")
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setRecorderError("Microphone access denied. Please allow mic access and try again.")
      return
    }

    // Pick the best supported MIME type
    const mimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"]
      .find((t) => MediaRecorder.isTypeSupported(t)) ?? ""

    let recorder: MediaRecorder
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    } catch {
      setRecorderError("Audio recording is not supported in this browser.")
      stream.getTracks().forEach((t) => t.stop())
      return
    }

    chunks.current = []
    recorder.ondataavailable = (e) => chunks.current.push(e.data)
    recorder.onstop = () => {
      const b = new Blob(chunks.current, { type: mimeType || "audio/webm" })
      setBlob(b)
      stream.getTracks().forEach((t) => t.stop())
    }
    recorder.start()
    mediaRef.current = recorder
    setIsRecording(true)
    setSeconds(0)
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000)
  }

  function stop() {
    mediaRef.current?.stop()
    if (timerRef.current) clearInterval(timerRef.current)
    setIsRecording(false)
  }

  function reset() {
    setBlob(null)
    setSeconds(0)
    setRecorderError("")
  }

  return { start, stop, blob, isRecording, seconds, reset, recorderError }
}
