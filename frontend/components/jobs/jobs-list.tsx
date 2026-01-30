import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EditJobButton } from "./edit-job-button"
import { DeleteJobButton } from "./delete-job-button"
import type { Job } from "@/lib/types/api"
import { formatDistanceToNow } from "date-fns"

interface JobsListProps {
  jobs: Job[]
  onRefresh?: () => void
}

export function JobsList({ jobs, onRefresh }: JobsListProps) {
  if (jobs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Jobs</CardTitle>
          <CardDescription>Manage your job postings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p>No jobs found. Create your first job posting!</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Jobs</CardTitle>
        <CardDescription>Manage your job postings</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {jobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell className="font-medium">{job.title}</TableCell>
                <TableCell className="max-w-md truncate">
                  {job.description || (
                    <span className="text-muted-foreground">No description</span>
                  )}
                </TableCell>
                <TableCell>
                  <Badge
                    variant={job.status === "open" ? "default" : "secondary"}
                  >
                    {job.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(job.created_at), {
                    addSuffix: true,
                  })}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <EditJobButton job={job} onSuccess={onRefresh} />
                    <DeleteJobButton job={job} onSuccess={onRefresh} />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

