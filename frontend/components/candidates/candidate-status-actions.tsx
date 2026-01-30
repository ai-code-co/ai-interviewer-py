"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { updateCandidateStatus } from "@/lib/api/client"
import type { CandidateDetail } from "@/lib/types/api"

interface CandidateStatusActionsProps {
  candidate: CandidateDetail
  onStatusUpdate?: () => void
}

export function CandidateStatusActions({
  candidate,
  onStatusUpdate,
}: CandidateStatusActionsProps) {
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false)
  const [isRejectionModalOpen, setIsRejectionModalOpen] = useState(false)
  const [customMessage, setCustomMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const status = candidate.status || "PENDING"
  const evaluationCompleted =
    candidate.evaluation?.status === "COMPLETED" || candidate.evaluation?.status === "FAILED"

  // Show buttons if status is PENDING or AI evaluation is completed
  const canUpdateStatus = status === "PENDING" || evaluationCompleted

  const handleStatusUpdate = async (newStatus: "APPROVED" | "REJECTED") => {
    setIsLoading(true)
    setError(null)

    try {
      await updateCandidateStatus(candidate.id, newStatus, customMessage || undefined)
      setCustomMessage("")
      setIsApprovalModalOpen(false)
      setIsRejectionModalOpen(false)
      if (onStatusUpdate) {
        onStatusUpdate()
      }
    } catch (err: any) {
      setError(err.message || "Failed to update candidate status")
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = () => {
    switch (status) {
      case "APPROVED":
        return (
          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        )
      case "REJECTED":
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        )
      default:
        return (
          <Badge variant="outline">
            Pending
          </Badge>
        )
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold mb-2">Candidate Status</h3>
          <div className="flex items-center gap-2">
            {getStatusBadge()}
          </div>
        </div>
      </div>

      {canUpdateStatus && (
        <div className="flex gap-2">
          <Button
            onClick={() => setIsApprovalModalOpen(true)}
            disabled={isLoading || status === "APPROVED"}
            className="bg-green-600 hover:bg-green-700"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Approve
          </Button>
          <Button
            onClick={() => setIsRejectionModalOpen(true)}
            disabled={isLoading || status === "REJECTED"}
            variant="destructive"
          >
            <XCircle className="h-4 w-4 mr-2" />
            Reject
          </Button>
        </div>
      )}

      {error && (
        <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
          {error}
        </div>
      )}

      {/* Approval Modal */}
      <Dialog open={isApprovalModalOpen} onOpenChange={setIsApprovalModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Candidate</DialogTitle>
            <DialogDescription>
              Approve {candidate.name} for the {candidate.job.title} position. You can include a
              custom message that will be sent via email.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="approval-message">Custom Message (Optional)</Label>
              <Textarea
                id="approval-message"
                placeholder="Congratulations! We are pleased to inform you..."
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsApprovalModalOpen(false)
                setCustomMessage("")
                setError(null)
              }}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleStatusUpdate("APPROVED")}
              disabled={isLoading}
              className="bg-green-600 hover:bg-green-700"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Approving...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Approve Candidate
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rejection Modal */}
      <Dialog open={isRejectionModalOpen} onOpenChange={setIsRejectionModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Candidate</DialogTitle>
            <DialogDescription>
              Reject {candidate.name} for the {candidate.job.title} position. You can include a
              custom message that will be sent via email.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="rejection-message">Custom Message (Optional)</Label>
              <Textarea
                id="rejection-message"
                placeholder="Thank you for your interest. After careful consideration..."
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsRejectionModalOpen(false)
                setCustomMessage("")
                setError(null)
              }}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleStatusUpdate("REJECTED")}
              disabled={isLoading}
              variant="destructive"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject Candidate
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

