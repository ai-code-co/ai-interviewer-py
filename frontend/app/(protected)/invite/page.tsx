"use client"

import { useEffect, useState } from "react"
import { InviteFormModal } from "@/components/invite/invite-form-modal"
import { BulkInviteModal } from "@/components/invite/bulk-invite-modal" // <--- IMPORT THIS
import { InvitedCandidatesList } from "@/components/invite/invited-candidates-list"
import { apiRequest } from "@/lib/api/client"
import { useAuth } from "@/components/auth/auth-provider"
import type { InvitedCandidate } from "@/lib/types/api"

export default function InvitePage() {
  const [invitedCandidates, setInvitedCandidates] = useState<InvitedCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { user } = useAuth()

  const fetchInvitedCandidates = async () => {
    if (!user?.id) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await apiRequest<InvitedCandidate[]>(`/invites?issued_by=${user.id}`)
      setInvitedCandidates(data)
    } catch (err: any) {
      setError(err.message || "Failed to fetch invited candidates")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.id) {
      fetchInvitedCandidates()
    }
  }, [user?.id])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Invite Candidates</h1>
            <p className="text-muted-foreground">
              Send invitations to candidates to apply for your job openings
            </p>
          </div>
          <div className="flex gap-2">
            <InviteFormModal onSuccess={fetchInvitedCandidates} />
            <BulkInviteModal />
          </div>
        </div>
        <div className="text-center py-8">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Invite Candidates</h1>
          <p className="text-muted-foreground">
            Send invitations to candidates to apply for your job openings
          </p>
        </div>
        <div className="flex gap-2">
            {/* Single Invite */}
            <InviteFormModal onSuccess={fetchInvitedCandidates} />
            
            {/* Bulk Invite */}
            <BulkInviteModal />
        </div>
      </div>

      {error ? (
        <div className="text-center py-8">
          <p className="text-destructive">{error}</p>
          <button
            onClick={fetchInvitedCandidates}
            className="mt-4 text-primary hover:underline"
          >
            Try again
          </button>
        </div>
      ) : (
        <InvitedCandidatesList candidates={invitedCandidates} />
      )}
    </div>
  )
}