"// frontend/components/interview/transcription-view.tsx"
interface Props {
  transcript: string
}

export function InterviewTranscriptionView({ transcript }: Props) {
  return (
    <div className="p-4 rounded-md border bg-background h-56 overflow-auto text-sm whitespace-pre-wrap">
      {transcript || "Your live transcript will appear here as you speak."}
    </div>
  )
}

