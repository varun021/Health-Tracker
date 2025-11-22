"use client";

import { useEffect, useState } from "react";
import { create } from "zustand";
import api from "@/lib/axios-config";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

// ======================================================
//                 ZUSTAND STORE (extended)
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
    const res = await api.get(
      "/api/predictions/recommendations_based_on_history/"
    );
    set({ recommendations: res.data });
  },

  fetchHistory: async (page = 1) => {
    const res = await api.get(
      `/api/predictions/history/?page=${page}&page_size=10`
    );
    set({ history: res.data, historyPage: page });
  },

  deleteHistory: async (id) => {
    const response = await api.delete(
      `/api/predictions/${id}/delete_history/`
    );
    return response.data;
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
    deleteHistory,
  } = useReportsStore();

  // State
  const [format, setFormat] = useState("pdf");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [selectedRow, setSelectedRow] = useState(null);
  const [localRows, setLocalRows] = useState([]);
  const [removingId, setRemovingId] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load on mount
  useEffect(() => {
    fetchComparison();
    fetchRecommendations();
    fetchHistory(1);
  }, []);

  // Sync rows
  useEffect(() => {
    if (history?.results) setLocalRows(history.results);
    else setLocalRows([]);
  }, [history]);

  // Download Report
  const downloadReport = async () => {
    try {
      const res = await generateReport({ format });

      if (format === "json") {
        console.log(res.data);
        toast("JSON Report", {
          description: "Check console for JSON output.",
        });
        return;
      }

      const blob = new Blob([res.data], {
        type: format === "pdf" ? "application/pdf" : "text/csv",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `health_report.${format}`;
      a.click();

      toast("Report ready", {
        description: `Downloaded ${format.toUpperCase()} report.`,
      });
    } catch (err) {
      console.error(err);
      toast("Report failed", {
        description: "Unable to generate report.",
      });
    }
  };

  // Open confirmation
  const openDeleteConfirm = (row) => {
    setSelectedRow(row);
    setConfirmOpen(true);
  };

  // Handle Delete
  const handleDeleteConfirm = async () => {
    if (!selectedRow) return;
    const id = selectedRow.id;

    try {
      setIsDeleting(true);
      setRemovingId(id);

      await deleteHistory(id);

      setLocalRows((prev) => prev.filter((r) => r.id !== id));

      setTimeout(() => {
        fetchHistory(historyPage);
        fetchRecommendations();
        fetchComparison();
      }, 600);

      toast("Deleted", {
        description: "History record deleted successfully.",
      });
    } catch (err) {
      console.error(err);
      toast("Delete failed", {
        description: "Could not delete history record.",
      });
      setRemovingId(null);
    } finally {
      setIsDeleting(false);
      setConfirmOpen(false);
      setSelectedRow(null);
    }
  };

  const handleDeleteCancel = () => {
    setConfirmOpen(false);
    setSelectedRow(null);
    setRemovingId(null);
  };

  return (
    <div className="min-h-screen p-6 bg-background text-foreground space-y-6">
      <h1 className="text-3xl font-bold">History</h1>

      {/* Comparison Card */}
      {comparison && (
        <Card className="p-5 bg-card border border-border text-card-foreground">
          <h2 className="text-xl font-bold mb-3">Comparison Report</h2>
          <p className="text-muted-foreground mb-2">
            <strong>Current:</strong> {comparison.current_period.start} →{" "}
            {comparison.current_period.end}
          </p>

          <p className="text-muted-foreground">
            Total: {comparison.current_period.stats.total_predictions} <br />
            Avg Severity: {comparison.current_period.stats.avg_severity}
          </p>

          <div className="border-t border-border my-4" />

          <h3 className="text-lg font-semibold mb-2">Changes</h3>

          {Object.entries(comparison.changes).map(([key, val]) => (
            <div key={key} className="flex justify-between text-muted-foreground">
              <span className="capitalize">{key}</span>
              <span
                className={
                  val.direction === "up" ? "text-red-500" : "text-green-500"
                }
              >
                {val.value}% ({val.direction})
              </span>
            </div>
          ))}
        </Card>
      )}

      {/* Recommendations */}
      {recommendations && (
        <Card className="p-5 bg-card border border-border text-card-foreground">
          <h2 className="text-xl font-bold mb-2">Recommendations</h2>

          <p className="text-muted-foreground mb-3">
            Health Score:{" "}
            <span className="font-bold">{recommendations.health_score}</span>
          </p>

          {recommendations.recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="border border-border p-3 rounded mb-3 bg-muted/20"
            >
              <p className="text-xs uppercase text-muted-foreground">
                {rec.category}
              </p>
              <h3 className="text-lg font-semibold">{rec.title}</h3>
              <p className="text-muted-foreground">{rec.message}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Action: {rec.action}
              </p>
            </div>
          ))}
        </Card>
      )}

      {/* Prediction History */}
      {history && (
        <Card className="p-5 bg-card border border-border text-card-foreground">
          <h2 className="text-xl font-bold mb-4">Prediction History</h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="py-2">Date</th>
                  <th>Disease</th>
                  <th>Severity</th>
                  <th>Category</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                <AnimatePresence initial={false}>
                  {localRows.length === 0 ? (
                    <motion.tr
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <td
                        colSpan={5}
                        className="py-6 text-center text-muted-foreground"
                      >
                        No history found.
                      </td>
                    </motion.tr>
                  ) : (
                    localRows.map((row) => (
                      <motion.tr
                        layout
                        key={row.id}
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{
                          opacity: 0,
                          scale: 0.98,
                          height: 0,
                          margin: 0,
                          padding: 0,
                        }}
                        transition={{ duration: 0.35 }}
                        className="border-b border-border"
                      >
                        <td className="py-2">
                          {row.created_at.split("T")[0]}
                        </td>
                        <td>{row.primary_prediction || "-"}</td>
                        <td>{row.severity_score}</td>
                        <td>{row.severity_category}</td>
                        <td>
                          <div className="flex gap-2">
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => openDeleteConfirm(row)}
                              disabled={isDeleting && removingId === row.id}
                            >
                              {isDeleting && removingId === row.id
                                ? "Deleting..."
                                : "Delete"}
                            </Button>
                          </div>
                        </td>
                      </motion.tr>
                    ))
                  )}
                </AnimatePresence>
              </tbody>
            </table>
          </div>

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

      {/* Report Generator */}
      <Card className="p-5 bg-card border border-border text-card-foreground">
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete history record</DialogTitle>
            <DialogDescription>
              Are you sure you want to permanently delete this history record?
              This cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 text-sm text-muted-foreground">
            {selectedRow ? (
              <>
                <strong>{selectedRow.primary_prediction}</strong> —{" "}
                {selectedRow.created_at.split("T")[0]}
              </>
            ) : (
              "No record selected"
            )}
          </div>

          <DialogFooter className="mt-6 flex justify-end gap-2">
            <Button variant="outline" onClick={handleDeleteCancel}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
