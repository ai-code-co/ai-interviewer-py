"// frontend/app/interview/[token]/page.tsx"
"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { InterviewShell } from "@/components/interview/interview-shell"

export default function InterviewPage() {
  const params = useParams<{ token: string }>()
  const token = params?.token as string | undefined

  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError("Invalid interview link")
      setIsReady(true)
      return
    }
    // In a full implementation, we would validate the token and fetch session info here.
    setIsReady(true)
  }, [token])

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Preparing your interview...</p>
      </div>
    )
  }

  if (error || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-destructive">{error ?? "Invalid interview link"}</p>
      </div>
    )
  }

  return <InterviewShell token={token} />
}

