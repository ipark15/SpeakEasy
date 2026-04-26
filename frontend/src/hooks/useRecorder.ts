import { useRef, useState } from "react"

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const numSamples = samples.length
  const buffer = new ArrayBuffer(44 + numSamples * 2)
  const view = new DataView(buffer)

  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
  }
  writeStr(0, "RIFF")
  view.setUint32(4, 36 + numSamples * 2, true)
  writeStr(8, "WAVE")
  writeStr(12, "fmt ")
  view.setUint32(16, 16, true)       // PCM chunk size
  view.setUint16(20, 1, true)        // PCM format
  view.setUint16(22, 1, true)        // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)  // byte rate
  view.setUint16(32, 2, true)        // block align
  view.setUint16(34, 16, true)       // bits per sample
  writeStr(36, "data")
  view.setUint32(40, numSamples * 2, true)

  // float32 → int16
  let offset = 44
  for (let i = 0; i < numSamples; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    offset += 2
  }

  return new Blob([buffer], { type: "audio/wav" })
}

export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [blob, setBlob] = useState<Blob | null>(null)
  const [seconds, setSeconds] = useState(0)
  const [recorderError, setRecorderError] = useState("")

  const audioCtxRef = useRef<AudioContext | null>(null)
  const workletRef = useRef<AudioWorkletNode | null>(null)
  const samplesRef = useRef<Float32Array[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const TARGET_SR = 16000

  async function start() {
    setRecorderError("")
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
          channelCount: 1,
        },
      })
    } catch {
      setRecorderError("Microphone access denied. Please allow mic access and try again.")
      return
    }

    streamRef.current = stream
    samplesRef.current = []

    const ctx = new AudioContext()
    audioCtxRef.current = ctx

    await ctx.audioWorklet.addModule("/recorder-processor.js")
    const source = ctx.createMediaStreamSource(stream)
    const worklet = new AudioWorkletNode(ctx, "recorder-processor")
    workletRef.current = worklet

    worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
      samplesRef.current.push(new Float32Array(e.data))
    }

    source.connect(worklet)
    worklet.connect(ctx.destination)

    setIsRecording(true)
    setSeconds(0)
    timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000)
  }

  function stop() {
    if (timerRef.current) clearInterval(timerRef.current)
    setIsRecording(false)

    const ctx = audioCtxRef.current
    const worklet = workletRef.current
    const stream = streamRef.current

    if (!ctx || !worklet) return

    worklet.disconnect()
    worklet.port.close()
    stream?.getTracks().forEach((t) => t.stop())

    // Concatenate all PCM chunks
    const totalLen = samplesRef.current.reduce((s, c) => s + c.length, 0)
    const merged = new Float32Array(totalLen)
    let offset = 0
    for (const chunk of samplesRef.current) {
      merged.set(chunk, offset)
      offset += chunk.length
    }

    // Resample from ctx.sampleRate → 16000 using OfflineAudioContext
    const offlineCtx = new OfflineAudioContext(1, Math.ceil(merged.length * TARGET_SR / ctx.sampleRate), TARGET_SR)
    const buf = offlineCtx.createBuffer(1, merged.length, ctx.sampleRate)
    buf.copyToChannel(merged, 0)
    const offlineSource = offlineCtx.createBufferSource()
    offlineSource.buffer = buf
    offlineSource.connect(offlineCtx.destination)
    offlineSource.start()

    offlineCtx.startRendering().then((rendered) => {
      const resampled = rendered.getChannelData(0)
      setBlob(encodeWav(resampled, TARGET_SR))
    })

    ctx.close()
    audioCtxRef.current = null
    workletRef.current = null
  }

  function reset() {
    setBlob(null)
    setSeconds(0)
    setRecorderError("")
  }

  return { start, stop, blob, isRecording, seconds, reset, recorderError }
}
