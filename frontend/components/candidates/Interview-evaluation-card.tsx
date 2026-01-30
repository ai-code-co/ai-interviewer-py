"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Brain, CheckCircle2, XCircle, AlertTriangle, Check, Loader2 } from "lucide-react"
import type { InterviewEvaluation } from "@/lib/types/api"

interface InterviewEvaluationCardProps {
    evaluation?: InterviewEvaluation | null
    isLoading?: boolean
}

export function InterviewEvaluationCard({ evaluation, isLoading }: InterviewEvaluationCardProps) {

    // 1. Recommendation Badge Logic
    const getRecommendationBadge = (recommendation: string) => {
        const rec = recommendation.toUpperCase().replace(" ", "_");
        switch (rec) {
            case "STRONG_MATCH":
                return <Badge className="bg-green-600">Strong Match</Badge>
            case "POTENTIAL_MATCH":
                return <Badge className="bg-yellow-600 text-white">Potential Match</Badge>
            case "WEAK_MATCH":
            case "NO_MATCH":
                return <Badge variant="destructive">No Match</Badge>
            default:
                return <Badge variant="secondary">{recommendation}</Badge>
        }
    }

    // 2. Loading State
    if (isLoading) {
        return (
            <Card className="border-primary/20 shadow-lg">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Brain className="h-5 w-5 text-primary" />
                        Interview AI Evaluation
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                    <p className="text-sm text-muted-foreground">Generating interview report...</p>
                </CardContent>
            </Card>
        )
    }

    // 3. Early return if no data
    if (!evaluation) return null;

    return (
        <Card className="border-primary/20 shadow-md bg-card/50 backdrop-blur-sm">
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="flex items-center gap-2 text-xl">
                            <Brain className="h-6 w-6 text-primary" />
                            AI Evaluation
                        </CardTitle>
                        <CardDescription>AI-powered candidate evaluation</CardDescription>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="space-y-8">
                {/* Score and Recommendation Section */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Match Score</p>
                        <div className="flex items-baseline gap-1">
                            <span className="text-4xl font-extrabold">{evaluation.score}</span>
                            <span className="text-muted-foreground font-medium">/ 100</span>
                        </div>
                    </div>
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Recommendation</p>
                        <div className="mt-2">{getRecommendationBadge(evaluation.recommendation)}</div>
                    </div>
                </div>

                {/* Summary Section */}
                <div>
                    <p className="text-sm font-bold text-foreground mb-2">Summary</p>
                    <p className="text-sm leading-relaxed text-muted-foreground italic">
                        "{evaluation.summary}"
                    </p>
                </div>

                {/* Matched Skills */}
                {evaluation.matched_skills?.length > 0 && (
                    <div>
                        <p className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                            Matched Skills
                        </p>
                        <div className="grid gap-2">
                            {evaluation.matched_skills.map((item, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-sm group">
                                    <span className="text-green-500 mt-1">•</span>
                                    <p className="text-muted-foreground">
                                        <span className="font-bold text-foreground">{item.skill}:</span> {item.reason}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Missing Skills */}
                {evaluation.missing_skills?.length > 0 && (
                    <div>
                        <p className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                            <XCircle className="h-4 w-4 text-orange-500" />
                            Missing Skills
                        </p>
                        <div className="grid gap-2">
                            {evaluation.missing_skills.map((item, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-sm">
                                    <span className="text-orange-500 mt-1">•</span>
                                    <p className="text-muted-foreground">
                                        <span className="font-bold text-foreground">{item.skill}:</span> {item.reason}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Strengths and Improvements Grid */}
                <div className="grid md:grid-cols-2 gap-6 pt-4 border-t border-border/50">
                    {/* Strengths */}
                    <div className="space-y-3">
                        <p className="text-sm font-bold text-foreground">Strengths</p>
                        {evaluation.strengths?.map((s, i) => (
                            <div key={i} className="flex items-start gap-3 bg-green-500/5 p-3 rounded-lg border border-green-500/10">
                                <Check className="h-4 w-4 text-green-500 mt-0.5" />
                                <div>
                                    <p className="text-sm font-bold text-foreground leading-none">{s.header}</p>
                                    <p className="text-xs text-muted-foreground mt-1.5">{s.detail}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Areas for Improvement */}
                    <div className="space-y-3">
                        <p className="text-sm font-bold text-foreground">Areas for Improvement</p>
                        {evaluation.areas_for_improvement?.map((a, i) => (
                            <div key={i} className="flex items-start gap-3 bg-yellow-500/5 p-3 rounded-lg border border-yellow-500/10">
                                <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                                <div>
                                    <p className="text-sm font-bold text-foreground leading-none">{a.header}</p>
                                    <p className="text-xs text-muted-foreground mt-1.5">{a.detail}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Disclaimer Footer */}
                <div className="pt-6 border-t border-border/50">
                    <p className="text-[10px] text-muted-foreground/60 uppercase tracking-widest text-center">
                        * This evaluation is AI-generated and should be used as a reference tool. Final hiring decisions should be made by human recruiters.
                    </p>
                </div>
            </CardContent>
        </Card>
    )
}