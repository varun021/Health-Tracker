"use client";
import React, { useEffect, useState, useMemo } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Database,
  Brain,
  Activity,
  ClipboardList,
  Download,
  RefreshCcw,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { userApi } from "@/lib/api-services";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export default function ModelReportPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ diseases: 0, symptoms: 0, samples: 0 });
  const [diseases, setDiseases] = useState([]);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  // Fetch model summary + diseases
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const meta = await userApi.getModelSummary();
      const diseaseList = await userApi.getDiseases();

      setStats({
        diseases: meta.diseases,
        symptoms: meta.symptoms,
        samples: meta.samples_trained,
      });
      setDiseases(diseaseList);
    } catch (err) {
      console.error(err);
      setError("Failed to load model report. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter diseases by search term
  const filteredDiseases = useMemo(() => {
    if (!searchTerm) return diseases;
    return diseases.filter((d) =>
      d.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm, diseases]);

  // Pagination logic
  const totalPages = Math.ceil(filteredDiseases.length / PAGE_SIZE);
  const paginatedDiseases = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredDiseases.slice(start, start + PAGE_SIZE);
  }, [filteredDiseases, page]);

  // Handle report download
  const handleDownload = async (format = "pdf") => {
    try {
      setDownloading(true);
      const options = {
        format,
        include_personal_info: false,
        include_recommendations: false,
      };
      const response = await userApi.generateReport(options);

      const blob = new Blob([response], {
        type: format === "pdf" ? "application/pdf" : "text/csv",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `model_report_${new Date()
        .toISOString()
        .slice(0, 10)}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success(`Report downloaded as ${format.toUpperCase()}`);
    } catch (err) {
      console.error("Report download failed:", err);
      toast.error("Failed to download report");
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading model report...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto mt-20">
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <div className="flex justify-center mt-4">
          <Button onClick={fetchData} variant="default">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-3">
        <h1 className="text-3xl font-bold text-gray-900">
          Model Overview Report
        </h1>
        <div className="flex gap-3 flex-wrap">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
          </Button>
          <Button onClick={() => handleDownload("pdf")} disabled={downloading}>
            {downloading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" /> Download PDF
              </>
            )}
          </Button>
          <Button
            variant="secondary"
            onClick={() => handleDownload("csv")}
            disabled={downloading}
          >
            <Download className="w-4 h-4 mr-2" /> Download CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <Card className="border-2 shadow-sm">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-600" />
            Model Training Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-6 text-center">
          <SummaryCard
            icon={<Database className="w-6 h-6 text-blue-600" />}
            value={stats.diseases}
            label="Total Diseases"
            bg="bg-blue-50"
          />
          <SummaryCard
            icon={<Activity className="w-6 h-6 text-green-600" />}
            value={stats.symptoms}
            label="Total Symptoms"
            bg="bg-green-50"
          />
          <SummaryCard
            icon={<ClipboardList className="w-6 h-6 text-purple-600" />}
            value={stats.samples}
            label="Training Samples"
            bg="bg-purple-50"
          />
        </CardContent>
      </Card>

      {/* Search bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-gray-800">
          Disease & Symptom Report
        </h2>
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-gray-500" />
          <Input
            placeholder="Search diseases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
          />
        </div>
      </div>

      {/* Table */}
      <Card className="border-2 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader className="bg-gray-50">
                <TableRow>
                  <TableHead className="w-1/4 font-semibold">Disease</TableHead>
                  <TableHead className="font-semibold">Description</TableHead>
                  <TableHead className="font-semibold">
                    Symptoms (with Weight)
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedDiseases.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={3}
                      className="text-center py-6 text-gray-500"
                    >
                      No diseases found.
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedDiseases.map((disease) => (
                    <TableRow key={disease.id}>
                      <TableCell className="font-medium text-blue-700">
                        {disease.name}
                      </TableCell>

                      {/* Truncated Description with Tooltip */}
                      <TableCell className="text-sm text-gray-600 max-w-xs truncate">
                        {disease.description ? (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span
                                  title={disease.description}
                                  className="cursor-pointer block truncate"
                                >
                                  {disease.description.length > 80
                                    ? `${disease.description.slice(0, 80)}...`
                                    : disease.description}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent className="max-w-sm p-2 bg-gray-900 text-white text-xs rounded-lg shadow-md">
                                {disease.description}
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        ) : (
                          "—"
                        )}
                      </TableCell>

                      {/* Symptoms */}
                      <TableCell>
                        {disease.symptoms?.length > 0 ? (
                          <ul className="space-y-1">
                            {disease.symptoms.map((s, index) => (
                              <li
                                key={index}
                                className="text-sm text-gray-700 flex items-center gap-1"
                              >
                                •{" "}
                                <span className="font-medium">
                                  {s.symptom.name}
                                </span>
                                <span className="text-xs text-gray-500">
                                  (Weight: {s.weight})
                                </span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-gray-400 text-sm">
                            No symptoms listed
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-3 mt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="w-4 h-4 mr-1" /> Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}

/* ✅ Small Reusable Card for Summary Stats */
function SummaryCard({ icon, value, label, bg }) {
  return (
    <div
      className={`p-4 border rounded-lg ${bg} hover:shadow-md transition-all duration-200`}
    >
      <div className="flex flex-col items-center">
        {icon}
        <h4 className="text-lg font-semibold mt-2">{value}</h4>
        <p className="text-sm text-gray-600">{label}</p>
      </div>
    </div>
  );
}
