import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { dummyInvites } from "@/lib/data/dummy-data"

export function InvitationsOverview() {
  const pending = dummyInvites.filter((i) => i.status === "PENDING").length
  const used = dummyInvites.filter((i) => i.status === "USED").length
  const expired = dummyInvites.filter((i) => i.status === "EXPIRED").length
  const total = dummyInvites.length

  const pendingPercentage = total > 0 ? Math.round((pending / total) * 100) : 0
  const usedPercentage = total > 0 ? Math.round((used / total) * 100) : 0
  const expiredPercentage = total > 0 ? Math.round((expired / total) * 100) : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Invitations Overview</CardTitle>
        <CardDescription>Status breakdown of all invitations</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Badge variant="default">PENDING</Badge>
                <span className="text-muted-foreground">{pending} invitations</span>
              </div>
              <span className="font-medium">{pendingPercentage}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${pendingPercentage}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">USED</Badge>
                <span className="text-muted-foreground">{used} invitations</span>
              </div>
              <span className="font-medium">{usedPercentage}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${usedPercentage}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Badge variant="outline">EXPIRED</Badge>
                <span className="text-muted-foreground">{expired} invitations</span>
              </div>
              <span className="font-medium">{expiredPercentage}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-gray-500 transition-all"
                style={{ width: `${expiredPercentage}%` }}
              />
            </div>
          </div>

          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Total Invitations</span>
              <span className="text-2xl font-bold">{total}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

