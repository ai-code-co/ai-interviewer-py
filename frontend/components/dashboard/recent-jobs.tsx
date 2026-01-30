import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { dummyJobs } from "@/lib/data/dummy-data"
import { formatDistanceToNow } from "date-fns"

export function RecentJobs() {
  const recentJobs = dummyJobs.slice(0, 5)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Jobs</CardTitle>
        <CardDescription>Latest job postings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentJobs.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
            >
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">{job.title}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(job.created_at), {
                    addSuffix: true,
                  })}
                </p>
              </div>
              <Badge
                variant={job.status === "open" ? "default" : "secondary"}
              >
                {job.status}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

