import { StatsCards } from "@/components/dashboard/stats-cards"
import { RecentJobs } from "@/components/dashboard/recent-jobs"
import { InvitationsOverview } from "@/components/dashboard/invitations-overview"
import { RecentActivity } from "@/components/dashboard/recent-activity"

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your recruitment activities
        </p>
      </div>

      <StatsCards />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="md:col-span-1 lg:col-span-2">
          <RecentJobs />
        </div>
        <div className="md:col-span-1">
          <InvitationsOverview />
        </div>
      </div>

      <RecentActivity />
    </div>
  )
}
