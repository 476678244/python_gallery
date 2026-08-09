# Readonly Boss Hire — Index

> Boss 直聘只读浏览 — **可复用工作脚本**索引（Playwright 执行，非回归测试）
> **所有 Boss 直聘操作：READONLY ONLY，零 WRITE**

---

## ⚠️ 第一法则

```
Boss 直聘（zhipin.com）= 只读浏览
✅ 看、滚、截图、摘录到本地
❌ 打招呼、发消息、发布、收藏、提交表单 — 一切 write 禁止
```

详见 [`Agents.md`](Agents.md) 禁止清单。

---

## 🔒 铭刻：CDP 登录态同步（第二法则）

```
① 日常 Chrome 登录 Boss 直聘
② ./flow_coding/scripts/start_chrome_cdp.sh --restart   ← 默认，rsync 同步 profile
③ npm run chrome:cdp / connectOverCDP
```

| 规则 | 说明 |
|------|------|
| **同步是默认** | `--restart` 含 rsync：`Chrome` → `Chrome-CDP` |
| **禁止默认 `--no-sync`** | Agent、npm、错误提示均不得推荐跳过 sync |
| **Fail Fast** | 无登录态 → 中止，不 fallback isolated profile |

Soul / Agents 同源约束：[`Soul.md`](Soul.md) · [`Agents.md`](Agents.md)

---

## 🔒 铭刻：工作脚本，不是回归测试

```
npm run run:boss-recommend   ← 执行一次工作流，产物写入 BOSS_HIRE_WORKDIR
npm run run:boss-login       ← 探查登录态，输出 STOP/OK 报告
npm run run:boss-idle        ← 打开页面驻留，日志落盘
```

| 原则 | 说明 |
|------|------|
| **Playwright = 执行引擎** | `.spec.ts` 仅为文件名约定，语义是**工作脚本** |
| **成功 = 有产物** | 截图 / extracts / reports / logs，不是 runner 全绿 |
| **STOP 是有效输出** | 登录缺失等 → 写 STOP 报告，不是"测试失败要修代码" |
| **禁止回归思维** | 无 snapshot 基线对比、无 CI 门禁、无 retries 自愈 |

---

## 快速导航

| 文档 | 路径 | 说明 |
|------|------|------|
| **Agent 人格** | [`Soul.md`](Soul.md) | 猎阅 Agent — 只读至上 |
| **Agent 规范** | [`Agents.md`](Agents.md) | 系统提示词、write 禁止清单、Playwright 硬约束 |
| **Flow Coding 总索引** | [`flow_coding/Index.md`](../../Index.md) | 川流编程生态 |
| **HR 知识库** | [`basic/HR/README.md`](../../../basic/HR/README.md) | 岗位标准、行业入门 |
| **Chrome CDP** | [`flow_coding_chrome_cdp`](../../../skills/private_skills/flow_coding_chrome_cdp/SKILL.md) | 已登录 Chrome 附着 |

---

## 场景定位

```
HR 意图（看简历 / 看市场 / 对照 JD）
    ↓
猎阅 Agent（READONLY）
    ↓
Boss 直聘页面浏览 → 截图/摘录 → BOSS_HIRE_WORKDIR
    ↓
HR 人工决策（沟通/收藏/邀约 — 在平台上自行操作）
```

Agent **止步于摘录**；平台上的招聘动作 **永远由 HR 人工完成**。

---

## 工作目录（BOSS_HIRE_WORKDIR）

浏览过程中的**中间文件**与 **reports** 统一写入：

```
/Users/nicole/Downloads/nicole/boss直聘_工作目录/
├── screenshots/     # 页面截图
├── extracts/        # 简历/JD 文本摘录
├── reports/         # 浏览报告
└── tmp/             # 单次会话临时文件
```

```bash
export BOSS_HIRE_WORKDIR="/Users/nicole/Downloads/nicole/boss直聘_工作目录"
```

| 子目录 | 内容 |
|--------|------|
| `screenshots/` | Playwright 截图、页面快照 |
| `extracts/` | 候选人/JD 结构化摘录（.md / .json） |
| `reports/` | 汇总浏览报告、匹配分析 |
| `tmp/` | 单次会话缓存，可清理 |

> 与 SafeClaw 通用 `WORKSPACE_DIR` 分离；Boss 直聘浏览产物**只**写此目录。

---

## 目录结构

```
flow_coding/e2e/readonly_boss_hire/
├── Soul.md              # 猎阅人格
├── Agents.md            # 只读规范 + 工作脚本约定
├── Index.md             # 本文件
├── helpers/             # 共享工具（CDP、日志、只读守卫）
└── *.spec.ts            # 工作脚本（Playwright 执行引擎，非回归测试）
```

### 工作脚本清单

| 脚本 | npm 命令 | 产出 |
|------|----------|------|
| `browse-recommend-structure.spec.ts` | `npm run run:boss-recommend` | 推荐页截图、文本、DOM → `extracts/` `reports/` |
| `check-login-state.spec.ts` | `npm run run:boss-login` | 登录态探查 → `reports/login-check-*`（OK 或 STOP） |
| `idle-open-geek-jobs.spec.ts` | `npm run run:boss-idle` | 打开 URL 驻留 + browser logs → `logs/` |

---

## 启动流程

### 1. Chrome CDP（推荐 — 保留登录态）

```bash
# 确保 CDP 就绪：退出 Chrome → 从日常 profile 同步最新登录态 → CDP 重启
./flow_coding/scripts/start_chrome_cdp.sh --restart
# 或
skills/private_skills/flow_coding_chrome_cdp/scripts/start_chrome_cdp.sh --restart
```

> **登录态同步是默认行为**（`--restart` 会 rsync 日常 Chrome → `Chrome-CDP`）。  
> 仅当 `Chrome-CDP` 里登录态已确认够用、且只想改启动参数时，才用 `--no-sync` 跳过同步。

### 2. 运行工作脚本

```bash
cd flow_coding/e2e
npm run run:boss-recommend   # 结构探查
npm run run:boss-login       # 登录态探查
npm run run:boss-idle        # 打开页面驻留
```

> 用 `npx playwright test ...` 亦可；npm 脚本命名 `run:*` 强调**工作流**而非回归测试。

### 3. connectOverCDP 附着

```typescript
const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
// 必须注册 Agents.md 中的 route 守卫后再 goto zhipin.com
```

---

## READONLY 检查清单

启动 Boss 直聘浏览前，逐项确认：

```
- [ ] 已读 Agents.md 禁止清单
- [ ] Playwright spec 含 // @readonly-boss-hire
- [ ] beforeEach 已注册 mutating 请求拦截（非 GET → abort）
- [ ] spec 中无 click 沟通/发送/发布/收藏 类按钮
- [ ] spec 中无 fill/type 到消息框或表单
- [ ] 输出目录为 BOSS_HIRE_WORKDIR（`/Users/nicole/Downloads/nicole/boss直聘_工作目录/`）
- [ ] retries: 0（write 误触不可重试）
```

---

## Write vs Read 速查

| 用户说 | Agent 做 | 原因 |
|--------|----------|------|
| "打开这个候选人看看" | ✅ goto + 截图 + 摘录 | 只读 |
| "帮我搜 Python 工程师" | ✅ 搜索页浏览（不点沟通） | 只读 |
| "帮我打个招呼" | ❌ 拒绝 | write |
| "收藏这个人" | ❌ 拒绝 | write |
| "发布这个 JD" | ❌ 拒绝 | write |
| "把简历发到微信" | ❌ 拒绝（平台内） | write；本地摘录 ✅ |

---

## Skills 映射

| 步骤 | Skill | Action |
|------|-------|--------|
| 启动浏览器 | `flow_coding_chrome_cdp` | `check_status`, `start_chrome` |
| 截图存档 | `flow_coding_testing` | `run_playwright`（仅 goto/screenshot） |
| 本地报告 | — | 写入 `BOSS_HIRE_WORKDIR/reports/` |

---

## HR 知识库联动

浏览 Boss 直聘时可对照：

| 文件 | 用途 |
|------|------|
| [`basic/HR/00_行业入门.md`](../../../basic/HR/00_行业入门.md) | 机器人/具身智能行业地图 |
| [`basic/HR/01_电气装配与测试工程师.md`](../../../basic/HR/01_电气装配与测试工程师.md) | 岗位 JD 对照 |
| [`basic/HR/02_AI模仿学习高级算法工程师.md`](../../../basic/HR/02_AI模仿学习高级算法工程师.md) | 算法岗筛选项 |
| … | 见 [`basic/HR/README.md`](../../../basic/HR/README.md) 索引 |

摘录格式建议：候选人 ID（若有）、年限、技能关键词、与 JD 匹配点 — **全部存本地**。

---

## 相关链接

- Boss 直聘：https://www.zhipin.com
- Flow Coding 方法论：[`docs/flow_coding.md`](../../../docs/flow_coding.md)
- WORKSPACE 规则：[`Agents.md`](../../../Agents.md)
