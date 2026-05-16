/**
 * Safety Panel - Feature Component
 *
 * Business: Safety checks, block rates, audit log
 * Responsibility: Safety monitoring display
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { Shield, RefreshCw, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface SafetyStats {
  total_checks: number;
  blocked_requests: number;
  confirmation_required: number;
  block_rate: number;
  risk_distribution: Record<string, number>;
}

interface SafetyData {
  safety_stats: SafetyStats;
  audit_stats: { total_events: number; by_level: Record<string, number> };
}

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-400",
  medium: "bg-yellow-400",
  high: "bg-orange-400",
  critical: "bg-red-500",
};

export function SafetyPanel() {
  const [data, setData] = useState<SafetyData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/safety");
      if (res.ok) setData(await res.json());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const stats = data?.safety_stats;

  return (
    <div className="h-full flex flex-col gap-4 p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-medium text-slate-700">Safety Dashboard</span>
        </div>
        <button
          onClick={load}
          className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
        >
          <RefreshCw className={cn("w-3.5 h-3.5 text-slate-400", isLoading && "animate-spin")} />
        </button>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-1.5 mb-1">
            <CheckCircle className="w-3.5 h-3.5 text-green-500" />
            <span className="text-xs text-slate-500">Total Checks</span>
          </div>
          <p className="text-xl font-bold text-slate-700">{stats?.total_checks ?? 0}</p>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-1.5 mb-1">
            <XCircle className="w-3.5 h-3.5 text-red-500" />
            <span className="text-xs text-slate-500">Blocked</span>
          </div>
          <p className="text-xl font-bold text-slate-700">{stats?.blocked_requests ?? 0}</p>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-xs text-slate-500">Needs Confirm</span>
          </div>
          <p className="text-xl font-bold text-slate-700">{stats?.confirmation_required ?? 0}</p>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-1.5 mb-1">
            <Shield className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs text-slate-500">Block Rate</span>
          </div>
          <p className="text-xl font-bold text-slate-700">
            {((stats?.block_rate ?? 0) * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Risk distribution */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-slate-600">Risk Distribution</p>
        {Object.entries(stats?.risk_distribution ?? { low: 0, medium: 0, high: 0, critical: 0 }).map(([level, count]) => {
          const total = Object.values(stats?.risk_distribution ?? {}).reduce((a, b) => a + b, 0);
          const pct = total > 0 ? (count / total) * 100 : 0;
          return (
            <div key={level} className="space-y-1">
              <div className="flex justify-between text-xs text-slate-500">
                <span className="capitalize">{level}</span>
                <span>{count} ({pct.toFixed(0)}%)</span>
              </div>
              <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-500", RISK_COLORS[level] ?? "bg-slate-400")}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Audit stats */}
      {data?.audit_stats && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-600">Audit Log</p>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex justify-between text-xs text-slate-500">
              <span>Total Events</span>
              <span className="font-medium text-slate-700">{data.audit_stats.total_events}</span>
            </div>
            {Object.entries(data.audit_stats.by_level).map(([level, count]) => (
              <div key={level} className="flex justify-between text-xs text-slate-500">
                <span className="capitalize">{level}</span>
                <span>{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats?.total_checks === 0 && (
        <div className="text-center py-4 text-xs text-slate-400">
          <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p>No safety events recorded yet</p>
        </div>
      )}
    </div>
  );
}
