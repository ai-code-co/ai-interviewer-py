"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Video, FileText, CheckCircle, XCircle, Trophy, Ban } from "lucide-react"
import { updateCandidateStatus } from "@/lib/api/client"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"

interface InterviewResultCardProps {
  interview?: {
    status: string
    video_url?: string
    transcript_url?: string
    completed_at?: string // Needed for logic
  }
  candidateId: string
  candidateStatus?: string
  statusUpdatedAt?: string | null // Needed for logic
  onStatusUpdate?: () => void
}

export function InterviewResultCard({ 
  interview, 
  candidateId, 
  candidateStatus, 
  statusUpdatedAt, 
  onStatusUpdate 
}: InterviewResultCardProps) {
  
  const [modalOpen, setModalOpen] = useState(false)
  const [actionType, setActionType] = useState<"HIRED" | "REJECTED">("HIRED")
  const [message, setMessage] = useState("")
  const [loading, setLoading] = useState(false)

  if (!interview || interview.status !== "COMPLETED") return null

  // --- LOGIC: Determine if a Final Decision has been made ---
  // If the status was updated AFTER the interview finished, it's a Final Decision.
  // If the status is from BEFORE the interview (e.g. the invite approval), it's Pending.
  const interviewTime = interview.completed_at ? new Date(interview.completed_at).getTime() : 0
  const statusTime = statusUpdatedAt ? new Date(statusUpdatedAt).getTime() : 0
  
  const isFinalDecisionMade = statusTime > interviewTime
  
  const isHired = isFinalDecisionMade && candidateStatus === 'APPROVED'
  const isRejected = isFinalDecisionMade && candidateStatus === 'REJECTED'

  const handleAction = (type: "HIRED" | "REJECTED") => {
    setActionType(type)
    setMessage(type === "HIRED" 
      ? "We are pleased to offer you the position. Let's discuss the next steps." 
      : "Thank you for the interview. However, we have decided to move forward with other candidates.")
    setModalOpen(true)
  }

  const submitDecision = async () => {
    setLoading(true)
    try {
      const statusToSend = actionType === "HIRED" ? "APPROVED" : "REJECTED"
      await updateCandidateStatus(candidateId, statusToSend, message)
      setModalOpen(false)
      window.location.reload()
    } catch (error) {
      console.error(error)
      alert("Failed to send email.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Card className="border shadow-sm">
        <CardHeader className="pb-4 border-b">
          <CardTitle className="flex items-center gap-2 text-primary">
            <Video className="h-5 w-5" />
            Interview Recording
          </CardTitle>
          <CardDescription>Review the full interview session and transcript</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          
          {/* Video Player */}
          {interview.video_url ? (
            <div className="rounded-lg overflow-hidden border bg-black shadow-sm aspect-video relative group">
              <video src={interview.video_url} controls className="w-full h-full"/>
            </div>
          ) : (
            <div className="p-4 bg-muted rounded-md text-center text-sm text-muted-foreground border border-dashed">
              Video processing or not available.
            </div>
          )}

          {/* Actions Footer */}
          <div className="flex flex-col sm:flex-row gap-4 justify-between items-center pt-2">
            
            {/* Transcript Button */}
            {interview.transcript_url && (
              <a href={interview.transcript_url} target="_blank" rel="noreferrer" className="w-full sm:w-auto">
                <Button variant="outline" className="gap-2 w-full sm:w-auto">
                  <FileText className="h-4 w-4" /> Transcript PDF
                </Button>
              </a>
            )}

            {/* Decision Controls */}
            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              
              {isHired ? (
                  // STATE: HIRED (Permanent)
                  <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 px-4 py-2 rounded-md">
                      <Trophy className="h-5 w-5 text-green-600" /> 
                      <span className="text-green-700 font-semibold">Candidate Hired</span>
                  </div>
              ) : isRejected ? (
                  // STATE: REJECTED (Permanent)
                  <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 px-4 py-2 rounded-md">
                      <Ban className="h-5 w-5 text-red-600" />
                      <span className="text-red-700 font-semibold">Candidate Rejected</span>
                  </div>
              ) : (
                  // STATE: PENDING (Buttons)
                  <>
                    <Button 
                        onClick={() => handleAction("REJECTED")} 
                        variant="outline" 
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                    >
                        <XCircle className="h-4 w-4 mr-2" /> Reject
                    </Button>
                    
                    <Button 
                        onClick={() => handleAction("HIRED")} 
                        className="bg-green-600 hover:bg-green-700 text-white"
                    >
                        <CheckCircle className="h-4 w-4 mr-2" /> Select & Offer
                    </Button>
                  </>
              )}
            </div>
          </div>

        </CardContent>
      </Card>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{actionType === "HIRED" ? "Extend Offer" : "Reject Candidate"}</DialogTitle>
            <DialogDescription>
                This action is final. It will update the status and send an email.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium mb-2 block">Email Message</label>
            <Textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={5}/>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={submitDecision} disabled={loading} className={actionType === "HIRED" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"}>
              {loading ? "Sending..." : "Confirm Decision"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}