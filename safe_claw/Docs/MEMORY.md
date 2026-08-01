# SafeClaw Memory System

过程文档（计划 / 里程碑 / 验收 / 有头 E2E / 脚本）见：

**[docs/features/memory-system/](../../docs/features/memory-system/)**

## Storage

Memories live under the workspace (not the git repo):

```
~/Downloads/safe_claw_worksapce/workspace/memory/
  active/*.json
  dormant/*.json
  deep/*.json
  forgotten/*.json
  vectors.sqlite   # used when enable_vector_search=true
```

`WORKSPACE_DIR` is defined in `api/main.py` as  
`Path.home() / "Downloads" / "safe_claw_worksapce" / "workspace"`.

## Layers

| Layer | Role |
|-------|------|
| active | Hot set; overflow moves least-important → dormant |
| dormant | Cooler store; high-score search hits can wake → active |
| deep | Long-term archive (stale + low-importance dormant) |
| forgotten | Past retention window |

## Chat loop

1. `POST /chat/stream` searches the global `MemoryManager` with the latest user text.
2. Hits are injected as a `system` message (`format_memory_context`).
3. SSE memory step reports the **real** hit count (not a hardcoded 3).
4. After a successful reply, `maybe_store_conversation` writes the turn only if  
   `importance >= auto_write_min_importance` (default **0.6**).

## HTTP API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/memory?layer=active&limit=20` | List layer; invalid layer → **400** |
| GET | `/memory?search=…` | Hybrid search |
| POST | `/memory` | Explicit add (`/remember`) |
| POST | `/memory/cleanup` | Age → forgotten, dormant→deep, consolidate |

DTO fields: `id`, `content`, `layer`, `importance` (from `importance_score`),  
`created_at`, `access_count`, `tags` (from `keywords`).

## Slash commands

- `/remember <text>` — POST memory (importance 0.9) and open Memory panel
- `/memory [query]` — open Memory panel; optional search notice

## Config (`MemoryConfig`)

- `max_active_memories` (alias: `active_memory_max`)
- `auto_write_min_importance` (default 0.6)
- `dormant_wakeup_threshold`
- `dormant_to_deep_days`
- `enable_vector_search` — hashing bag-of-words + SQLite index (no Chroma)

## Fail Fast

Memory APIs do **not** swallow errors into empty lists. Missing manager → 503;  
invalid layer → 400; write/read failures surface with context.
