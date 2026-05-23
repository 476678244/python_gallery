/**
 * System Panel - Feature Component
 *
 * Business: Monitor CPU, memory, disk, SafeClaw process
 * Responsibility: System resource display
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { Monitor, RefreshCw, Cpu, HardDrive, MemoryStick } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface SystemInfo {
  cpu: { percent: number; count: number; per_cpu: number[] };
  memory: { total: number; available: number; used: number; percent: number };
  disk: { total: number; used: number; free: number; percent: number };
  safe_claw_loaded: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function GaugeBar({ percent, color }: { percent: number; color: string }) {
  return (
    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
      <div
        className={cn("h-full rounded-full transition-all duration-500", color)}
        style={{ width: `${Math.min(100, percent)}%` }}
      />
    </div>
  );
}

export function SystemPanel() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/system");
      if (res.ok) setInfo(await res.json());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  const cpuColor = !info ? "bg-blue-400" : info.cpu.percent > 80 ? "bg-red-400" : info.cpu.percent > 50 ? "bg-amber-400" : "bg-green-400";
  const memColor = !info ? "bg-blue-400" : info.memory.percent > 80 ? "bg-red-400" : info.memory.percent > 60 ? "bg-amber-400" : "bg-blue-400";
  const diskColor = !info ? "bg-blue-400" : info.disk.percent > 90 ? "bg-red-400" : info.disk.percent > 70 ? "bg-amber-400" : "bg-slate-400";

  return (
    <div className="h-full flex flex-col gap-4 p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Monitor className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">System Resources</span>
        </div>
        <button
          onClick={load}
          className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          title="Refresh"
        >
          <RefreshCw className={cn("w-3.5 h-3.5 text-slate-400", isLoading && "animate-spin")} />
        </button>
      </div>

      {/* SafeClaw status */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200">
        <div className={cn("w-2 h-2 rounded-full", info?.safe_claw_loaded ? "bg-green-500" : "bg-amber-400")} />
        <span className="text-xs text-slate-600">
          SafeClaw Core: {info?.safe_claw_loaded ? "Loaded" : "Mock mode"}
        </span>
      </div>

      {/* CPU */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-medium text-slate-600">CPU</span>
          </div>
          <span className="text-xs text-slate-500">{info?.cpu.percent.toFixed(1) ?? "—"}% · {info?.cpu.count ?? "—"} cores</span>
        </div>
        <GaugeBar percent={info?.cpu.percent ?? 0} color={cpuColor} />
        {info && info.cpu.per_cpu.length > 0 && (
          <div className="grid grid-cols-4 gap-1 mt-1">
            {info.cpu.per_cpu.slice(0, 8).map((p, i) => (
              <div key={i} className="text-center">
                <div className="text-xs text-slate-400">C{i}</div>
                <div className="text-xs font-medium text-slate-600">{p.toFixed(0)}%</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Memory */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <MemoryStick className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-medium text-slate-600">Memory</span>
          </div>
          <span className="text-xs text-slate-500">
            {info ? `${formatBytes(info.memory.used)} / ${formatBytes(info.memory.total)}` : "—"}
          </span>
        </div>
        <GaugeBar percent={info?.memory.percent ?? 0} color={memColor} />
        <div className="flex justify-between text-xs text-slate-400">
          <span>Used: {info?.memory.percent.toFixed(1) ?? "—"}%</span>
          <span>Free: {info ? formatBytes(info.memory.available) : "—"}</span>
        </div>
      </div>

      {/* Disk */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <HardDrive className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-medium text-slate-600">Disk</span>
          </div>
          <span className="text-xs text-slate-500">
            {info ? `${formatBytes(info.disk.used)} / ${formatBytes(info.disk.total)}` : "—"}
          </span>
        </div>
        <GaugeBar percent={info?.disk.percent ?? 0} color={diskColor} />
        <div className="flex justify-between text-xs text-slate-400">
          <span>Used: {info?.disk.percent.toFixed(1) ?? "—"}%</span>
          <span>Free: {info ? formatBytes(info.disk.free) : "—"}</span>
        </div>
      </div>

      <p className="text-xs text-slate-400 text-center">Auto-refreshes every 5s</p>
    </div>
  );
}
