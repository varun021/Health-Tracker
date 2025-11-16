"use client";

import { useEffect, useState } from "react";
import { create } from "zustand";
import api from "@/lib/axios-config";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


// ======================================================
//                 ZUSTAND STORE (unchanged)
// ======================================================
const useReportsStore = create((set) => ({
  loading: false,
  comparison: null,
  recommendations: null,
  history: null,
  historyPage: 1,

  fetchComparison: async () => {
    const res = await api.get("/api/predictions/comparison_report/");
    set({ comparison: res.data });
  },

  fetchRecommendations: async () => {
    const res = await api.get("/api/predictions/recommendations_based_on_history/");
    set({ recommendations: res.data });
  },

  fetchHistory: async (page = 1) => {
    const res = await api.get(`/api/predictions/history/?page=${page}&page_size=10`);
    set({ history: res.data, historyPage: page });
  },

  generateReport: async ({ format }) => {
    const res = await api.post(
      "/api/predictions/generate_report/",
      { format },
      { responseType: format === "json" ? "json" : "blob" }
    );
    return res;
  },
}));


// ======================================================
//                      PAGE UI
// ======================================================

export default function ReportsPage() {
  const {
    comparison,
    recommendations,
    history,
    historyPage,
    fetchComparison,
    fetchRecommendations,
    fetchHistory,
    generateReport,
  } = useReportsStore();

  const [format, setFormat] = useState("pdf");

  useEffect(() => {
    fetchComparison();
    fetchRecommendations();
    fetchHistory(1);
  }, []);

  const downloadReport = async () => {
    const res = await generateReport({ format });

    if (format === "json") {
      console.log(res.data);
      return;
    }

    const blob = new Blob(
      [res.data],
      { type: format === "pdf" ? "application/pdf" : "text/csv" }
    );

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `health_report.${format}`;
    a.click();
  };


  return (
    <div className="min-h-screen p-6 bg-background text-foreground space-y-6">

      <h1 className="text-3xl font-bold">Reports & Analytics</h1>


      {/* ======================================================
                      COMPARISON REPORT
      ======================================================= */}
      {comparison && (
        <Card className="p-5 border border-border bg-card text-card-foreground">
          <h2 className="text-xl font-bold mb-3">Comparison Report</h2>

          <p className="mb-1 text-muted-foreground">
            <strong>Current:</strong> {comparison.current_period.start} → {comparison.current_period.end}
          </p>

          <p className="text-muted-foreground">
            Total: {comparison.current_period.stats.total_predictions} <br />
            Avg Severity: {comparison.current_period.stats.avg_severity}
          </p>

          <div className="border-t border-border my-4"></div>

          <h3 className="text-lg font-semibold mb-2">Changes</h3>

          {Object.entries(comparison.changes).map(([key, val]) => (
            <div key={key} className="flex justify-between text-muted-foreground">
              <span className="capitalize">{key}</span>
              <span className={val.direction === "up" ? "text-red-500" : "text-green-500"}>
                {val.value}% ({val.direction})
              </span>
            </div>
          ))}
        </Card>
      )}



      {/* ======================================================
                    AI RECOMMENDATIONS
      ======================================================= */}
      {recommendations && (
        <Card className="p-5 border border-border bg-card text-card-foreground">
          <h2 className="text-xl font-bold mb-2"> Recommendations</h2>

          <p className="text-muted-foreground mb-3">
            Health Score:{" "}
            <span className="font-bold text-foreground">{recommendations.health_score}</span>
          </p>

          {recommendations.recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="border border-border p-3 rounded mb-3 bg-muted/20"
            >
              <p className="text-xs uppercase text-muted-foreground">{rec.category}</p>
              <h3 className="text-lg font-semibold">{rec.title}</h3>
              <p className="text-muted-foreground">{rec.message}</p>
              <p className="text-xs text-muted-foreground mt-1">Action: {rec.action}</p>
            </div>
          ))}
        </Card>
      )}



      {/* ======================================================
                    PREDICTION HISTORY
      ======================================================= */}
      {history && (
        <Card className="p-5 border border-border bg-card text-card-foreground">
          <h2 className="text-xl font-bold mb-4">Prediction History</h2>

          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="py-2">Date</th>
                <th>Disease</th>
                <th>Severity</th>
                <th>Category</th>
              </tr>
            </thead>

            <tbody>
              {history.results.map((row) => (
                <tr key={row.id} className="border-b border-border">
                  <td className="py-2">{row.created_at.split("T")[0]}</td>
                  <td>{row.primary_prediction || "-"}</td>
                  <td>{row.severity_score}</td>
                  <td>{row.severity_category}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="flex justify-center items-center mt-4 gap-4">
            <Button
              variant="outline"
              disabled={historyPage === 1}
              onClick={() => fetchHistory(historyPage - 1)}
            >
              Prev
            </Button>

            <span className="text-muted-foreground">
              Page {historyPage} / {history.total_pages}
            </span>

            <Button
              variant="outline"
              disabled={historyPage === history.total_pages}
              onClick={() => fetchHistory(historyPage + 1)}
            >
              Next
            </Button>
          </div>
        </Card>
      )}



      {/* ======================================================
                      REPORT GENERATOR
      ======================================================= */}
      <Card className="p-5 border border-border bg-card text-card-foreground">
        <h2 className="text-xl font-bold mb-4">Generate Report</h2>

        <div className="flex items-center gap-4">
          <select
            onChange={(e) => setFormat(e.target.value)}
            className="bg-muted text-foreground border border-border px-3 py-2 rounded"
          >
            <option value="pdf">PDF</option>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>

          <Button
            className="bg-foreground text-background hover:opacity-80"
            onClick={downloadReport}
          >
            Download
          </Button>
        </div>
      </Card>

    </div>
  );
}
