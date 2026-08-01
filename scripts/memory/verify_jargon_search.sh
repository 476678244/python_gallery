#!/usr/bin/env bash
# Verify jargon memory search queries. See docs/features/memory-system/scripts.md
set -euo pipefail

API="${API:-http://localhost:8000}"
export NO_PROXY="${NO_PROXY:-127.0.0.1,localhost}"
unset ALL_PROXY all_proxy HTTP_PROXY HTTPS_PROXY http_proxy https_proxy 2>/dev/null || true

fail=0

check_query() {
  local q="$1"
  local body total
  body=$(curl -sG "${API}/memory" --data-urlencode "search=${q}" --data-urlencode "limit=5")
  total=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("total", 0))' <<<"${body}")
  if [[ "${total}" -ge 1 ]]; then
    echo "PASS  search=$(printf %q "${q}")  total=${total}"
  else
    echo "FAIL  search=$(printf %q "${q}")  total=${total}"
    fail=1
  fi
}

echo "API=${API}"
check_query "101"
check_query "什么是101"
check_query "黑话"
check_query "你知道哪些黑话"
check_query "皮夹克"

if [[ "${fail}" -ne 0 ]]; then
  echo "verify_jargon_search: FAILED (expected until Phase A/B land for Chinese questions)"
  exit 1
fi
echo "verify_jargon_search: OK"
exit 0
