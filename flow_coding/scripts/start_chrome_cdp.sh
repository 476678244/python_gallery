#!/usr/bin/env bash
# Delegate to canonical skill script.
exec "$(cd "$(dirname "$0")/../.." && pwd)/skills/private_skills/flow_coding_chrome_cdp/scripts/start_chrome_cdp.sh" "$@"
