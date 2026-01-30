"// frontend/components/interview/question-display.tsx"
interface Props {
  question: string
}

export function InterviewQuestionDisplay({ question }: Props) {
  return (
    <div className="p-4 rounded-md bg-muted flex items-start gap-3">
      <div className="font-semibold mt-1">Q:</div>
      <div className="text-base">{question}</div>
    </div>
  )
}

