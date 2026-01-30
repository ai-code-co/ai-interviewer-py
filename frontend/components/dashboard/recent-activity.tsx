import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, UserPlus, Mail, Briefcase } from "lucide-react"
import { formatDistanceToNow } from "date-fns"

const activities = [
  {
    type: "candidate_applied",
    message: "New candidate applied for Senior Full Stack Developer",
    icon: UserPlus,
    time: "2 hours ago",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
  },
  {
    type: "invitation_sent",
    message: "Invitation sent to candidate@example.com",
    icon: Mail,
    time: "5 hours ago",
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
  },
  {
    type: "job_created",
    message: "New job created: Product Manager",
    icon: Briefcase,
    time: "1 day ago",
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
  },
  {
    type: "candidate_replied",
    message: "John Doe replied to Frontend React Developer invitation",
    icon: Activity,
    time: "2 days ago",
    timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
  },
  {
    type: "invitation_sent",
    message: "Invitation sent to jane.smith@example.com",
    icon: Mail,
    time: "3 days ago",
    timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
  },
]

export function RecentActivity() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest updates and events</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity, index) => {
            const Icon = activity.icon
            return (
              <div
                key={index}
                className="flex items-start gap-4 border-b pb-4 last:border-0 last:pb-0"
              >
                <div className="rounded-full bg-muted p-2">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {activity.message}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDistanceToNow(activity.timestamp, { addSuffix: true })}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

