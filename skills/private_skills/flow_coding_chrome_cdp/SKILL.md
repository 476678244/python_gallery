---
name: flow_coding_chrome_cdp
description: 启动 Google Chrome CDP 模式——同步现有 profile 到 Chrome-CDP 并开启 remote debugging，供 Playwright connectOverCDP 附着真实浏览器会话（书签、扩展、登录态）。适用于 Flow Coding 验证端、E2E 调试、需复用用户 Chrome 环境的场景。
---

# Flow Coding Chrome CDP Skill

## 核心理念

Flow Coding 验证端默认用 Playwright 内置 Chromium。但在以下场景需要**真实 Chrome + 现有 profile**：

- 已登录态、扩展、书签需保留
- 与日常浏览环境一致的可视验证
- `connectOverCDP` 附着正在运行的浏览器，而非每次冷启动

本 Skill 负责：**安全启动 Chrome CDP + profile 同步 + 状态检查 + Playwright 连接片段**。

---

## 🔒 铭刻：Profile 同步是默认，不是可选项

**用户反复强调、全生态不可协商：日常 Chrome 的登录态必须通过 rsync 同步到 Chrome-CDP。**

| 铭刻 | 规则 |
|------|------|
| **默认命令** | `start_chrome_cdp.sh --restart` → 退出 Chrome → rsync → CDP 启动 |
| **Python API** | `run(action="start_chrome", restart=True, sync_profile=True)` |
| **npm** | `npm run chrome:cdp` → `--restart`（**无** `--no-sync`） |
| **禁止** | Agent / 文档 / 错误提示 **不得** 默认推荐 `--no-sync` |
| **`--no-sync` 边界** | 仅用户明确要求 + Chrome-CDP 登录态已确认够用 |
| **Fail Fast** | 未 sync 无登录 → 中止，禁止 fallback isolated profile |

**Boss 直聘工作流（readonly_boss_hire）：**

```
日常 Chrome 登录 Boss → --restart（sync）→ connectOverCDP → 只读浏览
```

Soul 同源：[`flow_coding/Soul.md`](../../../flow_coding/Soul.md) · [`readonly_boss_hire/Soul.md`](../../../flow_coding/e2e/readonly_boss_hire/Soul.md)

---

## Chrome 136+ 约束

Chrome **不允许**在默认 profile 路径上开启 remote debugging：

```
DevTools remote debugging requires a non-default data directory.
```

因此 **existing 模式**采用兄弟目录策略：

| 角色 | macOS 路径 |
|------|------------|
| 源 profile（日常 Chrome） | `~/Library/Application Support/Google/Chrome` |
| CDP 启动目录（rsync 副本） | `~/Library/Application Support/Google/Chrome-CDP` |

`--restart` 流程：退出 Chrome → rsync 源 profile → 从 Chrome-CDP 以 CDP 启动。

> CDP 会话内的改动写入 Chrome-CDP，**不会**自动回写日常 Chrome。

---

## 与 Flow Coding 生态的关系

```
flow_coding_testing   → Playwright 跑 spec / 截图
flow_coding_logging   → 三路日志三角定位
flow_coding_chrome_cdp → 真实 Chrome CDP 会话（本 Skill）
```

典型 Phase 4 自愈流程：

1. `start_chrome(restart=True, sync_profile=True)` — **rsync 日常 profile**，CDP 就绪
2. `connectOverCDP` — Playwright 附着
3. 跑 E2E spec + `flow_coding_logging.tail_logs` 三角定位

---

## Action 类型

| Action | 功能 |
|--------|------|
| `get_guide` | 理论、profile 布局、工作流、注意事项 |
| `get_profile_paths` | 返回源/CDP/isolated 三路 profile 路径及是否存在 |
| `get_playwright_snippet` | 生成 `connectOverCDP` TypeScript 片段 |
| `check_status` | 探测 CDP 端口是否就绪（`/json/version`） |
| `start_chrome` | 执行 `start_chrome_cdp.sh` 启动 Chrome |

---

## 命令行（直接执行）

```bash
# 同步现有 profile 并以 CDP 启动（**默认推荐 — Boss 登录态靠此同步**）
skills/private_skills/flow_coding_chrome_cdp/scripts/start_chrome_cdp.sh --restart

# 打开待测 URL
skills/private_skills/flow_coding_chrome_cdp/scripts/start_chrome_cdp.sh --restart --url http://localhost:3000

# 高级：跳过同步（Chrome-CDP 登录态已够用、仅改启动参数时用）
skills/private_skills/flow_coding_chrome_cdp/scripts/start_chrome_cdp.sh --restart --no-sync

# 空白 automation profile
skills/private_skills/flow_coding_chrome_cdp/scripts/start_chrome_cdp.sh --isolated-profile
```

项目内快捷入口（委托到本 Skill）：

```bash
./flow_coding/scripts/start_chrome_cdp.sh --restart
```

---

## Python API

### check_status

```python
run(action="check_status", port=9222)
# → {"ready": true, "cdp_url": "http://127.0.0.1:9222", "browser": "Chrome/150..."}
```

### start_chrome

```python
run(
    action="start_chrome",
    restart=True,
    url="http://localhost:3000",
    port=9222,
    sync_profile=True,
    isolated_profile=False,
    background=True,
)
```

### get_playwright_snippet

```python
run(action="get_playwright_snippet", port=9222)
```

---

## Playwright 连接

```typescript
import { chromium } from '@playwright/test';

const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
const context = browser.contexts()[0] ?? await browser.newContext();
const page = context.pages()[0] ?? await context.newPage();
```

Flow Coding 标准 viewport：**1920×1080**（脚本默认 `--window-size=1920,1080`）。

---

## Fail Fast 规则

- Chrome 已运行但未开 CDP → 必须 `restart=true`，禁止静默失败
- 源 profile 目录不存在 → 立即报错
- CDP 端口被非 Chrome 进程占用 → 报错并提示换端口
- `start_chrome_cdp.sh` 缺失 → 报错含完整路径

### CDP WebSocket 被拒绝（zhipin.com / Playwright）

Chrome 111+ 默认限制 CDP WebSocket 来源。若终端出现：

```
Rejected an incoming WebSocket connection from the https://www.zhipin.com origin.
Use --remote-allow-origins=...
```

脚本已硬编码 `--remote-allow-origins=*`。**必须 `--restart` 重启 Chrome** 后生效。

```bash
./flow_coding/scripts/start_chrome_cdp.sh --restart
```

---

## 依赖

- Google Chrome（macOS / Linux）
- `rsync`（existing 模式 profile 同步）
- `curl`（CDP 状态探测）
- 无 Python 第三方依赖
