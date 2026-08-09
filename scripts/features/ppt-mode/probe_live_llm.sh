#!/usr/bin/env bash
# Live LLM probe wrapper — docs/features/ppt-mode
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
EVIDENCE="${HOME}/Downloads/safe_claw_worksapce/workspace/ppt/_evidence_2026-08-05"
mkdir -p "$EVIDENCE"
# Prefer committed copy if present; else evidence workspace copy
SCRIPT="$ROOT/scripts/features/ppt-mode/probe_live_llm.py"
if [[ ! -f "$SCRIPT" ]]; then
  SCRIPT="$EVIDENCE/probe_live_llm.py"
fi
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate safe_claw
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy || true
exec python "$SCRIPT"
