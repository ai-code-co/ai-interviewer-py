"use client"

import { useEffect, useState } from "react"
import { CandidatesList } from "@/components/candidates/candidates-list"
import { apiRequest } from "@/lib/api/client"
import type { CandidateWithJob } from "@/lib/types/api"

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateWithJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiRequest<CandidateWithJob[]>("/candidates")
        setCandidates(data)
      } catch (err: any) {
        setError(err.message || "Failed to fetch candidates")
      } finally {
        setLoading(false)
      }
    }

    fetchCandidates()
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Candidates</h1>
          <p className="text-muted-foreground">
            View all candidates who have applied for positions
          </p>
        </div>
        <div className="text-center py-8">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
          <p className="mt-4 text-muted-foreground">Loading candidates...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Candidates</h1>
          <p className="text-muted-foreground">
            View all candidates who have applied for positions
          </p>
        </div>
        <div className="text-center py-8">
          <p className="text-destructive">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-primary hover:underline"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Candidates</h1>
        <p className="text-muted-foreground">
          View all candidates who have applied for positions
        </p>
      </div>

      <CandidatesList candidates={candidates} />
    </div>
  )
}

