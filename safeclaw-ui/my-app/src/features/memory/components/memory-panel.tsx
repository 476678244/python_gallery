/**
 * Memory Panel - Feature Component
 *
 * Business: Browse, search, manage AI memory layers
 * Responsibility: Memory browser UI
 */

"use client";

import { useEffect, useState } from "react";
import { Brain, Search, Trash2, RefreshCw, Loader2 } from "lucide-react";
import { cn } from "@/shared/utils/cn";

type MemoryLayer = "active" | "dormant" | "deep" | "forgotten";

interface MemoryItem {
  id: string;
  content: string;
  layer: MemoryLayer;
  importance: number;
  created_at: string;
  access_count: number;
  tags: string[];
}

interface MemoryStats {
  active_count: number;
  dormant_count: number;
  deep_count: number;
  forgotten_count: number;
}

const LAYERS: { id: MemoryLayer; label: string; color: string }[] = [
  { id: "active", label: "Active", color: "bg-green-100 text-green-700" },
  { id: "dormant", label: "Dormant", color: "bg-yellow-100 text-yellow-700" },
  { id: "deep", label: "Deep", color: "bg-blue-100 text-blue-700" },
  { id: "forgotten", label: "Forgotten", color: "bg-slate-100 text-slate-500" },
];

async function fetchMemories(layer: MemoryLayer, search?: string): Promise<{ memories: MemoryItem[]; stats: MemoryStats; total: number }> {
  const params = new URLSearchParams({ layer, limit: "20" });
  if (search) params.set("search", search);
  const res = await fetch(`/api/memory?${params}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch memories (${res.status})`);
  }
  return res.json();
}

async function runCleanup(): Promise<void> {
  await fetch("/api/memory/cleanup", { method: "POST" });
}

export function MemoryPanel() {
  const [layer, setLayer] = useState<MemoryLayer>("active");
  const [search, setSearch] = useState("");
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [stats, setStats] = useState<MemoryStats>({ active_count: 0, dormant_count: 0, deep_count: 0, forgotten_count: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchMemories(layer, search || undefined);
      setMemories(data.memories ?? []);
      if (data.stats) setStats(data.stats as MemoryStats);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to load memories";
      setError(message);
      // Fail Fast: keep previous memories; do not pretend the layer is empty
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, [layer]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load();
  };

  const handleCleanup = async () => {
    setIsCleaning(true);
    try {
      await runCleanup();
      await load();
    } finally {
      setIsCleaning(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-y-auto" data-testid="memory-panel">
      {error && (
        <div
          data-testid="memory-panel-error"
          className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2"
        >
          {error}
        </div>
      )}
      {/* Stats */}
      <div className="grid grid-cols-2 gap-2">
        {LAYERS.map((l) => (
          <button
            key={l.id}
            onClick={() => setLayer(l.id)}
            className={cn(
              "flex flex-col items-center p-2 rounded-lg border-2 transition-colors text-xs font-medium",
              layer === l.id ? "border-blue-500 bg-blue-50" : "border-transparent bg-slate-50 hover:bg-slate-100"
            )}
          >
            <span className={cn("px-2 py-0.5 rounded-full text-xs mb-1", l.color)}>
              {l.label}
            </span>
            <span className="text-lg font-bold text-slate-700">
              {stats[`${l.id}_count` as keyof MemoryStats] ?? 0}
            </span>
          </button>
        ))}
      </div>

      {/* Controls */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memories..."
            className="w-full pl-7 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-blue-400"
          />
        </div>
        <button
          type="submit"
          className="px-3 py-1.5 text-xs bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Search
        </button>
      </form>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={load}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors text-slate-600"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", isLoading && "animate-spin")} />
          Refresh
        </button>
        <button
          onClick={handleCleanup}
          disabled={isCleaning}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors text-slate-600"
        >
          {isCleaning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
          Cleanup
        </button>
      </div>

      {/* Memory list */}
      <div className="flex-1 space-y-2">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-400">
            <Brain className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p>No memories in {layer} layer</p>
          </div>
        ) : (
          memories.map((mem) => (
            <div key={mem.id} className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
              <p className="text-xs text-slate-700 line-clamp-3">{mem.content}</p>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={cn("px-1.5 py-0.5 rounded text-xs", LAYERS.find(l => l.id === mem.layer)?.color ?? "bg-slate-100")}>
                  {mem.layer}
                </span>
                <span className="text-xs text-slate-400">
                  importance: {(mem.importance * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-slate-400">
                  accessed: {mem.access_count}×
                </span>
              </div>
              {mem.tags.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {mem.tags.map((tag) => (
                    <span key={tag} className="px-1.5 py-0.5 bg-blue-50 text-blue-600 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-xs text-slate-400">{new Date(mem.created_at).toLocaleString()}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
