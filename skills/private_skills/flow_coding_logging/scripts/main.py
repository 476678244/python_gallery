"""
Flow Coding Logging Skill - Main Implementation
心流编程「三重反馈」基础设施技能主实现

此 skill 为 AI Agent 提供 Flow Coding 三重反馈（前端 + 后端 + Playwright）的
实践工具：搭建实时可 tail 的日志、读取三路日志快照、并基于三路信号做三角定位
（Triangulation）锁定问题根因层级。
"""
import os
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional


# Skill 定义元数据
SKILL_DEFINITION = {
    "name": "flow_coding_logging",
    "description": "搭建并使用 Flow Coding 三重反馈基础设施：让前后端 stdout 实时落盘可 tail -f，结合 Playwright 行为反馈做三角定位，快速锁定根因层级。",
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
                ],
                "description": "执行的操作类型",
            },
            "project_root": {
                "type": "string",
                "description": "项目根目录（其下应存在 logs/ 目录）",
            },
            "log_dir": {
                "type": "string",
                "description": "日志目录，默认 <project_root>/logs",
            },
            "lines": {
                "type": "integer",
                "description": "tail_logs 读取的行数，默认 20",
                "default": 20,
            },
            "frontend_request": {
                "type": "boolean",
                "description": "triangulate: ui.log 中是否观测到对应请求",
            },
            "frontend_status": {
                "type": "integer",
                "description": "triangulate: 前端观测到的状态码（省略表示无记录/超时）",
            },
            "backend_request": {
                "type": "boolean",
                "description": "triangulate: access.log 中是否观测到对应请求",
            },
            "backend_status": {
                "type": "integer",
                "description": "triangulate: 后端返回状态码（省略表示无记录）",
            },
            "backend_error": {
                "type": "boolean",
                "description": "triangulate: server.log 中是否出现异常堆栈/报错",
            },
        },
        "required": ["action"],
    },
}

# 三路日志的标准文件名
LOG_FILES = {
    "server": "server.log",   # 后端 stdout/stderr（应用日志 + print + 服务器默认/错误日志）
    "access": "access.log",   # 后端访问日志（每个 HTTP 请求 + 状态码）
    "ui": "ui.log",           # 前端 stdout/stderr（dev server 请求日志 + SSR 报错）
}


def _resolve_log_dir(project_root: Optional[str], log_dir: Optional[str]) -> Path:
    """解析日志目录。优先 log_dir，其次 <project_root>/logs。Fail fast。"""
    if log_dir:
        return Path(log_dir).expanduser()
    if project_root:
        return Path(project_root).expanduser() / "logs"
    raise ValueError(
        "[flow_coding_logging] Cannot resolve log directory\n"
        "  Provide either 'log_dir' or 'project_root'."
    )


def _tail_file(path: Path, lines: int) -> List[str]:
    """读取文件末尾 N 行（内存友好）。文件不存在返回空列表。"""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [ln.rstrip("\n") for ln in deque(f, maxlen=max(1, lines))]


def _get_guide() -> Dict[str, Any]:
    return {
        "success": True,
        "skill_name": "flow_coding_logging",
        "concept": "三重反馈 = ①行为(Playwright) + ②前端(ui.log) + ③后端(server.log+access.log)",
        "causal_chain": (
            "用户操作 → [②前端发出请求 ui.log] → [③后端处理并响应 access.log/server.log] "
            "→ [②前端接收并渲染 ui.log] → [①用户看到结果 Playwright 截图]"
        ),
        "why_three": "单一反馈只知'结果不对'，三路交叉验证才能定位'为什么不对'，避免反复试错。",
        "root_cause_table": [
            {"behavior": "结果错", "frontend": "无请求记录", "backend": "无请求记录", "layer": "前端：事件/状态未触发请求"},
            {"behavior": "结果错", "frontend": "请求 4xx/5xx", "backend": "有报错堆栈", "layer": "后端：逻辑/数据异常"},
            {"behavior": "结果错", "frontend": "请求 200", "backend": "200 + 日志正常", "layer": "前端：渲染/状态错误"},
            {"behavior": "结果错", "frontend": "请求 200", "backend": "异常但仍返回 200", "layer": "后端：吞掉异常、返回错误内容"},
            {"behavior": "结果错", "frontend": "请求超时", "backend": "无访问记录", "layer": "接口契约：URL/端口/代理错配"},
        ],
        "setup": {
            "backend": "应用入口 tee stdout/stderr 到 logs/server.log；访问日志单独写 logs/access.log（propagate=False 避免重复）。",
            "backend_warning": "tee 包装类必须委托 isatty()/fileno() 给真实流，否则服务器日志格式化器会因 AttributeError 崩溃。",
            "frontend": 'package.json dev 脚本: "next dev 2>&1 | tee ../../logs/ui.log"',
            "monitor": "tail -f logs/server.log logs/access.log logs/ui.log",
        },
        "self_healing_link": "三重反馈是自愈闭环的输入燃料：反馈越全越实时，方向假设越准，3×3 预算消耗越少。",
    }


def _get_tail_command(log_dir: Path) -> Dict[str, Any]:
    paths = [str(log_dir / LOG_FILES[k]) for k in ("server", "access", "ui")]
    return {
        "success": True,
        "log_dir": str(log_dir),
        "command": "tail -f " + " ".join(paths),
        "files": paths,
    }


def _check_setup(log_dir: Path) -> Dict[str, Any]:
    report = {}
    all_ok = True
    for key, fname in LOG_FILES.items():
        p = log_dir / fname
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        ok = exists
        all_ok = all_ok and ok
        report[key] = {
            "path": str(p),
            "exists": exists,
            "size_bytes": size,
            "empty": exists and size == 0,
        }
    return {
        "success": True,
        "log_dir": str(log_dir),
        "all_present": all_ok,
        "logs": report,
        "hint": "若某路缺失，三角定位会退化为单点猜测——请先按 get_guide 的 setup 落盘该路日志。",
    }


def _tail_logs(log_dir: Path, lines: int) -> Dict[str, Any]:
    snapshot = {}
    for key, fname in LOG_FILES.items():
        snapshot[key] = _tail_file(log_dir / fname, lines)
    return {
        "success": True,
        "log_dir": str(log_dir),
        "lines": lines,
        "server": snapshot["server"],
        "access": snapshot["access"],
        "ui": snapshot["ui"],
    }


def _triangulate(
    frontend_request: Optional[bool],
    frontend_status: Optional[int],
    backend_request: Optional[bool],
    backend_status: Optional[int],
    backend_error: Optional[bool],
) -> Dict[str, Any]:
    """根据三路观测信号定位根因层级（对应 SKILL.md 的根因层对照表）。"""

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

    # 1) 前端压根没发出请求，后端也没收到 → 前端事件/状态未触发
    if frontend_request is False and not backend_request:
        return _result(
            "frontend",
            "ui.log 无请求记录且 access.log 无对应请求：操作未触发网络请求。",
            "检查前端事件绑定、条件渲染、状态机是否真正发起了请求。",
        )

    # 2) 前端发了但后端没收到（超时/连不上）→ 接口契约
    if frontend_request and not backend_request:
        return _result(
            "api_contract",
            "ui.log 有请求但 access.log 无访问记录：请求未到达后端。",
            "核对 baseURL/端口/代理(NO_PROXY)、CORS、后端是否在线。",
        )

    # 3) 后端有报错堆栈 → 后端逻辑/数据异常（无论状态码）
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

    # 4) 后端返回错误状态码 → 后端
    if backend_status and backend_status >= 400:
        return _result(
            "backend",
            f"后端返回 {backend_status}：后端逻辑/数据/权限异常。",
            "查 server.log 对应时间点的异常与 access.log 状态码。",
        )

    # 5) 链路全通（前后端均 200，无后端报错）→ 前端渲染/状态
    if (frontend_status == 200 or frontend_request) and backend_status == 200:
        return _result(
            "frontend",
            "请求链路全通（前后端均 200，server.log 正常），但结果仍错：前端拿到正确数据却渲染/状态错误。",
            "检查前端数据映射、状态更新、组件渲染逻辑（如 snake_case→camelCase、空数组处理）。",
        )

    # 兜底：信息不足
    return _result(
        "unknown",
        "三路信号不足以判定根因层级。",
        "先用 tail_logs 读取三路日志快照补齐 frontend_request/status、backend_request/status、backend_error 后再 triangulate。",
    )


def run(
    action: str,
    project_root: Optional[str] = None,
    log_dir: Optional[str] = None,
    lines: int = 20,
    frontend_request: Optional[bool] = None,
    frontend_status: Optional[int] = None,
    backend_request: Optional[bool] = None,
    backend_status: Optional[int] = None,
    backend_error: Optional[bool] = None,
) -> Dict[str, Any]:
    """Flow Coding Logging Skill 主入口。"""
    if action == "get_guide":
        return _get_guide()

    if action == "get_tail_command":
        return _get_tail_command(_resolve_log_dir(project_root, log_dir))

    if action == "check_setup":
        return _check_setup(_resolve_log_dir(project_root, log_dir))

    if action == "tail_logs":
        return _tail_logs(_resolve_log_dir(project_root, log_dir), lines)

    if action == "triangulate":
        return _triangulate(
            frontend_request,
            frontend_status,
            backend_request,
            backend_status,
            backend_error,
        )

    raise ValueError(
        f"[flow_coding_logging] Unknown action: {action!r}\n"
        f"  Expected one of: get_guide, get_tail_command, check_setup, tail_logs, triangulate"
    )


if __name__ == "__main__":
    import json

    print(json.dumps(run(action="get_guide"), ensure_ascii=False, indent=2))
</CodeContent>
<parameter name="EmptyFile">false
