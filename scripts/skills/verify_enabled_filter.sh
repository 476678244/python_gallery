#!/usr/bin/env bash
# Toggle Ljg off → assert filtered paths / discovery have no ljg-*
set -euo pipefail
API="${SAFECLAW_API_URL:-http://127.0.0.1:8000}"

curl -sf "$API/skills" >/dev/null
curl -sf -X POST "$API/skills" -H 'Content-Type: application/json' \
  -d '{"folder_id":"linked/ljg-skills","enabled":false}' >/dev/null

python3 - <<'PY'
import json, urllib.request
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# Prefer live API tree for enabled flags
api = __import__("os").environ.get("SAFECLAW_API_URL", "http://127.0.0.1:8000")
with urllib.request.urlopen(api + "/skills") as r:
    tree = json.load(r)["tree"]
ljg = next(n for n in tree if n["id"] == "linked/ljg-skills")
assert ljg["enabled"] is False, ljg
assert all(not c.get("enabled") for c in ljg["children"]), "ljg children still enabled"
priv = next(n for n in tree if n["id"] == "private")
assert any(c.get("enabled") for c in priv["children"]), "private collateral-disabled"
print("OK: folder toggle strict; ljg off, private still has enabled skills")
PY

# restore
curl -sf -X POST "$API/skills" -H 'Content-Type: application/json' \
  -d '{"folder_id":"linked/ljg-skills","enabled":true}' >/dev/null
echo "restored linked/ljg-skills"
