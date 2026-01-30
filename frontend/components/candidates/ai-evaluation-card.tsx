"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Brain, CheckCircle2, XCircle, AlertCircle, Loader2 } from "lucide-react"
import type { AIEvaluation } from "@/lib/types/api"

interface AIEvaluationCardProps {
  evaluation?: AIEvaluation
  isLoading?: boolean
}

export function AIEvaluationCard({ evaluation, isLoading }: AIEvaluationCardProps) {
  // Helper to check if value is object or array
  const isObject = (value: any): value is Record<string, string> => {
    return typeof value === "object" && value !== null && !Array.isArray(value)
  }

  // Convert object/array to display format
  const formatItems = (items: Record<string, string> | string[]): Array<{ key: string; value: string }> => {
    if (Array.isArray(items)) {
      return items.map((item, idx) => ({
        key: String(idx),
        value: typeof item === "string" ? item : String(item),
      }))
    }
    if (isObject(items)) {
      return Object.entries(items).map(([key, value]) => ({
        key,
        value: String(value),
      }))
    }
    return []
  }

  // Get recommendation badge
  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case "STRONG_MATCH":
        return <Badge className="bg-green-500">Strong Match</Badge>
      case "POTENTIAL_MATCH":
        return <Badge className="bg-yellow-500">Potential Match</Badge>
      case "WEAK_MATCH":
        return <Badge className="bg-orange-500">Weak Match</Badge>
      default:
        return <Badge variant="secondary">{recommendation}</Badge>
    }
  }

  // Loading state
  if (isLoading || !evaluation || evaluation.status === "PENDING") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            AI Evaluation
          </CardTitle>
          <CardDescription>AI-powered candidate evaluation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <div className="text-center">
              <p className="font-medium">Evaluating candidate...</p>
              <p className="text-sm text-muted-foreground mt-1">
                Our AI is analyzing the resume and job requirements
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Failed state
  if (evaluation.status === "FAILED") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            AI Evaluation
          </CardTitle>
          <CardDescription>AI-powered candidate evaluation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div className="text-center">
              <p className="font-medium text-destructive">Evaluation Failed</p>
              <p className="text-sm text-muted-foreground mt-1">
                {evaluation.error_message || "Unable to complete AI evaluation"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Completed state - show results
  const matchedSkills = formatItems(evaluation.matched_skills)
  const missingSkills = formatItems(evaluation.missing_skills)
  const strengths = formatItems(evaluation.strengths)
  const weaknesses = formatItems(evaluation.weaknesses)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          AI Evaluation
        </CardTitle>
        <CardDescription>AI-powered candidate evaluation</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Score and Recommendation */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-1">Match Score</p>
            <div className="flex items-baseline gap-2">
              <div className="text-3xl font-bold">{evaluation.score}</div>
              <div className="text-sm text-muted-foreground">/ 100</div>
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-1">Recommendation</p>
            <div>{getRecommendationBadge(evaluation.recommendation)}</div>
          </div>
        </div>

        {/* Summary */}
        {evaluation.summary && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">Summary</p>
            <p className="text-sm leading-relaxed">{evaluation.summary}</p>
          </div>
        )}

        {/* Matched Skills */}
        {matchedSkills.length > 0 && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Matched Skills
            </p>
            <div className="space-y-1">
              {matchedSkills.map((item) => (
                <div key={item.key} className="flex items-start gap-2 text-sm">
                  <span className="text-green-500">•</span>
                  <span>
                    {isObject(evaluation.matched_skills) ? (
                      <>
                        <span className="font-medium">{item.key}:</span> {item.value}
                      </>
                    ) : (
                      item.value
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Missing Skills */}
        {missingSkills.length > 0 && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
              <XCircle className="h-4 w-4 text-orange-500" />
              Missing Skills
            </p>
            <div className="space-y-1">
              {missingSkills.map((item) => (
                <div key={item.key} className="flex items-start gap-2 text-sm">
                  <span className="text-orange-500">•</span>
                  <span>
                    {isObject(evaluation.missing_skills) ? (
                      <>
                        <span className="font-medium">{item.key}:</span> {item.value}
                      </>
                    ) : (
                      item.value
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Strengths */}
        {strengths.length > 0 && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">Strengths</p>
            <div className="space-y-1">
              {strengths.map((item) => (
                <div key={item.key} className="flex items-start gap-2 text-sm">
                  <span className="text-green-500">✓</span>
                  <span>
                    {isObject(evaluation.strengths) ? (
                      <>
                        <span className="font-medium">{item.key}:</span> {item.value}
                      </>
                    ) : (
                      item.value
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Weaknesses */}
        {weaknesses.length > 0 && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">Areas for Improvement</p>
            <div className="space-y-1">
              {weaknesses.map((item) => (
                <div key={item.key} className="flex items-start gap-2 text-sm">
                  <span className="text-orange-500">⚠</span>
                  <span>
                    {isObject(evaluation.weaknesses) ? (
                      <>
                        <span className="font-medium">{item.key}:</span> {item.value}
                      </>
                    ) : (
                      item.value
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="pt-4 border-t">
          <p className="text-xs text-muted-foreground italic">
            * This evaluation is AI-generated and should be used as a reference tool. 
            Final hiring decisions should be made by human recruiters.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

