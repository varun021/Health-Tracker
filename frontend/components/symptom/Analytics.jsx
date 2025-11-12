// import { SectionCards } from "@/components/section-cards";
// import { ChartAreaInteractive } from "@/components/chart-area-interactive";

// export function Analytics() {
//   return (
//     <div className="@container/main flex flex-1 flex-col gap-2">
//       <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
//         <SectionCards />
//         <div className="px-4 lg:px-6">
//           <ChartAreaInteractive />
//         </div>
//       </div>
//     </div>
//   );
// }

"use client";
import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Loader2,
  Activity,
  Stethoscope,
  TrendingUp,
  HeartPulse,
  Thermometer,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { userApi } from "@/lib/api-services";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);
  const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const res = await userApi.getAnalytics(days);
        setData(res);
      } catch (err) {
        console.error("Error fetching analytics:", err);
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [days]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen text-gray-600">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mb-2" />
        <span>Loading health analytics...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <Alert variant="destructive" className="max-w-md mx-auto mt-20">
        <AlertDescription>
          Failed to load analytics data. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  const { overview, trends, disease_analytics, symptom_analytics, health_score } = data;

  return (
    <div className="max-w-7xl mx-auto py-10 space-y-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">Health Analytics Dashboard</h1>
        <Select value={days.toString()} onValueChange={(v) => setDays(Number(v))}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Overview Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <OverviewCard
          title="Total Predictions"
          value={overview.total_predictions}
          icon={<Activity className="w-5 h-5 text-blue-600" />}
          color="text-blue-600"
        />
        <OverviewCard
          title="Average Severity"
          value={`${overview.avg_severity.toFixed(1)}%`}
          icon={<HeartPulse className="w-5 h-5 text-orange-500" />}
          color="text-orange-500"
        />
        <OverviewCard
          title="Health Score"
          value={health_score.toFixed(2)}
          icon={<TrendingUp className="w-5 h-5 text-green-600" />}
          color="text-green-600"
        />
        <OverviewCard
          title="Most Common Disease"
          value={overview.most_common_disease || "—"}
          icon={<Stethoscope className="w-5 h-5 text-purple-600" />}
          color="text-purple-600"
        />
      </div>

      {/* Severity Trend */}
      <Card className="border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-indigo-700">
            <TrendingUp className="w-5 h-5" /> Severity Trend ({days} days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="avg_severity"
                  stroke="#3b82f6"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 py-10">
              No severity trend data available.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Disease & Symptom Distribution */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Disease Occurrences */}
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-700">
              <Stethoscope className="w-5 h-5" /> Disease Occurrences
            </CardTitle>
          </CardHeader>
          <CardContent>
            {disease_analytics.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={disease_analytics}
                    dataKey="occurrences"
                    nameKey="disease"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {disease_analytics.map((_, index) => (
                      <Cell
                        key={index}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 py-10">
                No disease data available.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Top Symptoms */}
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <Thermometer className="w-5 h-5" /> Top Symptoms
            </CardTitle>
          </CardHeader>
          <CardContent>
            {symptom_analytics.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={symptom_analytics.slice(0, 5)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="symptom" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="frequency" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 py-10">
                No symptom data available.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/* Reusable Card for Overview Stats */
function OverviewCard({ title, value, icon, color }) {
  return (
    <Card className="border hover:shadow-md transition-all">
      <CardHeader className="flex items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-gray-700">
          {icon} {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className={`text-3xl font-bold ${color}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
