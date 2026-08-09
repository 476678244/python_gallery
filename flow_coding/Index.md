# Flow Coding Index

> 川流编程资源索引 — 方法论、Skills、Agent 配置、E2E 验证入口
> 上游仓库：[476678244/flow_coding](https://github.com/476678244/flow_coding)

---

## 快速导航

| 文档 | 路径 | 说明 |
|------|------|------|
| **方法论（完整版）** | [`docs/flow_coding.md`](../docs/flow_coding.md) | 川流编程定义、原则、Playwright 模板、三重反馈、5 阶段算法 |
| **Agent 人格** | [`Soul.md`](Soul.md) | 川流 Agent 性格、价值观、交互风格 |
| **Agent 规范** | [`Agents.md`](Agents.md) | 系统提示词、Skills 调用、E2E 约定、3 × 3 规则 |
| **E2E 运行指南** | [`test/e2e/README.md`](../test/e2e/README.md) | 服务启动、NO_PROXY、运行命令、踩坑记录 |
| **全局开发规范** | [`Agents.md`](../Agents.md) | WORKSPACE_DIR、Fail Fast、Python 3.11 |

---

## 公式与核心概念

```
Flow Coding = Vibe Coding（生产端自动化） + Dev Automation（验证端自动化）
```

| 概念 | 一句话 |
|------|--------|
| **5 阶段算法** | 基线 → 生成 → 测试适配 → 自愈 → 收敛确认 |
| **三重反馈** | Playwright 行为 + ui.log 前端 + server/access.log 后端 + 会话记录 |
| **三角定位** | 日志与会话交叉比对，一次锁定根因；**禁止只靠截图猜** |
| **3 × 3 原则** | 单方向 ≤3 次，方向切换 ≤3 次，最多 9 次触顶即停 |
| **注意力守恒** | 开发者只在意图层和最终判断层，中间轮次零切换 |

---

## Skills

| Skill | 路径 | 职责 |
|-------|------|------|
| **flow_coding_chrome_cdp** | [`skills/private_skills/flow_coding_chrome_cdp/`](../skills/private_skills/flow_coding_chrome_cdp/) | 真实 Chrome CDP 启动、profile 同步、connectOverCDP |
| **flow_coding_testing** | [`skills/private_skills/flow_coding_testing/`](../skills/private_skills/flow_coding_testing/) | 5 阶段指南、Playwright 执行、截图对比、自愈闭环 |
| **flow_coding_logging** | [`skills/private_skills/flow_coding_logging/`](../skills/private_skills/flow_coding_logging/) | 三路日志落盘、tail 监控、三角定位 |

### Skills 与 Phase 映射

| Phase | flow_coding_testing | flow_coding_logging | flow_coding_chrome_cdp |
|-------|---------------------|---------------------|----------------------|
| 0 准备 | — | `check_setup` | `start_chrome`, `check_status` |
| 1 基线 | `run_playwright`, `check_phase` | `check_setup` | `check_status` |
| 2 生成 | — | — | — |
| 3 测试适配 | `check_phase` | — | — |
| 4 自愈 | `run_playwright`, `compare_screenshots` | `tail_logs`, `triangulate` | `check_status` |
| 5 收敛 | `report_completion` | `tail_logs`（可选确认） | — |

---

## E2E 验证工程

### 主入口：`test/e2e/`

本仓库的 Playwright 验证工程统一放在 `test/e2e/`，**验证端只用 TypeScript spec，不写 Python 测试脚本**。

```
test/e2e/
├── playwright.config.ts              # 1920×1080, headless:false, retries:1
├── basic-chat-flow-coding.spec.ts    # 基础对话 5 阶段
├── skill-tree.spec.ts                # Skill Tree 4 主目录
├── skill-recognition-flow-coding.spec.ts
├── skills-path-activation.spec.ts
├── prompt-inspect-flow-coding.spec.ts
├── chat-input-dropzone.spec.ts
├── jupyterhub-terminal.spec.ts
└── README.md
```

### 运行命令

```bash
# 前置：API :8000 + 前端 :3000 已启动，NO_PROXY 已设置
cd safeclaw-ui/my-app
npx playwright test --config ../../test/e2e/playwright.config.ts

# 单个 spec
npx playwright test --config ../../test/e2e/playwright.config.ts basic-chat-flow-coding.spec.ts

# 查看报告
npx playwright show-report
```

### Flow Coding 标准 spec 清单

| Spec | Phase 覆盖 | 说明 |
|------|------------|------|
| `basic-chat-flow-coding.spec.ts` | 1–5 | 页面加载 → 对话 → 多轮 → 自愈 → 截图 |
| `skill-recognition-flow-coding.spec.ts` | 1–5 | Skill 路由识别 |
| `prompt-inspect-flow-coding.spec.ts` | 1–5 | Prompt Inspect + Private Skills |
| `skills-path-activation.spec.ts` | 1–4 | Skills Path 面板激活 |
| `skill-tree.spec.ts` | T1–T10 | 4 主目录加载、toggle、persist |

---

## `flow_coding/e2e/` — 脚手架参考

```
flow_coding/
├── Soul.md
├── Agents.md
├── Index.md          # 本文件
└── e2e/              # 方法论级 Playwright 脚手架（可独立复制到新项目）
    ├── package.json          # 独立 e2e package
    └── playwright.config.ts  # Flow Coding 标准配置模板
```

**定位**：`flow_coding/e2e/` 是**可移植的验证端脚手架**，与上游 [476678244/flow_coding](https://github.com/476678244/flow_coding) 仓库对齐。`test/e2e/` 是本项目的**实际运行实例**。

复制到新项目时：

```bash
cp -r flow_coding/e2e/ <new-project>/test/e2e/
cd <new-project>/test/e2e && npm install && npx playwright install chromium
```

模板约定见 [`docs/flow_coding.md` § 可复用模板](../docs/flow_coding.md)。

### readonly_boss_hire — Boss 直聘只读工作脚本

> **READONLY ONLY** + **工作脚本（非回归测试）**：Boss 直聘上只能浏览；Playwright 跑的是可复用工作流，产物落盘到 `BOSS_HIRE_WORKDIR`。

| 文档 | 路径 |
|------|------|
| Soul / Agents / Index | [`e2e/readonly_boss_hire/`](e2e/readonly_boss_hire/Index.md) |

```bash
cd flow_coding/e2e
npm run run:boss-recommend   # 结构探查工作流
npm run run:boss-login       # 登录态探查
```

---

### Chrome CDP 模式

> 🔒 **铭刻**：`--restart` = 退出 Chrome + **rsync 日常 profile → Chrome-CDP** + CDP 重启。  
> Boss 登录态同步靠此；**禁止**默认推荐 `--no-sync`。

用**现有 Chrome profile**（书签、扩展、登录态）启动 CDP：

```bash
# 退出 Chrome → **同步日常 profile（含 Boss 登录态）** → 以 CDP 模式重启
./flow_coding/scripts/start_chrome_cdp.sh --restart

# 打开指定 URL
./flow_coding/scripts/start_chrome_cdp.sh --restart --url http://localhost:3000

# 高级：跳过同步（仅当 Chrome-CDP 登录态已够用、只想快速改 flag 时）
./flow_coding/scripts/start_chrome_cdp.sh --restart --no-sync

# 空白 automation profile
./flow_coding/scripts/start_chrome_cdp.sh --isolated-profile
```

| 选项 | 说明 |
|------|------|
| `--restart` | 退出 Chrome，**rsync 日常 profile → Chrome-CDP**，CDP 重启（Boss 登录态同步靠这个） |
| `--no-sync` | 高级选项：跳过 rsync，复用上次 `Chrome-CDP`（**不会**拉取日常 Chrome 新登录） |
| `--isolated-profile` | 独立空白 profile |

Chrome 136+ 不允许在默认 profile 路径上开 CDP，因此脚本会：
- **源 profile**：`~/Library/Application Support/Google/Chrome`
- **CDP 启动目录**（同步副本）：`~/Library/Application Support/Google/Chrome-CDP`

---

## 三重反馈基础设施

### 日志文件

| 文件 | 来源 | 观测层 |
|------|------|--------|
| `logs/ui.log` | 前端 dev server stdout | 请求发出、状态码、SSR 报错 |
| `logs/server.log` | 后端 stdout/stderr | 应用日志、异常堆栈 |
| `logs/access.log` | 后端 HTTP 访问日志 | 每个请求 + 状态码 |

### 统一监控

```bash
tail -f logs/server.log logs/access.log logs/ui.log
```

### 查问题纪律

定位问题必须读 `logs/*` + 对应 `session_id` 会话记录；截图只作线索，不作根因结论。

### 根因层速查

| ① Playwright | ② ui.log | ③ backend | 根因 |
|--------------|----------|-----------|------|
| 结果错 | 无请求 | 无请求 | 前端未触发 |
| 结果错 | 4xx/5xx | 有堆栈 | 后端异常 |
| 结果错 | 200 | 200 正常 | 前端渲染/状态 |
| 结果错 | 200 | 异常仍 200 | 后端吞异常 |
| 结果错 | 超时 | 无记录 | 接口契约错配 |

---

## 5 阶段算法速查

```
PHASE 1  建立验证基线     → 跑 spec，确认 100% 绿
PHASE 2  意图表达与生成     → 实现变更，最小上游修复
PHASE 3  测试规范适配       → 更新 locator / 断言
PHASE 4  自愈闭环           → 三重反馈定位 → 修复 → 3×3 重跑
PHASE 5  最终收敛确认       → 全绿截图/报告 → 交还开发者
```

---

## 目录结构总览

```
python_gallery/
├── flow_coding/                       # ← 你在这里
│   ├── Soul.md                        # Agent 人格
│   ├── Agents.md                      # Agent 规范 + E2E 约定
│   ├── Index.md                       # 资源索引（本文件）
│   ├── scripts/start_chrome_cdp.sh    # Chrome CDP 启动脚本
│   └── e2e/                           # 可移植脚手架
├── docs/flow_coding.md                # 方法论长文
├── test/e2e/                          # 实际 Playwright 工程
├── skills/private_skills/
│   ├── flow_coding_chrome_cdp/        # Chrome CDP Skill
│   ├── flow_coding_testing/           # 验证端 Skill
│   └── flow_coding_logging/           # 三重反馈 Skill
└── Agents.md                          # SafeClaw 全局规范
```

---

## 相关链接

- 上游方法论仓库：[github.com/476678244/flow_coding](https://github.com/476678244/flow_coding)
- 中文 README：[README_zh.md](https://github.com/476678244/flow_coding/blob/main/README_zh.md)（上游）
- SafeClaw 项目 README：[README.md](../README.md) § 川流编程工作流
