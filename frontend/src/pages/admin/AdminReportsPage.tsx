/*
Admin Reports page — Phase 3/4 rewrite. The old "Generate → wait → appears in list → Download"
flow is gone, since generate_payments_report() was confirmed to be synchronous already (the
Celery dispatch was dead code). Now: pick CSV or PDF, the file is generated and downloaded in
one click. Two charts, fed by the new GET /admin/reports/summary endpoint, sit above the
export history so the page is useful to look at even before anyone clicks download. The
history list itself stays — it's the audit trail (who exported what, when), which we decided
to keep even though exports are no longer async.
*/

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { ReportExport, ReportSummary } from "../../types";

const REPORT_STATUS_COLORS: Record<string, string> = {
  completed: "#1E7A46",
  pending: "#919191",
  failed: "#FF5449",
};

const PAYMENT_STATUS_COLORS: Record<string, string> = {
  succeeded: "#1E7A46",
  declined: "#FF5449",
  processing: "#919191",
  requires_payment_method: "#919191",
  requires_confirmation: "#919191",
  canceled: "#919191",
};

export function AdminReportsPage() {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [reports, setReports] = useState<ReportExport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingFormat, setDownloadingFormat] = useState<"csv" | "pdf" | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [redownloadingId, setRedownloadingId] = useState<string | null>(null);

  async function loadAll() {
    setLoading(true);
    try {
      const [summaryRes, reportsRes] = await Promise.all([
        api.get<ReportSummary>("/api/v1/admin/reports/summary"),
        api.get<ReportExport[]>("/api/v1/admin/reports"),
      ]);
      setSummary(summaryRes.data);
      setReports(reportsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to load reports data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  function saveBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  async function handleDownload(format: "csv" | "pdf") {
    setDownloadingFormat(format);
    setDownloadError(null);
    try {
      const generateRes = await api.post<ReportExport>("/api/v1/admin/reports/payments", { format });
      const report = generateRes.data;

      if (report.status !== "completed" || !report.file_path) {
        setDownloadError(report.error_message ?? "Report generation did not complete.");
        await loadAll();
        return;
      }

      const fileRes = await api.get(`/api/v1/admin/reports/${report.id}/download`, {
        responseType: "blob",
      });
      saveBlob(fileRes.data, `${report.report_type}_${report.id}.${format}`);
      await loadAll();
    } catch (err: any) {
      setDownloadError(err.response?.data?.detail ?? "Failed to generate report");
    } finally {
      setDownloadingFormat(null);
    }
  }

  async function handleRedownload(report: ReportExport) {
    setRedownloadingId(report.id);
    try {
      const fileRes = await api.get(`/api/v1/admin/reports/${report.id}/download`, {
        responseType: "blob",
      });
      saveBlob(fileRes.data, `${report.report_type}_${report.id}.${report.format}`);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Failed to download report");
    } finally {
      setRedownloadingId(null);
    }
  }

  if (loading) return <p className="text-secondary text-sm">Loading…</p>;
  if (error) return <p className="text-error text-sm">{error}</p>;

  const dailyRevenueChartData = (summary?.daily_revenue ?? []).map((point) => ({
    ...point,
    label: new Date(point.date).toLocaleDateString("en-KE", { month: "short", day: "numeric" }),
    amount: point.amount_minor / 100,
  }));

  const statusChartData = summary?.status_breakdown ?? [];

  return (
    <div className="max-w-3xl flex flex-col gap-6">
      <div>
        <p className="text-xs uppercase tracking-wide text-secondary mb-2">Reports</p>
        <p className="text-secondary text-sm">
          Platform-wide payment activity over the last 30 days, and exportable data.
        </p>
      </div>

      {/* Daily revenue */}
      <section className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
        <p className="text-xs uppercase tracking-wide text-secondary mb-4">
          Daily revenue (last 30 days)
        </p>
        {dailyRevenueChartData.length === 0 ? (
          <p className="text-secondary text-sm">No payment activity in this period.</p>
        ) : (
          <>
            <div style={{ width: "100%", height: 220 }}>
              <ResponsiveContainer>
                <LineChart data={dailyRevenueChartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.08)" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 11, fill: "#919191", fontFamily: "IBM Plex Mono, monospace" }}
                    axisLine={{ stroke: "rgba(0,0,0,0.08)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#919191", fontFamily: "IBM Plex Mono, monospace" }}
                    axisLine={false}
                    tickLine={false}
                    width={40}
                  />
                  <Tooltip
                    formatter={(value) =>
                      typeof value === "number" ? value.toLocaleString() : String(value ?? "")
                    }
                    contentStyle={{
                      fontSize: 12,
                      fontFamily: "IBM Plex Mono, monospace",
                      border: "none",
                      borderRadius: 14,
                      boxShadow: "8px 8px 20px rgba(0,0,0,0.12), -8px -8px 20px rgba(255,255,255,0.9)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="amount"
                    stroke="#000000"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#000000" }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-secondary mt-3">
              Amounts are summed across every currency with no FX conversion — treat this as an
              approximate activity trend, not a real revenue total.
            </p>
          </>
        )}
      </section>

      {/* Status breakdown */}
      <section className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
        <p className="text-xs uppercase tracking-wide text-secondary mb-4">
          Payments by status (last 30 days)
        </p>
        {statusChartData.length === 0 ? (
          <p className="text-secondary text-sm">No payment activity in this period.</p>
        ) : (
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <BarChart data={statusChartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.08)" vertical={false} />
                <XAxis
                  dataKey="status"
                  tick={{ fontSize: 10, fill: "#919191", fontFamily: "IBM Plex Mono, monospace" }}
                  axisLine={{ stroke: "rgba(0,0,0,0.08)" }}
                  tickLine={false}
                  tickFormatter={(value: string) => value.replace(/_/g, " ")}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#919191", fontFamily: "IBM Plex Mono, monospace" }}
                  axisLine={false}
                  tickLine={false}
                  width={30}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    fontFamily: "IBM Plex Mono, monospace",
                    border: "none",
                    borderRadius: 14,
                    boxShadow: "8px 8px 20px rgba(0,0,0,0.12), -8px -8px 20px rgba(255,255,255,0.9)",
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {statusChartData.map((entry) => (
                    <Cell key={entry.status} fill={PAYMENT_STATUS_COLORS[entry.status] ?? "#919191"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      {/* Download */}
      <section className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
        <p className="text-xs uppercase tracking-wide text-secondary mb-2">Download payments export</p>
        <p className="text-secondary text-sm mb-4">
          Generates and downloads immediately — every payment intent on the platform, all time.
        </p>
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleDownload("csv")}
            disabled={downloadingFormat !== null}
            className="bg-primary text-white px-4 py-2 text-sm font-medium rounded-neu-md shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm disabled:opacity-50 transition-shadow"
          >
            {downloadingFormat === "csv" ? "Preparing…" : "Download CSV"}
          </button>
          <button
            onClick={() => handleDownload("pdf")}
            disabled={downloadingFormat !== null}
            className="px-4 py-2 text-sm font-medium rounded-neu-md shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm disabled:opacity-50 transition-shadow"
          >
            {downloadingFormat === "pdf" ? "Preparing…" : "Download PDF"}
          </button>
        </div>
        {downloadError && <p className="text-error text-sm mt-3">{downloadError}</p>}
      </section>

      {/* Export history */}
      <section className="rounded-neu-lg shadow-neu-raised-sm bg-surface p-6">
        <p className="text-xs uppercase tracking-wide text-secondary mb-4">Export history</p>
        {reports.length === 0 ? (
          <p className="text-secondary text-sm">No reports generated yet.</p>
        ) : (
          <div>
            {reports.map((report, index) => (
              <div key={report.id}>
                <div className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm">{report.report_type}</span>
                    <span className="font-mono text-[11px] uppercase tracking-wider px-3 py-1 rounded-neu-full shadow-neu-raised-sm text-secondary">
                      {report.format}
                    </span>
                    <span
                      className="font-mono text-[11px] uppercase tracking-wider px-3 py-1 rounded-neu-full shadow-neu-raised-sm"
                      style={{
                        color: REPORT_STATUS_COLORS[report.status] ?? "#919191",
                        backgroundColor: `${REPORT_STATUS_COLORS[report.status] ?? "#919191"}14`,
                      }}
                    >
                      {report.status}
                    </span>
                    {report.error_message && (
                      <span className="text-xs text-error">{report.error_message}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-secondary font-mono">{formatDate(report.created_at)}</span>
                    {report.status === "completed" && report.file_path && (
                      <button
                        onClick={() => handleRedownload(report)}
                        disabled={redownloadingId === report.id}
                        className="text-xs uppercase tracking-wide px-2 py-1 rounded-neu-sm shadow-neu-raised-sm hover:shadow-neu-hover active:shadow-neu-inset-sm disabled:opacity-50 transition-shadow"
                      >
                        {redownloadingId === report.id ? "…" : "Download"}
                      </button>
                    )}
                  </div>
                </div>
                {index < reports.length - 1 && <hr className="ledger-divider" />}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}