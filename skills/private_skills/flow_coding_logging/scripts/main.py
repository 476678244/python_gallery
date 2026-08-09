"""
Flow Coding Logging Skill - Main Implementation
心流编程「三重反馈」+ CDP/浏览器日志落盘基础设施

为 AI Agent 提供：
- 全栈三重反馈（前端 ui.log + 后端 server/access.log + Playwright 行为）
- Boss 直聘 / CDP 场景第四路反馈（browser-console/network/navigation + cdp-tabs）
- 日志 tail、快照导出、CDP 状态同步
"""
import json
import os
import shutil
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SKILL_DEFINITION = {
    "name": "flow_coding_logging",
    "description": (
        "搭建并使用 Flow Coding 反馈基础设施：全栈三路日志 + CDP/浏览器日志落盘，"
        "可 tail/export/sync，结合 Playwright 做三角/四角定位。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_guide",
                    "get_tail_command",
                    "check_setup",
                    "tail_logs",
                    "triangulate",
                    "sync_cdp_status",
                    "export_snapshot",
                ],
                "description": "执行的操作类型",
            },
            "project_root": {
                "type": "string",
                "description": "项目根目录（其下应存在 logs/ 目录）",
            },
            "log_dir": {
                "type": "string",
                "description": "日志目录；省略时按 profile 解析",
            },
            "profile": {
                "type": "string",
                "enum": ["fullstack", "boss_hire", "all"],
                "description": "日志配置：fullstack=server/access/ui；boss_hire=浏览器+CDP；all=合并",
                "default": "fullstack",
            },
            "lines": {
                "type": "integer",
                "description": "tail_logs / export_snapshot 读取的行数，默认 50",
                "default": 50,
            },
            "cdp_url": {
                "type": "string",
                "description": "CDP HTTP 端点，默认 http://127.0.0.1:9222",
                "default": "http://127.0.0.1:9222",
            },
            "output_dir": {
                "type": "string",
                "description": "export_snapshot 输出目录，默认 <log_dir>/../reports",
            },
            "frontend_request": {"type": "boolean"},
            "frontend_status": {"type": "integer"},
            "backend_request": {"type": "boolean"},
            "backend_status": {"type": "integer"},
            "backend_error": {"type": "boolean"},
        },
        "required": ["action"],
    },
}

DEFAULT_BOSS_HIRE_WORKDIR = os.environ.get(
    "BOSS_HIRE_WORKDIR",
    os.path.expanduser("~/Downloads/nicole/boss直聘_工作目录"),
)

FULLSTACK_LOG_FILES = {
    "server": "server.log",
    "access": "access.log",
    "ui": "ui.log",
}

BROWSER_LOG_FILES = {
    "browser_console": "browser-console.log",
    "browser_network": "browser-network.log",
    "browser_navigation": "browser-navigation.log",
    "cdp_tabs": "cdp-tabs.json",
    "cdp_version": "cdp-version.json",
}


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _resolve_log_dir(
    project_root: Optional[str],
    log_dir: Optional[str],
    profile: str,
) -> Path:
    if log_dir:
        return Path(log_dir).expanduser()

    if profile in ("boss_hire", "all"):
        return Path(DEFAULT_BOSS_HIRE_WORKDIR).expanduser() / "logs"

    if project_root:
        return Path(project_root).expanduser() / "logs"

    raise ValueError(
        "[flow_coding_logging] Cannot resolve log directory\n"
        "  Provide 'log_dir', 'project_root', or profile='boss_hire'."
    )


def _log_files_for_profile(profile: str) -> Dict[str, str]:
    if profile == "fullstack":
        return dict(FULLSTACK_LOG_FILES)
    if profile == "boss_hire":
        return dict(BROWSER_LOG_FILES)
    return {**FULLSTACK_LOG_FILES, **BROWSER_LOG_FILES}


def _tail_file(path: Path, lines: int) -> List[str]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [ln.rstrip("\n") for ln in deque(f, maxlen=max(1, lines))]


def _read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fetch_cdp_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def _get_guide() -> Dict[str, Any]:
    return {
        "success": True,
        "skill_name": "flow_coding_logging",
        "concept": (
            "全栈三重反馈 = ①行为(Playwright) + ②前端(ui.log) + ③后端(server.log+access.log)；"
            "CDP/Boss 直聘扩展第四路 = ④浏览器(console/network/navigation) + CDP tabs"
        ),
        "log_profiles": {
            "fullstack": list(FULLSTACK_LOG_FILES.keys()),
            "boss_hire": list(BROWSER_LOG_FILES.keys()),
            "all": list(_log_files_for_profile("all").keys()),
        },
        "boss_hire_log_dir": str(Path(DEFAULT_BOSS_HIRE_WORKDIR) / "logs"),
        "causal_chain_fullstack": (
            "用户操作 → [②前端 ui.log] → [③后端 access/server.log] "
            "→ [②前端 ui.log] → [①Playwright 截图]"
        ),
        "causal_chain_boss_hire": (
            "页面加载 → [④browser-network.log] → [④browser-console.log] "
            "→ [④browser-navigation.log] → [①Playwright 截图/断言]"
        ),
        "setup": {
            "fullstack_backend": "tee stdout/stderr → logs/server.log；access 单独 logs/access.log",
            "fullstack_frontend": '"dev": "next dev 2>&1 | tee ../../logs/ui.log"',
            "boss_hire_browser": (
                "Playwright connectCdpBrowser() 自动 installBrowserLogExport → "
                f"{DEFAULT_BOSS_HIRE_WORKDIR}/logs/browser-*.log"
            ),
            "boss_hire_cdp": "run(action='sync_cdp_status') → cdp-tabs.json + cdp-version.json",
            "monitor_fullstack": "tail -f logs/server.log logs/access.log logs/ui.log",
            "monitor_boss_hire": (
                f"tail -f {DEFAULT_BOSS_HIRE_WORKDIR}/logs/browser-console.log "
                f"{DEFAULT_BOSS_HIRE_WORKDIR}/logs/browser-network.log "
                f"{DEFAULT_BOSS_HIRE_WORKDIR}/logs/browser-navigation.log"
            ),
        },
        "agent_workflow": [
            "1. Playwright 失败或页面异常",
            "2. run(action='tail_logs', profile='boss_hire', lines=80)",
            "3. run(action='sync_cdp_status') 刷新 CDP tab 列表",
            "4. run(action='export_snapshot', profile='all') 生成可读 markdown 报告",
            "5. 交叉比对 ①截图 + ④network/console + cdp-tabs 定位根因",
        ],
    }


def _get_tail_command(log_dir: Path, profile: str) -> Dict[str, Any]:
    files_map = _log_files_for_profile(profile)
    paths = [str(log_dir / fname) for fname in files_map.values()]
    return {
        "success": True,
        "profile": profile,
        "log_dir": str(log_dir),
        "command": "tail -f " + " ".join(paths),
        "files": paths,
    }


def _check_setup(log_dir: Path, profile: str) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    any_present = False
    for key, fname in _log_files_for_profile(profile).items():
        p = log_dir / fname
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        if exists:
            any_present = True
        report[key] = {
            "path": str(p),
            "exists": exists,
            "size_bytes": size,
            "empty": exists and size == 0,
        }
    return {
        "success": True,
        "profile": profile,
        "log_dir": str(log_dir),
        "any_present": any_present,
        "logs": report,
        "hint": (
            "全栈：按 get_guide.setup 落盘 server/access/ui。"
            "Boss 直聘：跑 connectCdpBrowser() 的 Playwright spec 自动生成 browser-*.log；"
            "sync_cdp_status 写入 cdp-*.json。"
        ),
    }


def _tail_logs(log_dir: Path, profile: str, lines: int) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {}
    for key, fname in _log_files_for_profile(profile).items():
        path = log_dir / fname
        if fname.endswith(".json"):
            snapshot[key] = _read_json_file(path)
        else:
            snapshot[key] = _tail_file(path, lines)
    return {
        "success": True,
        "profile": profile,
        "log_dir": str(log_dir),
        "lines": lines,
        **snapshot,
    }


def _sync_cdp_status(log_dir: Path, cdp_url: str) -> Dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    base = cdp_url.rstrip("/")

    errors: List[str] = []
    version_path = log_dir / BROWSER_LOG_FILES["cdp_version"]
    tabs_path = log_dir / BROWSER_LOG_FILES["cdp_tabs"]

    version_data: Optional[Any] = None
    tabs_data: Optional[Any] = None

    try:
        version_data = _fetch_cdp_json(f"{base}/json/version")
        version_path.write_text(
            json.dumps(
                {"fetchedAt": datetime.now(timezone.utc).isoformat(), "data": version_data},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        errors.append(f"version: {e}")

    try:
        tabs_data = _fetch_cdp_json(f"{base}/json/list")
        tabs_path.write_text(
            json.dumps(
                {"fetchedAt": datetime.now(timezone.utc).isoformat(), "tabs": tabs_data},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        errors.append(f"tabs: {e}")

    if errors and version_data is None and tabs_data is None:
        raise ValueError(
            "[flow_coding_logging] sync_cdp_status failed\n"
            f"  CDP URL: {cdp_url}\n"
            f"  Errors: {errors}\n"
            "  Hint: start Chrome CDP first (flow_coding_chrome_cdp / start_chrome_cdp.sh)"
        )

    return {
        "success": True,
        "cdp_url": cdp_url,
        "log_dir": str(log_dir),
        "cdp_version_path": str(version_path),
        "cdp_tabs_path": str(tabs_path),
        "tab_count": len(tabs_data) if isinstance(tabs_data, list) else None,
        "errors": errors or None,
    }


def _export_snapshot(
    log_dir: Path,
    profile: str,
    lines: int,
    output_dir: Optional[str],
) -> Dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = _utc_stamp()
    out_root = Path(output_dir).expanduser() if output_dir else log_dir.parent / "reports"
    out_root.mkdir(parents=True, exist_ok=True)

    report_md = out_root / f"log-snapshot-{stamp}.md"
    bundle_dir = out_root / f"log-snapshot-{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    sections: List[str] = [
        f"# Log Snapshot — {stamp}",
        "",
        f"- **profile**: `{profile}`",
        f"- **log_dir**: `{log_dir}`",
        f"- **lines per text log**: {lines}",
        "",
    ]

    copied: List[str] = []
    for key, fname in _log_files_for_profile(profile).items():
        src = log_dir / fname
        sections.append(f"## {key} (`{fname}`)")
        sections.append("")

        if not src.exists():
            sections.append("_（文件不存在）_")
            sections.append("")
            continue

        dest = bundle_dir / fname
        shutil.copy2(src, dest)
        copied.append(str(dest))

        if fname.endswith(".json"):
            data = _read_json_file(src)
            sections.append("```json")
            sections.append(json.dumps(data, ensure_ascii=False, indent=2)[:8000])
            sections.append("```")
        else:
            tail = _tail_file(src, lines)
            sections.append("```")
            sections.extend(tail[-lines:])
            sections.append("```")
        sections.append("")

    report_md.write_text("\n".join(sections), encoding="utf-8")

    return {
        "success": True,
        "profile": profile,
        "log_dir": str(log_dir),
        "report_path": str(report_md),
        "bundle_dir": str(bundle_dir),
        "copied_files": copied,
        "hint": f"Agent 可直接 Read `{report_md}` 分析问题",
    }


def _triangulate(
    frontend_request: Optional[bool],
    frontend_status: Optional[int],
    backend_request: Optional[bool],
    backend_status: Optional[int],
    backend_error: Optional[bool],
) -> Dict[str, Any]:
    def _result(layer, reason, next_action):
        return {
            "success": True,
            "root_cause_layer": layer,
            "reason": reason,
            "next_action": next_action,
            "observed": {
                "frontend_request": frontend_request,
                "frontend_status": frontend_status,
                "backend_request": backend_request,
                "backend_status": backend_status,
                "backend_error": backend_error,
            },
        }

    if frontend_request is False and not backend_request:
        return _result(
            "frontend",
            "ui.log 无请求记录且 access.log 无对应请求：操作未触发网络请求。",
            "检查前端事件绑定、条件渲染、状态机是否真正发起了请求。",
        )

    if frontend_request and not backend_request:
        return _result(
            "api_contract",
            "ui.log 有请求但 access.log 无访问记录：请求未到达后端。",
            "核对 baseURL/端口/代理(NO_PROXY)、CORS、后端是否在线。",
        )

    if backend_error:
        if backend_status and backend_status < 400:
            return _result(
                "backend",
                f"server.log 出现异常，但仍返回 {backend_status}：后端吞掉异常、返回了错误内容。",
                "定位 server.log 异常堆栈根因；确保异常不被静默吞掉（Fail Fast）。",
            )
        return _result(
            "backend",
            "server.log 出现异常堆栈：后端逻辑/数据异常。",
            "按 server.log 堆栈定位根因，在后端最小上游修复。",
        )

    if backend_status and backend_status >= 400:
        return _result(
            "backend",
            f"后端返回 {backend_status}：后端逻辑/数据/权限异常。",
            "查 server.log 对应时间点的异常与 access.log 状态码。",
        )

    if (frontend_status == 200 or frontend_request) and backend_status == 200:
        return _result(
            "frontend",
            "请求链路全通（前后端均 200，server.log 正常），但结果仍错：前端渲染/状态错误。",
            "检查前端数据映射、状态更新、组件渲染逻辑。",
        )

    return _result(
        "unknown",
        "三路信号不足以判定根因层级。",
        "先用 tail_logs / export_snapshot 补齐日志，Boss 直聘场景加 profile='boss_hire' 读 browser 日志。",
    )


def run(
    action: str,
    project_root: Optional[str] = None,
    log_dir: Optional[str] = None,
    profile: str = "fullstack",
    lines: int = 50,
    cdp_url: str = "http://127.0.0.1:9222",
    output_dir: Optional[str] = None,
    frontend_request: Optional[bool] = None,
    frontend_status: Optional[int] = None,
    backend_request: Optional[bool] = None,
    backend_status: Optional[int] = None,
    backend_error: Optional[bool] = None,
) -> Dict[str, Any]:
    if action == "get_guide":
        return _get_guide()

    if action == "triangulate":
        return _triangulate(
            frontend_request,
            frontend_status,
            backend_request,
            backend_status,
            backend_error,
        )

    resolved_dir = _resolve_log_dir(project_root, log_dir, profile)

    if action == "get_tail_command":
        return _get_tail_command(resolved_dir, profile)

    if action == "check_setup":
        return _check_setup(resolved_dir, profile)

    if action == "tail_logs":
        return _tail_logs(resolved_dir, profile, lines)

    if action == "sync_cdp_status":
        return _sync_cdp_status(resolved_dir, cdp_url)

    if action == "export_snapshot":
        return _export_snapshot(resolved_dir, profile, lines, output_dir)

    raise ValueError(
        f"[flow_coding_logging] Unknown action: {action!r}\n"
        "  Expected: get_guide, get_tail_command, check_setup, tail_logs, "
        "triangulate, sync_cdp_status, export_snapshot"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        act = sys.argv[1]
        kwargs: Dict[str, Any] = {"action": act}
        if act in ("tail_logs", "export_snapshot") and len(sys.argv) > 2:
            kwargs["profile"] = sys.argv[2]
        print(json.dumps(run(**kwargs), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(run(action="get_guide"), ensure_ascii=False, indent=2))
