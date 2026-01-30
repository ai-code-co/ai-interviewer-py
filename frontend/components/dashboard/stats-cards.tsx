import { Briefcase, Mail, UserCheck, Clock } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { stats } from "@/lib/data/dummy-data"

const statCards = [
  {
    title: "Total Available Jobs",
    value: stats.totalJobs,
    icon: Briefcase,
    trend: "+12%",
    description: "Open positions",
  },
  {
    title: "Candidates Invited",
    value: stats.candidatesInvited,
    icon: Mail,
    trend: "+8%",
    description: "Total invitations sent",
  },
  {
    title: "Candidates Replied",
    value: stats.candidatesReplied,
    icon: UserCheck,
    trend: "+15%",
    description: "Responses received",
  },
  {
    title: "Pending Invitations",
    value: stats.pendingInvitations,
    icon: Clock,
    trend: "-5%",
    description: "Awaiting response",
  },
]

export function StatsCards() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {statCards.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                <span className="text-green-600 dark:text-green-400">
                  {stat.trend}
                </span>{" "}
                {stat.description}
              </p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

