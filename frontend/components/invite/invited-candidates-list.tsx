import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatDistanceToNow } from "date-fns"
import type { InvitedCandidate } from "@/lib/types/api"

interface InvitedCandidatesListProps {
  candidates: InvitedCandidate[]
}

export function InvitedCandidatesList({ candidates }: InvitedCandidatesListProps) {
  if (candidates.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invited Candidates</CardTitle>
          <CardDescription>List of all candidates you've invited</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p>No invitations sent yet. Click "Invite Candidate" to get started.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getStatusBadge = (candidate: InvitedCandidate) => {
    // Show "Applied" only if candidate has actually submitted the application
    if (candidate.has_applied) {
      return <Badge className="bg-green-500">Applied</Badge>
    }
    
    // Check if expired (either status is EXPIRED or token has expired)
    const expiresAt = new Date(candidate.expires_at)
    const now = new Date()
    if (candidate.status === "EXPIRED" || expiresAt <= now) {
      return <Badge variant="outline">Expired</Badge>
    }
    
    // Otherwise show Pending (token is valid but not used yet)
    return <Badge variant="default">Pending</Badge>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Invited Candidates</CardTitle>
        <CardDescription>List of all candidates you've invited</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Invited</TableHead>
              <TableHead>Expires</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {candidates.map((candidate) => (
              <TableRow key={candidate.id}>
                <TableCell className="font-medium">{candidate.email}</TableCell>
                <TableCell>{getStatusBadge(candidate)}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(candidate.created_at), {
                    addSuffix: true,
                  })}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {candidate.status === "EXPIRED" || 
                   new Date(candidate.expires_at) <= new Date() ? (
                    <span className="text-destructive">Expired</span>
                  ) : (
                    formatDistanceToNow(new Date(candidate.expires_at), {
                      addSuffix: true,
                    })
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}


