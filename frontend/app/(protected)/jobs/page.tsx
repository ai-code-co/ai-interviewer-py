"use client"

import { useEffect, useState } from "react"
import { JobsList } from "@/components/jobs/jobs-list"
import { AddJobButton } from "@/components/jobs/add-job-button"
import { apiRequest } from "@/lib/api/client"
import type { Job } from "@/lib/types/api"

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiRequest<Job[]>("/jobs")
      setJobs(data)
    } catch (err: any) {
      setError(err.message || "Failed to fetch jobs")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Jobs</h1>
            <p className="text-muted-foreground">
              Manage your job postings and recruitment opportunities
            </p>
          </div>
          <AddJobButton />
        </div>
        <div className="text-center py-8">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
          <p className="mt-4 text-muted-foreground">Loading jobs...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Jobs</h1>
            <p className="text-muted-foreground">
              Manage your job postings and recruitment opportunities
            </p>
          </div>
          <AddJobButton />
        </div>
        <div className="text-center py-8">
          <p className="text-destructive">{error}</p>
          <button
            onClick={fetchJobs}
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs</h1>
          <p className="text-muted-foreground">
            Manage your job postings and recruitment opportunities
          </p>
        </div>
        <AddJobButton onSuccess={fetchJobs} />
      </div>

      <JobsList jobs={jobs} onRefresh={fetchJobs} />
    </div>
  )
}
