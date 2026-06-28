---
name: flow_coding_logging
description: 实践 Flow Coding 的「三重反馈」基础设施——让前端、后端的所有 stdout 实时落盘并可 tail -f，结合 Playwright 行为反馈，通过三角定位（Triangulation）快速锁定问题根因层级（前端/后端/数据/接口契约）。适用于前后端协同调试与自愈闭环。
---

# Flow Coding Logging Skill（三重反馈）

## 核心理念

Flow Coding 的自愈闭环之所以能可靠收敛，根本在于 AI 拿到的不是单一信号，而是**三路相互独立、可交叉验证的实时反馈**。本 Skill 负责搭建并使用这套反馈基础设施。

**三重反馈 = ① 行为反馈（Playwright）+ ② 前端反馈（ui.log）+ ③ 后端反馈（server.log + access.log）**

### 为什么单一反馈不够

只看 Playwright 截图/断言，只能知道"结果不对"，却不知道"为什么不对"：

```
断言失败：页面显示 "0 skills"
  → 是前端没渲染？还是后端返回空？还是请求压根没发出？
  → 无从判断，只能猜 → 陷入"反复试错"
```

信息不足导致方向假设错误，浪费 3 × 3 自愈预算。

---

## 三路反馈的分工

| 反馈源 | 信号载体 | 回答的问题 | 观测层 |
|--------|----------|------------|--------|
| ① 行为反馈 | Playwright 截图 + 断言 | 用户**看到/体验到**什么？ | 表现层（端到端结果） |
| ② 前端反馈 | `logs/ui.log`（前端 stdout + 请求状态码 + SSR 报错） | 前端**做了**什么、请求**发出**了吗？ | 前端运行层 |
| ③ 后端反馈 | `logs/server.log` + `logs/access.log`（应用日志 + 服务器 + 每个 HTTP 请求） | 后端**收到**请求了吗、**返回**了什么、**报错**了吗？ | 后端运行层 |

三者覆盖了一次用户操作的**完整因果链**：

```
用户操作 → [②前端发出请求] → [③后端处理并响应] → [②前端接收并渲染] → [①用户看到结果]
            ui.log              access.log/server.log    ui.log              Playwright 截图
```

---

## 三角定位（Triangulation）：交叉验证锁定根因

三路信号同时实时可读（`tail -f`）时，AI 不再"猜方向"，而是**交叉比对**直接锁定根因层级：

```
现象（①）：Playwright 断言失败 — 页面显示 "0 skills"

交叉比对：
  ② ui.log:      POST /api/skills 200 in 16ms      ← 前端请求发出且成功
  ③ access.log:  GET /skills HTTP/1.1 200 OK        ← 后端收到并返回 200
  ③ server.log:  Found 58 skills ... ls: Directory not found  ← 后端逻辑异常！

结论：请求链路全通（②③状态码均 200），但 server.log 暴露后端
      在 ls 一个不存在的路径 → 根因在后端，且是路径解析问题。一次定位，无需试错。
```

### 根因层对照表（一眼定位）

| ① 行为 | ② 前端(ui.log) | ③ 后端(access/server) | 根因层级 |
|--------|----------------|------------------------|----------|
| 结果错 | 无请求记录 | 无请求记录 | 前端：事件/状态未触发请求 |
| 结果错 | 请求 4xx/5xx | 有报错堆栈 | 后端：逻辑/数据异常 |
| 结果错 | 请求 200 | 200 + 日志正常 | 前端：拿到正确数据但渲染/状态错误 |
| 结果错 | 请求 200 | server.log 有异常但仍返回 200 | 后端：吞掉异常、返回了错误内容 |
| 结果错 | 请求超时 | 无访问记录 | 接口契约：URL/端口/代理错配 |

---

## 工程前提：三路日志必须实时、可 tail

三重反馈成立的硬性前提是**所有 stdout 都被实时落盘、可 `tail -f`**，无论服务以何种方式启动（脚本 / IDE 调试 / 手动）：

- **后端**：在应用入口 tee `stdout`/`stderr` 到 `logs/server.log`；服务器访问日志单独写 `logs/access.log`。
- **前端**：`dev` 脚本将前端 dev server 输出 `tee` 到 `logs/ui.log`。
- **统一监控**：`tail -f logs/server.log logs/access.log logs/ui.log`。

> 若任一路反馈缺失（如后端只输出到 IDE 控制台、未落盘），三角定位即退化为单点猜测，自愈闭环的收敛性随之下降。

### 后端落盘范式（Python / FastAPI 示例）

在应用入口处 tee stdout/stderr，使所有 print/日志/服务器输出都写入 `logs/server.log`：

```python
import sys
from pathlib import Path

class _Tee:
    def __init__(self, primary, *streams):
        self._primary = primary
        self._streams = (primary, *streams)
    def write(self, data):
        for s in self._streams:
            try:
                s.write(data); s.flush()
            except Exception:
                pass
        return len(data)
    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass
    def isatty(self):
        try:
            return self._primary.isatty()
        except Exception:
            return False
    def fileno(self):
        return self._primary.fileno()
    def __getattr__(self, name):
        return getattr(self._primary, name)

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_SERVER_LOG = open(_LOG_DIR / "server.log", "a", buffering=1, encoding="utf-8")
sys.stdout = _Tee(sys.__stdout__, _SERVER_LOG)
sys.stderr = _Tee(sys.__stderr__, _SERVER_LOG)
```

> 关键点：`_Tee` 必须委托 `isatty()` / `fileno()` 给真实流，否则 uvicorn/服务器的日志格式化器会因 `AttributeError` 崩溃。

访问日志单独落盘（uvicorn `log_config` 示例）：access logger 用独立 FileHandler 写 `logs/access.log`，并 `propagate: False`，避免与 stdout 重复。

### 前端落盘范式（Next.js 示例）

```json
{
  "scripts": {
    "dev": "next dev 2>&1 | tee ../../logs/ui.log"
  }
}
```

> `2>&1` 合并 stderr，`tee` 同时输出到终端与文件，保证既可见又可 tail。

---

## 与自愈闭环的关系

三重反馈是自愈闭环的**输入燃料**——反馈越完整、越实时，方向假设越准，3 × 3 预算消耗越少：

```
Playwright 失败
   ↓
AI 同时读取 ①截图 + ②ui.log + ③server.log/access.log
   ↓
三角定位 → 锁定根因层级（前端/后端/数据/契约）
   ↓
在正确位置修复（最小上游修复）
   ↓
重跑 Playwright → 三路信号重新比对 → 收敛或换方向（受 3×3 约束）
```

---

## 实际执行功能

本 Skill 提供可执行的日志基础设施工具。

| Action | 功能 |
|--------|------|
| `get_guide` | 获取三重反馈理论 + 落盘范式指南 |
| `get_tail_command` | 生成统一监控的 `tail -f` 命令 |
| `check_setup` | 检查三路日志文件是否存在且非空 |
| `tail_logs` | 读取三路日志最近 N 行（只读快照） |
| `triangulate` | 根据观测到的三路信号，定位根因层级 |

### get_tail_command

```python
run(action="get_tail_command", project_root="/path/to/project")
# → "tail -f /path/to/project/logs/server.log /path/to/project/logs/access.log /path/to/project/logs/ui.log"
```

### check_setup / tail_logs

```python
run(action="check_setup", project_root="/path/to/project")
# → 每路日志的 exists / size / 是否实时

run(action="tail_logs", project_root="/path/to/project", lines=20)
# → {"server": [...], "access": [...], "ui": [...]}
```

### triangulate（三角定位）

```python
run(
    action="triangulate",
    frontend_request=True,      # ui.log 中是否有请求记录
    frontend_status=200,        # 前端观测到的状态码（None 表示无/超时）
    backend_request=True,       # access.log 中是否有对应请求
    backend_status=200,         # 后端返回状态码
    backend_error=True          # server.log 中是否有异常堆栈
)
# → {"root_cause_layer": "backend", "reason": "...", "next_action": "..."}
```

---

## 依赖

无第三方依赖，仅使用 Python 标准库（`pathlib`、`collections.deque`）。
</CodeContent>
<parameter name="EmptyFile">false
