# SafeClaw 🦞 × Flow Coding（川流编程）

> **SafeClaw (TRASA — The Real AI Safety Assistant)** — 安全优先、文件优先、隐私可控的本地 AI 助手。
> 采用 **Flow Coding（川流编程）** 方法论开发：在 Vibe Coding 的基础上，用 Playwright 把验证环节也完全自动化，闭合开发内循环的最后一公里。

---

## 目录

- [一、SafeClaw 是什么](#一safeclaw-是什么)
- [二、Flow Coding（川流编程）是什么](#二flow-coding川流编程是什么)
- [三、技术架构](#三技术架构)
- [四、快速开始](#四快速开始)
- [五、川流编程工作流](#五川流编程工作流)
- [六、项目结构](#六项目结构)
- [七、文档索引](#七文档索引)

---

## 一、SafeClaw 是什么

SafeClaw（安全之爪）是一个 **安全优先**、**文件优先** 的本地 AI 助手，基于 **LangGraph Deep Agents** + **4 层记忆系统** + **安全策略** 构建。

| 特性 | 说明 |
|------|------|
| **🛡️ 安全优先** | 三级安全策略（黑名单/确认级/白名单），敏感操作确认，完整审计日志 |
| **🧠 4 层记忆系统** | Active / Dormant / Deep / Forgotten 智能分层与自动管理 |
| **🤖 多 Agent 架构** | Chat / Memory / Router / Safety Agent 协作 |
| **🔧 技能系统** | 文件操作、代码分析、可扩展技能框架（Skill Tree） |
| **🔒 本地优先** | 数据不出境，配置可编辑，完全透明 |

前端为 **Next.js（`safeclaw-ui/my-app`）**，后端 API 入口为 `api/main.py`，核心逻辑在 `safe_claw/`。

---

## 二、Flow Coding（川流编程）是什么

**Flow Coding（川流编程）** 是本项目采用的开发范式：

```
Flow Coding = Vibe Coding（生产端自动化） + Dev Automation（验证端自动化）
```

- **Vibe Coding** 自动化了「写代码」，但验证仍是手动的——打开浏览器、导航、填数据、肉眼比对。
- **Flow Coding** 用 **Playwright** 把验证端也自动化：AI 生成代码 → 自动导航/填表/截图/断言 → 读取结果 → 自主修复 → 收敛。

开发者的注意力始终停留在「意图表达」与「最终判断」层，不被中间操作打断。

### 命名释义：为什么是「川流」

- **过程之川**：「意图 → 生成 → 验证 → 修复」如河川般连续不断，*川流不息*。
- **双源汇流**：生产端与验证端两股自动化支流汇入同一主干，形成端到端闭合水系。
- **心流 vs 川流**：心流（Flow State）是开发者的心理状态（结果），川流是达成该状态的工作流形态（手段）。

> 完整方法论见 **[`docs/flow_coding.md`](docs/flow_coding.md)**。

---

## 三、技术架构

### 生产端（SafeClaw 本体）
- **Python 3.11** + **LangGraph**（Deep Agents 状态图）+ **LangChain**
- **FastAPI**（`api/main.py`，端口 `8000`）
- **Next.js** 前端（`safeclaw-ui/my-app`，端口 `3000`）

### 验证端（川流编程脚手架）
- **Playwright（TS only）**：所有 E2E 验证写在 `test/e2e/*.spec.ts`，**不写任何 Python 测试脚本**
- **统一分辨率 1920×1080**，截图基线可复现
- 配置见 [`test/e2e/playwright.config.ts`](test/e2e/playwright.config.ts) 与 [`test/e2e/package.json`](test/e2e/package.json)

---

## 四、快速开始

### 1. 环境

```bash
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate safe_claw   # Python 3.11
pip install -r requirements.txt
```

### 2. 启动后端 API（端口 8000）

```bash
python start_api.py
```

### 3. 启动前端（端口 3000）

```bash
cd safeclaw-ui/my-app
npm install
npm run dev
```

### 4. 运行川流编程验证（Playwright）

```bash
cd test/e2e
npm install
npx playwright install chromium
npx playwright test                 # 全部 spec
npx playwright test <spec>.spec.ts  # 单个 spec
```

> ⚠️ 临时文件、Agent 输出统一写入 `~/Downloads/safe_claw_worksapce/workspace/`，详见 [`Agents.md`](Agents.md)。

---

## 五、川流编程工作流

开发任何 UI / 组件 / API / 重构任务，遵循 5 阶段闭环（详见 [`docs/flow_coding.md`](docs/flow_coding.md)）：

1. **建立验证基线**：跑现有 Playwright spec，确认 100% 绿。
2. **意图表达与代码生成（Vibe）**：实现改动，最小上游修复优于下游绕过。
3. **测试规约适配（元自动化）**：结构变化时同步更新 spec 的 locator/断言。
4. **自愈闭环（自动跑 + 修）**：
   - 验证的是 **端到端产品功能完整性**，**前后端均可修改**——先定位根因（前端/后端/数据层/接口契约），再在正确位置修复。
   - 遵循 **3 × 3 原则**：单方向最多迭代 3 次；3 次未解决则切换方向，最多切 3 次；触顶（最多 9 次）仍未收敛则停止并回报开发者。**禁止无限迭代。**
5. **最终收敛确认**：全绿后截图/录屏，呈交开发者判断。

---

## 六、项目结构

```
python_gallery/
├── api/                  # FastAPI 入口 (main.py, 端口 8000)
├── safe_claw/            # 核心：agents / graph / memory / skills / safety
│   ├── core/
│   ├── models/
│   ├── services/         # llm_gateway 等
│   └── utils/
├── safeclaw-ui/my-app/   # Next.js 前端 (端口 3000)
├── test/
│   ├── e2e/              # Playwright TS 验证工程（独立 package.json）
│   ├── unit/ integration/
├── skills/               # 私有技能
├── linked_skills/        # 外链技能集合
├── docs/
│   └── flow_coding.md    # 川流编程方法论
├── Agents.md             # 工作目录与开发规范
├── Soul.md               # 项目灵魂：SafeClaw
└── requirements.txt
```

---

## 七、文档索引

| 文档 | 说明 |
|------|------|
| **[docs/flow_coding.md](docs/flow_coding.md)** | 川流编程方法论（含可复用 Playwright 模板、3×3 自愈原则） |
| **[safe_claw/README.md](safe_claw/README.md)** | SafeClaw 核心：记忆系统 / 安全策略 / 技能系统 |
| **[safeclaw-ui/README.md](safeclaw-ui/README.md)** | 前端架构 |
| **[test/README.md](test/README.md)** | 测试策略与运行 |
| **[Agents.md](Agents.md)** | 工作目录规则、Fail Fast 实践、调试配置 |

---

**SafeClaw TRASA** · 以 **川流编程** 持续闭合「意图 → 生成 → 验证 → 修复」的开发内循环。
