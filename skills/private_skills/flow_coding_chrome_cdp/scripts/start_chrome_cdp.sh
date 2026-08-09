#!/usr/bin/env bash
# Start Google Chrome with CDP (Chrome DevTools Protocol) enabled.
# Playwright: chromium.connectOverCDP('http://127.0.0.1:9222')
#
# Default: syncs your existing Chrome profile, then launches from a sibling
# user-data-dir (Chrome 136+ blocks CDP on the literal default profile path).
#
# Usage:
#   ./start_chrome_cdp.sh --restart
#   ./start_chrome_cdp.sh --restart --url http://localhost:3000
#   ./start_chrome_cdp.sh --isolated-profile

set -euo pipefail

PORT="${CDP_PORT:-9222}"
URL="${CDP_URL:-}"
WINDOW_SIZE="${CDP_WINDOW_SIZE:-1920,1080}"
CHROME_BIN="${CHROME_BIN:-}"
PROFILE_MODE="${CDP_PROFILE_MODE:-existing}"   # existing | isolated
RESTART=false
USER_DATA_DIR="${CDP_USER_DATA_DIR:-}"
SYNC_PROFILE=true

usage() {
  cat <<'EOF'
Start Chrome with remote debugging (CDP mode).

Options:
  --port PORT             Remote debugging port (default: 9222)
  --url URL               Open this URL on startup
  --restart               Quit Chrome, sync daily profile → Chrome-CDP, relaunch with CDP
  --no-sync               Advanced: skip profile sync (reuse last Chrome-CDP; no new logins)
  --isolated-profile      Use a blank automation profile (no bookmarks/logins)
  --user-data-dir DIR     Override profile directory explicitly
  --window-size WxH       Window size (default: 1920,1080)
  --chrome-bin PATH       Chrome executable (auto-detected if omitted)
  -h, --help              Show this help

Environment:
  CDP_PORT, CDP_URL, CDP_USER_DATA_DIR, CDP_WINDOW_SIZE, CHROME_BIN, CDP_PROFILE_MODE

Profile layout (existing mode):
  Source (your daily Chrome):  ~/Library/Application Support/Google/Chrome
  CDP launch dir (synced):     ~/Library/Application Support/Google/Chrome-CDP

Playwright connect:
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');

Note:
  Chrome 136+ requires a non-default user-data-dir for remote debugging.
  --restart quits Chrome, rsyncs your profile into Chrome-CDP, then launches.
EOF
}

real_user_data_dir() {
  case "$(uname -s)" in
    Darwin)
      echo "$HOME/Library/Application Support/Google/Chrome"
      ;;
    Linux)
      echo "$HOME/.config/google-chrome"
      ;;
    *)
      echo "[start_chrome_cdp] Unsupported OS for default profile: $(uname -s)" >&2
      return 1
      ;;
  esac
}

cdp_user_data_dir() {
  case "$(uname -s)" in
    Darwin)
      echo "$HOME/Library/Application Support/Google/Chrome-CDP"
      ;;
    Linux)
      echo "$HOME/.config/google-chrome-cdp"
      ;;
    *)
      return 1
      ;;
  esac
}

isolated_user_data_dir() {
  echo "$HOME/Downloads/safe_claw_worksapce/workspace/flow_coding_chrome_cdp"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift 2
      ;;
    --url)
      URL="$2"
      shift 2
      ;;
    --user-data-dir)
      USER_DATA_DIR="$2"
      shift 2
      ;;
    --window-size)
      WINDOW_SIZE="$2"
      shift 2
      ;;
    --chrome-bin)
      CHROME_BIN="$2"
      shift 2
      ;;
    --restart)
      RESTART=true
      shift
      ;;
    --no-sync)
      SYNC_PROFILE=false
      shift
      ;;
    --isolated-profile)
      PROFILE_MODE="isolated"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[start_chrome_cdp] Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "[start_chrome_cdp] Invalid port: $PORT (expected 1024-65535)" >&2
  exit 1
fi

REAL_PROFILE_DIR="$(real_user_data_dir)"

if [[ -z "$USER_DATA_DIR" ]]; then
  if [[ "$PROFILE_MODE" == "isolated" ]]; then
    USER_DATA_DIR="$(isolated_user_data_dir)"
  else
    USER_DATA_DIR="$(cdp_user_data_dir)"
  fi
fi

find_chrome() {
  if [[ -n "$CHROME_BIN" ]]; then
    if [[ -x "$CHROME_BIN" ]]; then
      echo "$CHROME_BIN"
      return 0
    fi
    echo "[start_chrome_cdp] CHROME_BIN is not executable: $CHROME_BIN" >&2
    return 1
  fi

  local candidates=()
  case "$(uname -s)" in
    Darwin)
      candidates=(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        "/Applications/Chromium.app/Contents/MacOS/Chromium"
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
      )
      ;;
    Linux)
      candidates=(
        google-chrome
        google-chrome-stable
        chromium
        chromium-browser
      )
      ;;
    *)
      echo "[start_chrome_cdp] Unsupported OS: $(uname -s)" >&2
      return 1
      ;;
  esac

  local candidate resolved
  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
    resolved="$(command -v "$candidate" 2>/dev/null || true)"
    if [[ -n "$resolved" && -x "$resolved" ]]; then
      echo "$resolved"
      return 0
    fi
  done

  echo "[start_chrome_cdp] Chrome not found. Install Google Chrome or set CHROME_BIN." >&2
  return 1
}

port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1
    return $?
  fi
  return 1
}

cdp_ready() {
  curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1
}

chrome_pids() {
  pgrep -f "Google Chrome" 2>/dev/null || true
}

quit_chrome() {
  echo "[start_chrome_cdp] Quitting Chrome..."
  case "$(uname -s)" in
    Darwin)
      osascript -e 'tell application "Google Chrome" to quit' >/dev/null 2>&1 || true
      ;;
    Linux)
      pkill -f "chrome" >/dev/null 2>&1 || true
      ;;
  esac

  local waited=0
  while (( waited < 20 )); do
    if [[ -z "$(chrome_pids)" ]]; then
      sleep 1
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done

  echo "[start_chrome_cdp] Force stopping remaining Chrome processes..." >&2
  pkill -f "Google Chrome" 2>/dev/null || true
  sleep 2
}

sync_existing_profile() {
  local src="$REAL_PROFILE_DIR"
  local dest="$USER_DATA_DIR"

  if [[ ! -d "$src" ]]; then
    echo "[start_chrome_cdp] Source profile not found: $src" >&2
    exit 1
  fi

  echo "[start_chrome_cdp] Syncing profile:"
  echo "[start_chrome_cdp]   from: $src"
  echo "[start_chrome_cdp]   to:   $dest"

  mkdir -p "$dest"
  rsync -a \
    --exclude 'SingletonLock' \
    --exclude 'SingletonSocket' \
    --exclude 'SingletonCookie' \
    --exclude 'RunningChromeVersion' \
    --exclude '*/Cache/*' \
    --exclude '*/Code Cache/*' \
    --exclude '*/GPUCache/*' \
    --exclude '*/Service Worker/CacheStorage/*' \
    "$src/" "$dest/"
}

CHROME_BIN="$(find_chrome)"

if port_in_use && cdp_ready; then
  if [[ "$RESTART" == true ]]; then
    echo "[start_chrome_cdp] CDP active on port $PORT — --restart: relaunching with current flags..."
    quit_chrome
  else
    running_dir="$(pgrep -fl "Google Chrome" | grep -o '\--user-data-dir=[^ ]*' | head -1 | cut -d= -f2- || true)"
    echo "[start_chrome_cdp] CDP already active on port $PORT"
    echo "[start_chrome_cdp] CDP URL: http://127.0.0.1:$PORT"
    if [[ -n "$running_dir" ]]; then
      echo "[start_chrome_cdp] Profile:  $running_dir"
    fi
    exit 0
  fi
fi

if port_in_use; then
  echo "[start_chrome_cdp] Port $PORT in use by non-CDP process. Use --port <other>." >&2
  exit 1
fi

if [[ -n "$(chrome_pids)" ]]; then
  if [[ "$RESTART" == true ]]; then
    quit_chrome
  else
    echo "[start_chrome_cdp] Chrome is already running." >&2
    echo "[start_chrome_cdp] Re-run with --restart to quit, sync your profile, and launch with CDP." >&2
    exit 1
  fi
fi

if [[ "$PROFILE_MODE" == "existing" && "$SYNC_PROFILE" == true ]]; then
  sync_existing_profile
elif [[ "$PROFILE_MODE" == "isolated" ]]; then
  mkdir -p "$USER_DATA_DIR"
fi

ARGS=(
  "--remote-debugging-port=$PORT"
  "--remote-allow-origins=*"
  "--user-data-dir=$USER_DATA_DIR"
  "--window-size=$WINDOW_SIZE"
)

if [[ "$PROFILE_MODE" == "isolated" ]]; then
  ARGS+=(
    "--no-first-run"
    "--no-default-browser-check"
    "--disable-background-networking"
    "--disable-sync"
  )
fi

if [[ -n "$URL" ]]; then
  ARGS+=("$URL")
fi

echo "[start_chrome_cdp] Chrome:      $CHROME_BIN"
echo "[start_chrome_cdp] Profile:     $PROFILE_MODE"
echo "[start_chrome_cdp] Launch dir:  $USER_DATA_DIR"
if [[ "$PROFILE_MODE" == "existing" ]]; then
  echo "[start_chrome_cdp] Synced from: $REAL_PROFILE_DIR"
fi
echo "[start_chrome_cdp] CDP port:    $PORT"
echo "[start_chrome_cdp] Window:      $WINDOW_SIZE"
echo "[start_chrome_cdp] CDP URL:     http://127.0.0.1:$PORT"
echo "[start_chrome_cdp] Playwright:  chromium.connectOverCDP('http://127.0.0.1:$PORT')"
echo "[start_chrome_cdp] Starting..."

exec "$CHROME_BIN" "${ARGS[@]}"
