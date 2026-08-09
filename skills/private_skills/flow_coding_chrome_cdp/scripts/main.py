"""
Flow Coding Chrome CDP Skill - Main Implementation

启动真实 Chrome（含现有 profile 同步）并暴露 CDP 端点，供 Playwright connectOverCDP 附着。
"""
from __future__ import annotations

import json
import platform
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


SKILL_DEFINITION = {
    "name": "flow_coding_chrome_cdp",
    "description": (
        "启动 Google Chrome CDP 模式：同步现有 profile 到 Chrome-CDP 目录并开启 "
        "remote debugging，供 Playwright connectOverCDP 附着。适用于 Flow Coding "
        "验证端需要真实浏览器会话（书签、扩展、登录态）的场景。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_guide",
                    "get_profile_paths",
                    "get_playwright_snippet",
                    "check_status",
                    "start_chrome",
                ],
                "description": "执行的操作类型",
            },
            "port": {
                "type": "integer",
                "description": "CDP 端口，默认 9222",
                "default": 9222,
            },
            "url": {
                "type": "string",
                "description": "启动 Chrome 后打开的 URL",
            },
            "restart": {
                "type": "boolean",
                "description": "退出 Chrome、同步 profile 后以 CDP 重启",
                "default": False,
            },
            "sync_profile": {
                "type": "boolean",
                "description": "existing 模式下是否 rsync 源 profile（默认 true）",
                "default": True,
            },
            "isolated_profile": {
                "type": "boolean",
                "description": "使用空白 automation profile，不同步现有 profile",
                "default": False,
            },
            "background": {
                "type": "boolean",
                "description": "后台启动 Chrome（start_chrome 默认 true）",
                "default": True,
            },
        },
        "required": ["action"],
    },
}

_SCRIPT_PATH = Path(__file__).resolve().parent / "start_chrome_cdp.sh"
_DEFAULT_PORT = 9222


def _script_path() -> Path:
    if not _SCRIPT_PATH.is_file():
        raise FileNotFoundError(
            f"[flow_coding_chrome_cdp] start_chrome_cdp.sh not found\n"
            f"  Expected: {_SCRIPT_PATH}"
        )
    return _SCRIPT_PATH


def _profile_paths() -> Dict[str, str]:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return {
            "source_profile": str(home / "Library/Application Support/Google/Chrome"),
            "cdp_profile": str(home / "Library/Application Support/Google/Chrome-CDP"),
            "isolated_profile": str(
                home / "Downloads/safe_claw_worksapce/workspace/flow_coding_chrome_cdp"
            ),
        }
    if system == "Linux":
        return {
            "source_profile": str(home / ".config/google-chrome"),
            "cdp_profile": str(home / ".config/google-chrome-cdp"),
            "isolated_profile": str(
                home / "Downloads/safe_claw_worksapce/workspace/flow_coding_chrome_cdp"
            ),
        }
    raise ValueError(
        f"[flow_coding_chrome_cdp] Unsupported platform for profile paths\n"
        f"  Platform: {system}\n"
        f"  Expected: Darwin or Linux"
    )


def _cdp_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def _fetch_cdp_version(port: int) -> Optional[Dict[str, Any]]:
    url = f"{_cdp_url(port)}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def _get_guide() -> Dict[str, Any]:
    paths = _profile_paths()
    return {
        "success": True,
        "skill_name": "flow_coding_chrome_cdp",
        "concept": "真实 Chrome + CDP = Playwright connectOverCDP 附着已有浏览器会话",
        "chrome_136_constraint": (
            "Chrome 136+ 禁止在默认 profile 路径上开启 remote debugging。"
            "因此 existing 模式会 rsync 源 profile 到 Chrome-CDP 兄弟目录再启动。"
        ),
        "profile_layout": {
            "source": paths["source_profile"],
            "cdp_launch": paths["cdp_profile"],
            "isolated": paths["isolated_profile"],
        },
        "workflow": [
            "1. check_status — 确认 CDP 是否已在监听",
            "2. start_chrome(restart=true) — 退出 Chrome → 同步 profile → CDP 启动",
            "3. Playwright connectOverCDP('http://127.0.0.1:9222')",
        ],
        "cautions": [
            "CDP 会话改动写入 Chrome-CDP，不会自动回写日常 Chrome",
            "Chrome 已在运行且未开 CDP 时，必须 restart=true",
            "日常浏览请正常打开 Chrome，勿与 CDP 实例同时占用同一 profile",
        ],
        "script_path": str(_script_path()),
    }


def _get_profile_paths() -> Dict[str, Any]:
    paths = _profile_paths()
    exists = {k: Path(v).exists() for k, v in paths.items()}
    return {"success": True, "paths": paths, "exists": exists}


def _get_playwright_snippet(port: int = _DEFAULT_PORT) -> Dict[str, Any]:
    endpoint = _cdp_url(port)
    snippet = f"""import {{ chromium }} from '@playwright/test';

const browser = await chromium.connectOverCDP('{endpoint}');
const context = browser.contexts()[0] ?? await browser.newContext();
const page = context.pages()[0] ?? await context.newPage();
// ... run assertions / screenshots
"""
    return {
        "success": True,
        "cdp_url": endpoint,
        "playwright_snippet": snippet,
    }


def _check_status(port: int = _DEFAULT_PORT) -> Dict[str, Any]:
    version = _fetch_cdp_version(port)
    ready = version is not None
    result: Dict[str, Any] = {
        "success": True,
        "port": port,
        "cdp_url": _cdp_url(port),
        "ready": ready,
    }
    if ready:
        result["browser"] = version.get("Browser")
        result["webSocketDebuggerUrl"] = version.get("webSocketDebuggerUrl")
        result["message"] = "CDP is active; safe to connectOverCDP"
    else:
        result["message"] = (
            "CDP not ready. Run start_chrome with restart=true to sync profile and launch."
        )
    return result


def _build_start_args(
    port: int,
    url: Optional[str],
    restart: bool,
    sync_profile: bool,
    isolated_profile: bool,
) -> List[str]:
    args = [str(_script_path()), f"--port={port}"]
    if restart:
        args.append("--restart")
    if not sync_profile:
        args.append("--no-sync")
    if isolated_profile:
        args.append("--isolated-profile")
    if url:
        args.extend(["--url", url])
    return args


def _start_chrome(
    port: int = _DEFAULT_PORT,
    url: Optional[str] = None,
    restart: bool = False,
    sync_profile: bool = True,
    isolated_profile: bool = False,
    background: bool = True,
) -> Dict[str, Any]:
    if not restart and not isolated_profile:
        status = _check_status(port)
        if status["ready"]:
            return {
                "success": True,
                "already_running": True,
                **status,
            }

    args = _build_start_args(port, url, restart, sync_profile, isolated_profile)

    if background:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        # Give Chrome a moment to bind CDP port (sync may take longer on first run)
        import time

        for _ in range(30):
            time.sleep(1)
            status = _check_status(port)
            if status["ready"]:
                return {
                    "success": True,
                    "already_running": False,
                    "pid": proc.pid,
                    "command": args,
                    **status,
                }
            if proc.poll() is not None:
                output = proc.stdout.read() if proc.stdout else ""
                raise RuntimeError(
                    f"[flow_coding_chrome_cdp] Chrome exited before CDP became ready\n"
                    f"  Command: {' '.join(args)}\n"
                    f"  Exit code: {proc.returncode}\n"
                    f"  Output:\n{output}"
                )

        output = ""
        if proc.stdout:
            try:
                output = proc.stdout.read(4096)
            except Exception:
                pass
        return {
            "success": False,
            "pid": proc.pid,
            "command": args,
            "message": "Chrome started but CDP not ready within 30s",
            "partial_output": output,
            "hint": "Profile sync may still be running; call check_status again.",
        }

    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    status = _check_status(port)
    return {
        "success": completed.returncode == 0 and status["ready"],
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        **status,
    }


def run(
    action: str,
    port: int = _DEFAULT_PORT,
    url: Optional[str] = None,
    restart: bool = False,
    sync_profile: bool = True,
    isolated_profile: bool = False,
    background: bool = True,
) -> Dict[str, Any]:
    """Flow Coding Chrome CDP Skill 主入口。"""
    if action == "get_guide":
        return _get_guide()

    if action == "get_profile_paths":
        return _get_profile_paths()

    if action == "get_playwright_snippet":
        return _get_playwright_snippet(port)

    if action == "check_status":
        return _check_status(port)

    if action == "start_chrome":
        return _start_chrome(
            port=port,
            url=url,
            restart=restart,
            sync_profile=sync_profile,
            isolated_profile=isolated_profile,
            background=background,
        )

    raise ValueError(
        f"[flow_coding_chrome_cdp] Unknown action: {action!r}\n"
        f"  Expected one of: get_guide, get_profile_paths, get_playwright_snippet, "
        f"check_status, start_chrome"
    )


if __name__ == "__main__":
    print(json.dumps(run(action="get_guide"), ensure_ascii=False, indent=2))
