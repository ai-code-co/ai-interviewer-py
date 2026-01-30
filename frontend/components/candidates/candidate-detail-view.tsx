"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Mail, Phone, Calendar, FileText, Download } from "lucide-react"
import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import type { CandidateDetail } from "@/lib/types/api"
import { AIEvaluationCard } from "./ai-evaluation-card"
import { CandidateStatusActions } from "./candidate-status-actions"
import { InterviewResultCard } from "./interview-result-card"
import { InterviewEvaluationCard } from "./Interview-evaluation-card"

interface CandidateDetailViewProps {
  candidate: CandidateDetail
  isLoadingEvaluation?: boolean
  onStatusUpdate?: () => void
}

export function CandidateDetailView({ candidate, isLoadingEvaluation, onStatusUpdate }: CandidateDetailViewProps) {
  
  // Check if interview data is available
  const hasInterviewData = candidate.interview && candidate.interview.status === "COMPLETED"
  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link href="/candidates">
        <Button variant="outline" className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Candidates
        </Button>
      </Link>

      <div className="grid gap-6 md:grid-cols-2 mt-4">
        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Candidate contact details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p className="text-lg font-semibold">{candidate.name}</p>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Email</p>
                <p className="text-base">{candidate.email}</p>
              </div>
            </div>
            {candidate.phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Phone</p>
                  <p className="text-base">{candidate.phone}</p>
                </div>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Applied</p>
                <p className="text-base">
                  {formatDistanceToNow(new Date(candidate.created_at), {
                    addSuffix: true,
                  })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Job Information */}
        <Card>
          <CardHeader>
            <CardTitle>Job Position</CardTitle>
            <CardDescription>Position applied for</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Job Title</p>
              <p className="text-lg font-semibold">{candidate.job.title}</p>
            </div>
            {candidate.job.description && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Description
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap max-h-32 overflow-y-auto">
                  {candidate.job.description}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Documents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Documents
          </CardTitle>
          <CardDescription>Resume and uploaded documents</CardDescription>
        </CardHeader>
        <CardContent>
          {candidate.documents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents uploaded</p>
          ) : (
            <div className="space-y-3">
              {candidate.documents.map((doc) => {
                const fileName = doc.storage_path.split("/").pop() || "resume"
                const fileUrl = doc.url

                return (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium truncate max-w-[200px]">{fileName}</p>
                        <p className="text-xs text-muted-foreground">
                          Uploaded{" "}
                          {formatDistanceToNow(new Date(doc.uploaded_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                    </div>
                    {fileUrl && (
                      <a
                        href={fileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-primary hover:underline"
                      >
                        <Download className="h-4 w-4" />
                        Download
                      </a>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Resume Evaluation */}
      <AIEvaluationCard 
        evaluation={candidate.evaluation} 
        isLoading={isLoadingEvaluation}
      />
       
      
      {/* AI Interview  Evaluation */}
      <InterviewEvaluationCard
       evaluation={candidate.ai_interview_report} 
       isLoading={isLoadingEvaluation}
      />
      
      {/* --- DECISION SECTION --- */}
      
      {hasInterviewData ? (
        <div className="animate-in fade-in slide-in-from-bottom-4">
            <InterviewResultCard 
                interview={candidate.interview} 
                candidateId={candidate.id}
                candidateStatus={candidate.status} 
                statusUpdatedAt={candidate.status_updated_at} // <--- PASS THIS
                onStatusUpdate={onStatusUpdate}
            />
        </div>
      ) : (
        // SCENARIO 2: No Interview Yet -> Show Initial Screening Card
        <Card className="border-l-4 border-l-blue-500">
            <CardHeader>
            <CardTitle>Application Screening</CardTitle>
            <CardDescription>
                Initial Review. Approving will send an interview invitation to the candidate.
            </CardDescription>
            </CardHeader>
            <CardContent>
            <CandidateStatusActions 
                candidate={candidate} 
                onStatusUpdate={onStatusUpdate}
            />
            </CardContent>
        </Card>
      )}

    </div>
  )
}