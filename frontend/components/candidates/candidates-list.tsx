"use client"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { formatDistanceToNow } from "date-fns"
import Link from "next/link"
import { useRouter } from "next/navigation"
import type { CandidateWithJob } from "@/lib/types/api"

interface CandidatesListProps {
  candidates: CandidateWithJob[]
}

export function CandidatesList({ candidates }: CandidatesListProps) {
  const router = useRouter()

  if (candidates.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Candidates</CardTitle>
          <CardDescription>List of all candidates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p>No candidates have applied yet.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidates</CardTitle>
        <CardDescription>List of all candidates who have applied</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Job Position</TableHead>
              <TableHead>Applied</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {candidates.map((candidate) => (
              <TableRow
                key={candidate.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/candidates/${candidate.id}`)}
              >
                <TableCell className="font-medium">{candidate.name}</TableCell>
                <TableCell>{candidate.email}</TableCell>
                <TableCell>{candidate.job.title}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(candidate.created_at), {
                    addSuffix: true,
                  })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
