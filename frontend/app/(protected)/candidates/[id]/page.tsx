"use client"

import { useEffect, useState, useRef } from "react"
import { CandidateDetailView } from "@/components/candidates/candidate-detail-view"
import { apiRequest } from "@/lib/api/client"
import type { CandidateDetail } from "@/lib/types/api"
import { useParams } from "next/navigation"

export default function CandidateDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const handleStatusUpdate = async () => {
    // Refresh candidate data after status update
    try {
      const data = await apiRequest<CandidateDetail>(`/candidates/${id}`)
      setCandidate(data)
    } catch (err: any) {
      console.error("Error refreshing candidate:", err)
    }
  }

  useEffect(() => {
    if (!id) return

    const fetchCandidate = async () => {
      try {
        setError(null)
        const data = await apiRequest<CandidateDetail>(`/candidates/${id}`)
        setCandidate(data)
        
        // Stop polling if evaluation is completed or failed
        if (data.evaluation && (data.evaluation.status === "COMPLETED" || data.evaluation.status === "FAILED")) {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to fetch candidate")
      } finally {
        setLoading(false)
      }
    }

    // Initial fetch
    setLoading(true)
    fetchCandidate()

    // Cleanup on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [id])

  // Poll for evaluation updates if evaluation is pending
  useEffect(() => {
    if (!candidate?.evaluation || candidate.evaluation.status !== "PENDING") {
      return
    }

    // Start polling if not already polling
    if (!pollingIntervalRef.current) {
      pollingIntervalRef.current = setInterval(async () => {
        try {
          const data = await apiRequest<CandidateDetail>(`/candidates/${id}`)
          setCandidate(data)
          
          // Stop polling if evaluation is completed or failed
          if (data.evaluation && (data.evaluation.status === "COMPLETED" || data.evaluation.status === "FAILED")) {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current)
              pollingIntervalRef.current = null
            }
          }
        } catch (err) {
          // Silently fail polling - don't show errors
          console.error("Error polling candidate:", err)
        }
      }, 5000)
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [candidate?.evaluation?.status, id])

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Candidate Details</h1>
          <p className="text-muted-foreground">
            View detailed information about the candidate
          </p>
        </div>
        <div className="text-center py-8">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
          <p className="mt-4 text-muted-foreground">Loading candidate...</p>
        </div>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Candidate Details</h1>
          <p className="text-muted-foreground">
            View detailed information about the candidate
          </p>
        </div>
        <div className="text-center py-8">
          <p className="text-destructive">{error || "Candidate not found"}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Candidate Details</h1>
        <p className="text-muted-foreground">
          View detailed information about the candidate
        </p>
      </div>

      <CandidateDetailView 
        candidate={candidate} 
        isLoadingEvaluation={candidate.evaluation?.status === "PENDING"}
        onStatusUpdate={handleStatusUpdate}
      />

    </div>
  )
}

