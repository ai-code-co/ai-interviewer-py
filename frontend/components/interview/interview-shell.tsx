"use client"

import { useEffect, useState, useRef } from "react"
import { InterviewAnswerRecorder } from "./answer-recorder"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Mic, Video, CheckCircle, Loader2, Radio, Download } from "lucide-react"
import { jsPDF } from "jspdf"

interface InterviewShellProps { token: string }
type InterviewState = "LOADING" | "PERMISSIONS" | "GREETING" | "QUESTIONS" | "UPLOADING" | "COMPLETED" | "ERROR"

export function InterviewShell({ token }: InterviewShellProps) {
  const [viewState, setViewState] = useState<InterviewState>("LOADING")
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  // LIVE SUBTITLE STATE
  const [currentSubtitle, setCurrentSubtitle] = useState<string>("")

  const [history, setHistory] = useState<Array<{ role: 'AI' | 'Candidate', text: string }>>([])

  const [audioSrc, setAudioSrc] = useState<string | null>(null)
  const audioElRef = useRef<HTMLAudioElement | null>(null)

  const fullSessionRecorderRef = useRef<MediaRecorder | null>(null)
  const fullChunksRef = useRef<Blob[]>([])

  const answerRecorderRef = useRef<MediaRecorder | null>(null)
  const answerChunksRef = useRef<Blob[]>([])

  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const ttsSourceRef = useRef<MediaElementAudioSourceNode | null>(null)

  const recognitionRef = useRef<any>(null)
  const transcriptBuffer = useRef("")
  const interimBuffer = useRef("")
  const isListeningRef = useRef<boolean>(false)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001/api"

  // --- INIT ---
  useEffect(() => {
    const init = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/interview/validate/${token}`)
        const session = await res.json()
        if (!res.ok) throw new Error(session.detail || "Invalid Link")
        if (session.status === "COMPLETED") { setViewState("COMPLETED"); return }

        setSessionId(session.id)
        setJobId(session.job_id)

        // Resume Logic
        if (session.last_question_id) {
          setViewState("QUESTIONS")
          try {
            const stream = await setupStream()
            if (stream) {
              startFullRecording(stream)
              startContinuousTranscription()
              await fetchNextQuestion(session.last_question_id)
            }
          } catch { setViewState("PERMISSIONS") }
        } else {
          setViewState("PERMISSIONS")
        }

      } catch (err: any) {
        setError(err.message)
        setViewState("ERROR")
      }
    }
    if (token) void init()
    return () => { cleanupMedia() }
  }, [token])

  const cleanupMedia = () => {
    isListeningRef.current = false
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
    if (audioContextRef.current) audioContextRef.current.close()
    if (recognitionRef.current) recognitionRef.current.stop()
  }

  // --- AUDIO SETUP ---
  const setupStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      })

      const AudioContext = (window.AudioContext || (window as any).webkitAudioContext)
      const ctx = new AudioContext()
      const dest = ctx.createMediaStreamDestination()
      const micSource = ctx.createMediaStreamSource(stream)
      micSource.connect(dest)

      if (audioElRef.current && !ttsSourceRef.current) {
        const ttsSource = ctx.createMediaElementSource(audioElRef.current)
        ttsSource.connect(dest)
        ttsSource.connect(ctx.destination)
        ttsSourceRef.current = ttsSource
      }

      const mixedStream = new MediaStream([...stream.getVideoTracks(), ...dest.stream.getAudioTracks()])
      streamRef.current = mixedStream
      audioContextRef.current = ctx
      return mixedStream
    } catch (e) {
      console.error(e)
      throw e
    }
  }

  const startContinuousTranscription = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event: any) => {
      let final = ""
      let interim = ""
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) final += event.results[i][0].transcript + " "
        else interim += event.results[i][0].transcript
      }
      if (final) transcriptBuffer.current += final
      interimBuffer.current = interim
      setCurrentSubtitle(interim)
    }

    recognition.onend = () => {
      if (isListeningRef.current) { try { recognition.start() } catch { } }
    }

    recognitionRef.current = recognition
    isListeningRef.current = true
    try { recognition.start() } catch { }
  }

  const startFullRecording = (stream: MediaStream) => {
    fullChunksRef.current = []
    const fullRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' })
    fullRecorder.ondataavailable = (e) => { if (e.data.size > 0) fullChunksRef.current.push(e.data) }
    fullRecorder.start()
    fullSessionRecorderRef.current = fullRecorder
  }

  // --- ACTIONS ---
  const checkPermissions = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      s.getTracks().forEach(t => t.stop())
      setViewState("GREETING")
    } catch (err) {
      alert("Microphone and Camera access are required.")
    }
  }

  const startInterview = async () => {
    try {
      const stream = await setupStream()
      if (!stream) return
      startFullRecording(stream)
      startContinuousTranscription()
      setViewState("QUESTIONS")
      await fetchNextQuestion(null)
    } catch (e) {
      alert("Failed to start devices.")
    }
  }

  const fetchNextQuestion = async (lastId: string | null) => {
    if (!jobId) return
    setIsProcessing(true) // Ensure loading state is active

    try {
      const res = await fetch(`${API_BASE_URL}/interview/question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, last_question_id: lastId }),
      })
      const data = await res.json()
      console.log("data", data)
      if (data.done) {
        await finishInterview()
      } else {
        setCurrentQuestion(data.question)
        setHistory(prev => [...prev, { role: 'AI', text: data.question.question_text }])
        setCurrentSubtitle("")

        // Reset Text Buffers
        transcriptBuffer.current = ""
        interimBuffer.current = ""

        if (data.audio_base64 && audioElRef.current) {
          audioElRef.current.src = data.audio_base64
          if (audioContextRef.current?.state === 'suspended') await audioContextRef.current.resume()
          await audioElRef.current.play().catch(() => { })
        }

        // IMPORTANT: Start new audio chunk recording
        startAnswerRecording()
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setIsProcessing(false) // CRITICAL: Ensure UI unlocks even if error
    }
  }

  // const startAnswerRecording = () => {
  //   console.log("first record")
  //   // if (answerRecorderRef.current?.state === "recording") {
  //   //   answerRecorderRef.current.stop()
  //   // }
  //   if (!streamRef.current) return
  //   answerChunksRef.current = []
  //   console.log("streamRef.current", streamRef.current)
  //   console.log("answerChunksRef", answerChunksRef)
  //   const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : ""
  //   const recorder = new MediaRecorder(streamRef.current, mimeType ? { mimeType } : undefined)
  //   console.log("recorder", recorder)
  //   recorder.start()
  //   recorder.ondataavailable = (e) => { 
  //     console.log("putting data 230",e)
  //     answerChunksRef.current.push(e.data) 
  //   }
  //   console.log("234 recorder",234)
  //   console.log("235 answerRecorder",answerRecorderRef)
  //   answerRecorderRef.current = recorder
  // }

  const startAnswerRecording = () => {
    if (!streamRef.current) return

    answerChunksRef.current = []

    const mimeType = MediaRecorder.isTypeSupported("audio/webm")
      ? "audio/webm"
      : ""

    const recorder = new MediaRecorder(
      streamRef.current,
      mimeType ? { mimeType } : undefined
    )

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        answerChunksRef.current.push(e.data)
      }
    }

    recorder.onerror = console.error

    recorder.start(1000)

    answerRecorderRef.current = recorder
    console.log("answerRecorderRef", answerRecorderRef.current)
    console.log("recorder", recorder)
  }


  const handleAnswerSubmit = async () => {
    if (!sessionId || !currentQuestion) return

    setIsProcessing(true) // LOCK UI

    // FIX: Safer Recorder Stop
    const recorder = answerRecorderRef.current
    console.log("241 recorder",recorder)
    console.log("241d recorder",answerRecorderRef)
    console.log("241e recorder",answerRecorderRef.current)
    if (recorder && recorder.state === 'recording') {
      recorder.stop()
      console.log("242 answer chunk",answerChunksRef)
      // Wait for onstop to fire
      // await new Promise<void>(resolve => {
      //   recorder.onstop = () => resolve()
      // })

      await new Promise<void>((resolve) => {
        console.log("250 here,",resolve)
        recorder.addEventListener("stop", ()=>resolve(), { once: true })
        // recorder.stop()
      })
    }

    const audioBlob = new Blob(answerChunksRef.current, { type: 'audio/webm' })
    console.log("257 audioblob",audioBlob)

    // Use fallback text if Whisper fails later
    const fallbackText = (transcriptBuffer.current + " " + interimBuffer.current).trim() || "(Processing speech...)"
    setHistory(prev => [...prev, { role: 'Candidate', text: fallbackText }])

    try {
      const formData = new FormData()
      formData.append("session_id", sessionId)
      formData.append("question_id", currentQuestion.id)
      formData.append("audio_chunk", audioBlob, "answer.webm")

      console.log("258", audioBlob)
      console.log("259 tyypes", audioBlob.type)
      // Send to API
      await fetch(`${API_BASE_URL}/interview/answer`, { method: "POST", body: formData })

      // Get next question
      await fetchNextQuestion(currentQuestion.id)

    } catch (e: any) {
      console.error(e)
      // If upload fails, try moving next anyway to not block user
      await fetchNextQuestion(currentQuestion.id)
    }
  }

  // ... (keep finishInterview, createFormattedPDF, downloadTranscript exactly as before) ...
  const finishInterview = async () => {
    if (!sessionId || !fullSessionRecorderRef.current) return
    setViewState("UPLOADING")
    isListeningRef.current = false
    if (recognitionRef.current) recognitionRef.current.stop()
    const recorder = fullSessionRecorderRef.current
    if (recorder.state !== 'inactive') {
      recorder.stop()
      await new Promise<void>(resolve => { recorder.onstop = () => resolve() })
    }
    const fullBlob = new Blob(fullChunksRef.current, { type: "video/webm" })
    const videoForm = new FormData()
    videoForm.append("session_id", sessionId)
    videoForm.append("video", fullBlob, "full_interview.webm")
    const doc = createFormattedPDF()
    const pdfBlob = doc.output('blob')
    const pdfForm = new FormData()
    pdfForm.append("session_id", sessionId)
    pdfForm.append("file", pdfBlob, "transcript.pdf")
    try {
      await Promise.all([
        fetch(`${API_BASE_URL}/interview/upload-full-video`, { method: "POST", body: videoForm }),
        fetch(`${API_BASE_URL}/interview/upload-transcript`, { method: "POST", body: pdfForm }),
        fetch(`${API_BASE_URL}/interview/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId })
        })
      ])
      setViewState("COMPLETED")
      cleanupMedia()
    } catch (e) {
      setError("Failed to upload. Please contact support.")
      setViewState("ERROR")
    }
  }

  const createFormattedPDF = () => {
    const doc = new jsPDF()
    doc.setFontSize(20); doc.text("Interview Transcript", 20, 20)
    doc.setFontSize(12)
    let y = 40
    const pageHeight = doc.internal.pageSize.height
    history.forEach((item) => {
      doc.setFont("helvetica", "bold")
      item.role === 'AI' ? doc.setTextColor(0, 0, 0) : doc.setTextColor(0, 102, 204)
      doc.text(`${item.role === 'AI' ? 'AI Interviewer' : 'Candidate'}:`, 20, y)
      y += 7
      doc.setFont("helvetica", "normal"); doc.setTextColor(0, 0, 0)
      const lines = doc.splitTextToSize(item.text, 170)
      doc.text(lines, 20, y)
      y += (lines.length * 7) + 10
      if (y > pageHeight - 20) { doc.addPage(); y = 20 }
    })
    return doc
  }
  const downloadTranscript = () => { createFormattedPDF().save("Interview_Transcript.pdf") }

  // --- VIEWS ---
  if (viewState === "LOADING") return <div className="h-screen bg-neutral-950 text-white flex items-center justify-center text-sm tracking-widest uppercase">Initializing...</div>
  if (viewState === "UPLOADING") return (
    <div className="h-screen bg-neutral-950 text-white flex flex-col items-center justify-center space-y-6">
      <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
      <div className="text-center">
        <h2 className="text-xl font-medium">Saving Session</h2>
        <p className="text-neutral-500 text-sm mt-2">Uploading video and transcript...</p>
      </div>
    </div>
  )
  if (viewState === "COMPLETED") return (
    <div className="h-screen bg-neutral-950 text-white flex items-center justify-center p-4">
      <Card className="max-w-md w-full text-center p-8 bg-neutral-900 border-neutral-800 shadow-2xl">
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-6" />
        <h2 className="text-2xl font-bold mb-2 text-white">Interview Complete</h2>
        <p className="text-neutral-400 mb-8 text-sm">Your responses have been recorded.</p>
        <Button onClick={downloadTranscript} variant="outline" className="w-full border-neutral-700 text-neutral-300 hover:bg-neutral-800 hover:text-white">
          <Download className="w-4 h-4 mr-2" /> Download Transcript
        </Button>
      </Card>
    </div>
  )
  if (viewState === "ERROR") return <div className="h-screen bg-neutral-950 text-white flex items-center justify-center text-red-500">{error}</div>

  if (viewState === "PERMISSIONS" || viewState === "GREETING") return (
    <div className="h-screen bg-neutral-950 text-white flex items-center justify-center p-4">
      <Card className="max-w-lg w-full p-8 text-center bg-neutral-900 border-neutral-800 shadow-2xl">
        {viewState === "PERMISSIONS" ? (
          <>
            <h2 className="text-xl font-bold mb-4 text-white">System Check</h2>
            <div className="flex justify-center gap-8 mb-8 opacity-70">
              <div className="flex flex-col items-center gap-2"><Video className="w-6 h-6" /><span className="text-xs">Camera</span></div>
              <div className="flex flex-col items-center gap-2"><Mic className="w-6 h-6" /><span className="text-xs">Audio</span></div>
            </div>
            <Button onClick={checkPermissions} className="w-full bg-white text-black hover:bg-neutral-200">Allow Access</Button>
          </>
        ) : (
          <>
            <div className="aspect-video bg-black rounded-lg overflow-hidden border border-neutral-800 mb-6 relative">
              <PreviewCamera />
            </div>
            <h2 className="text-xl font-bold mb-2 text-white">Ready?</h2>
            <Button onClick={startInterview} className="w-full bg-blue-600 hover:bg-blue-700 text-white">Start Interview</Button>
          </>
        )}
      </Card>
    </div>
  )

  return (
    <div className="h-screen w-full bg-neutral-950 text-white overflow-hidden flex flex-col relative">
      <audio ref={audioElRef} className="hidden" crossOrigin="anonymous" />

      {isProcessing && (
        <div className="absolute inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center cursor-wait">
          <div className="bg-neutral-900 p-8 rounded-3xl border border-neutral-800 flex flex-col items-center gap-4 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full"></div>
              <Loader2 className="w-10 h-10 animate-spin text-blue-500 relative z-10" />
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-white">Processing Answer</p>
              <p className="text-xs text-neutral-500 mt-1">Please wait...</p>
            </div>
          </div>
        </div>
      )}

      <div className="absolute top-4 left-4 z-20">
        <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 px-3 py-1 rounded-full backdrop-blur-md">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-[10px] font-bold text-red-400 uppercase tracking-widest">Live</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-4 w-full max-w-4xl mx-auto h-full">
        <div className="w-full text-center mb-4 z-10 space-y-2">
          <h3 className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">Current Question</h3>
          {currentQuestion && (
            <h1 className="text-xl md:text-2xl font-medium leading-snug text-white drop-shadow-md px-4">
              {currentQuestion.question_text}
            </h1>
          )}
        </div>

        <div className="relative w-full aspect-video bg-neutral-900 rounded-2xl overflow-hidden shadow-2xl border border-neutral-800 ring-1 ring-white/5 max-h-[70vh]">
          <InterviewAnswerRecorder
            stream={streamRef.current}
            onSubmit={handleAnswerSubmit}
            isLoading={isProcessing}
            subtitle={currentSubtitle}
          />
        </div>
      </div>
    </div>
  )
}

function PreviewCamera() {
  const videoRef = useRef<HTMLVideoElement>(null)
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true }).then(s => {
      if (videoRef.current) videoRef.current.srcObject = s
    })
  }, [])
  return <video ref={videoRef} autoPlay muted className="w-full h-full object-cover transform scale-x-[-1]" />
}