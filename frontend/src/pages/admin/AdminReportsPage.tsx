/*
Async report generation — kicks off a Celery-backed CSV export job and lists past reports
with a download link once completed.
*/

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { ReportExport } from "../../types";

export function AdminReportsPage() {
  const [reports, setReports] = useState<ReportExport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  async function loadReports() {
    setLoading(true);
    try {
      const response = await api.get("/api/v1/admin/reports");
      setReports(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    try {
      await api.post("/api/v1/admin/reports/payments-csv");
      await loadReports();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to start report generation");
    } finally {
      setGenerating(false);
    }
  }

  function downloadUrl(reportId: string) {
    return `${api.defaults.baseURL}/api/v1/admin/reports/${reportId}/download`;
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  return (
    <div className="max-w-3xl">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-wide text-secondary mb-2">Reports</p>
          <p className="text-secondary text-sm">Async CSV exports of platform payment data.</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-primary text-white px-4 py-2 text-sm font-medium disabled:opacity-50 shrink-0"
        >
          {generating ? "Starting…" : "Generate payments report"}
        </button>
      </div>

      {reports.length === 0 ? (
        <p className="text-secondary text-sm">No reports generated yet.</p>
      ) : (
        <div>
          {reports.map((report, index) => (
            <div key={report.id}>
              <div className="flex items-center justify-between py-3">
                <div>
                  <span className="font-mono text-sm">{report.report_type}</span>
                  <span
                    className="font-mono text-[11px] uppercase tracking-wider px-2 py-0.5 border ml-3"
                    style={{
                      color:
                        report.status === "completed" ? "#1E7A46" : report.status === "failed" ? "#FF5449" : "#919191",
                      borderColor:
                        report.status === "completed" ? "#1E7A46" : report.status === "failed" ? "#FF5449" : "#919191",
                    }}
                  >
                    {report.status}
                  </span>
                  {report.error_message && (
                    <span className="text-xs text-error ml-3">{report.error_message}</span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-secondary font-mono">{formatDate(report.created_at)}</span>
                  {report.status === "completed" && report.file_path && (
                    
                      <a href={downloadUrl(report.id)}
                      className="text-xs uppercase tracking-wide border border-primary px-2 py-1"
                    >
                      Download
                    </a>
                  )}
                </div>
              </div>
              {index < reports.length - 1 && <hr className="ledger-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}