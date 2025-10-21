import { IconTrendingDown, IconTrendingUp, IconHeartbeat, IconUserCheck, IconAlertTriangle, IconPercentage } from "@tabler/icons-react"
import { useEffect, useState } from "react"
import { userApi } from "@/lib/api-services"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export function SectionCards() {
  const [analytics, setAnalytics] = useState(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await userApi.getAnalytics()
        setAnalytics(data)
      } catch (error) {
        console.error("Failed to fetch analytics:", error)
      }
    }
    fetchAnalytics()
  }, [])

  if (!analytics) return null

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Health Score</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {analytics.health_score.toFixed(1)}
          </CardTitle>
          <CardAction>
            <Badge variant={analytics.health_score > 50 ? "outline" : "destructive"}>
              <IconHeartbeat className="size-4" />
              {analytics.health_score > 50 ? "Good" : "Needs Attention"}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Overall Health Assessment
          </div>
          <div className="text-muted-foreground">
            Based on recent predictions and trends
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Total Predictions</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {analytics.overview.total_predictions}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconUserCheck className="size-4" />
              Active
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Total assessments made
          </div>
          <div className="text-muted-foreground">
            Most common: {analytics.overview.most_common_disease}
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Risk Level</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {analytics.overview.severity_distribution.risky || 0}
          </CardTitle>
          <CardAction>
            <Badge variant="destructive">
              <IconAlertTriangle className="size-4" />
              High Risk Cases
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Cases requiring attention
          </div>
          <div className="text-muted-foreground">
            Average severity: {analytics.overview.avg_severity.toFixed(1)}%
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Moderate Cases</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {analytics.overview.severity_distribution.moderate || 0}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconPercentage className="size-4" />
              {((analytics.overview.severity_distribution.moderate || 0) / analytics.overview.total_predictions * 100).toFixed(1)}%
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Moderate risk level cases
          </div>
          <div className="text-muted-foreground">
            Requires regular monitoring
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
