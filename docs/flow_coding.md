# Flow Coding（川流编程）

> 在 Vibe Coding 的基础上，闭合开发内循环的最后一公里。

Vibe Coding 让 AI 替你写代码。Flow Coding 让 AI 替你写代码，然后自动帮你打开浏览器、导航到正确页面、填入测试数据、截图比对——你只需要看结果，说"对"或"不对"。

你的注意力从未离开过意图层。这就是心流。

---

## 目录

- [一、问题：Vibe Coding 的"最后一公里"](#一问题vibe-coding-的最后一公里)
- [二、定义：什么是 Flow Coding](#二定义什么是-flow-coding)
- [三、范式演进：三个阶段的开发内循环](#三范式演进三个阶段的开发内循环)
- [四、核心原则](#四核心原则)
- [五、技术栈](#五技术栈)
- [六、实战示例](#六实战示例)
- [七、适用边界](#七适用边界)
- [八、FAQ](#八faq)
- [九、相关概念](#九相关概念)

---

## 一、问题：Vibe Coding 的"最后一公里"

[Vibe Coding](https://karpathy.ai) （Andrej Karpathy, 2025）改变了代码生产方式：

```
传统：  思考 → 手写代码 → 运行 → 调试 → 重复
Vibe：  描述意图 → AI 生成代码 → 运行 → 调试 → 重复
```

代码生产速度提升了 5-10 倍。但一个新的瓶颈浮现了：**验证环节仍然是手动的。**

每次 AI 生成代码后，你仍然需要：

1. 打开浏览器
2. 登录测试账号
3. 点击菜单导航到目标页面
4. 填入测试数据
5. 肉眼比对 UI 是否符合预期
6. 切回对话窗口，告诉 AI 哪里不对

这 6 步每天重复几十次。代码生产只要 3 秒，验证却要 30 秒。

**心流在验证环节被打断。Flow Coding 解决的就是这个问题。**

---

## 二、定义：什么是 Flow Coding

**Flow Coding（川流编程）** 是一种软件开发范式：在 Vibe Coding（AI 辅助代码生成）的基础上，通过浏览器自动化工具（如 Playwright）将验证环节也完全自动化，使开发者的注意力始终停留在「意图表达」与「判断」层面，不被任何中间操作打断，从而持续处于 Mihaly Csikszentmihalyi 所定义的心流状态（Flow State）。

### 命名释义：为什么是「川流」

「川流」比「心流」更贴合本范式的理念。它有两层含义：

1. **过程之川**：开发不再是「写代码 → 停下来手动验证 → 再写」的断点式跳跃，而是「意图 → 生成 → 验证 → 修复」如河川般连续不断、奔流向前的过程——*川流不息*。
2. **双源汇流**：生产端（Vibe Coding）与验证端（Dev Automation）两股自动化支流汇入同一条主干，形成端到端的闭合水系；正如《论语》「逝者如斯夫，不舍昼夜」，开发内循环持续流动、永不停滞。

「心流（Flow State）」描述的是开发者的*心理状态*（结果），「川流」描述的是达成这一状态的*工作流形态*（手段）——以连续不断的自动化川流，承载并保持开发者的心流。

### 公式

```
Flow Coding = Vibe Coding（生产端自动化） + Dev Automation（验证端自动化）
```

### 核心区别：反馈机制

| 范式 | 反馈机制 | 验证范围 | 反馈速度 | 心流保持 |
|------|----------|----------|----------|----------|
| Vibe Coding | Unit Test | 单元级（函数/类） | 快（ms 级） | 部分保持（仍需手动 E2E 验证） |
| Flow Coding | E2E Test | 端到端（完整用户流程） | 中（s 级） | 完全保持（验证全自动化） |

Vibe Coding 基于单元测试反馈：AI 生成代码 → 运行单元测试 → 根据断言失败调整 → 重复。反馈快速但范围有限，无法验证跨组件集成和真实用户场景。

Flow Coding 基于端到端测试反馈：AI 生成代码 → Playwright 自动导航到目标页面 → 填入真实数据 → 截图/断言比对 → 根据结果调整 → 重复。反馈稍慢但覆盖完整用户路径，验证的是"用户真正看到和体验到的"。

### 开发者只需要做三件事

| 步骤 | 你做什么 | 系统做什么 |
|------|----------|------------|
| 1. 表达意图 | 用自然语言描述需求 | AI 生成代码 |
| 2. 触发验证 | 说"跑一下" | Playwright 自动导航、填表、截图、比对 |
| 3. 判断 | 看截图/报告，说"对"或"这里不对" | 记录结果，等待下一轮意图图 |

你从未离开对话窗口。你的手从未碰过鼠标去点测浏览器。

---

## 三、范式演进：三个阶段的开发内循环

**阶段一：传统开发 — 全链手动**

```
[手写代码] → [手动导航浏览器] → [肉眼验证] → [改代码]
      慢                慢               慢              慢
——注意力反复中断，每天有效编码 < 4h——
```

**阶段二：Vibe Coding — 只自动化了生产端**

```
[意图 → AI 生成代码] → [手动导航浏览器] → [肉眼验证] → [改 prompt]
       快                    仍然慢            新瓶颈        慢
——心流在此处被打断——
```

**阶段三：Flow Coding — 生产 + 验证双端闭合**

```
[意图 → AI 生成代码] → [Playwright 一键直达] → [自动截图/比对] → [改 prompt]
       快                      快                      快               快
——心流不中断，全天保持 Flow State——
```

---

## 四、核心原则

### 原则 1：验证端自动化是 Vibe Coding 的天花板

Vibe Coding 的核心风险是 AI 生成"看起来对但实际错"的代码。团队敢在多大范围内使用 vibe coding，取决于验证能力有多强。

**验证越自动化，vibe coding 的安全边界越大。**

### 原则 2：元自动化（Meta-Automation）

在 Flow Coding 范式下，Playwright 脚本本身也可以被 vibe coded：

```
开发者："帮我写一个 Playwright 脚本：登录测试账号、进入库存页面、填入三条测试数据"
AI：    → 生成 Playwright 脚本
开发者："跑一下"
系统：  → Playwright 执行该脚本 → 返回截图
```

这是用 AI 生成自动化脚本来自动化 AI 生成代码的验证过程——递归式提效。

### 自愈闭环：验证结果直接回流 Coding Agent

上例中"返回截图"的终点是开发者——开发者看截图、判断对不对、再告诉 AI。但元自动化的真正力量在于：验证结果不需要经过开发者，可以**直接回流到 Coding Agent，由 Agent 自主判断并修复问题**。

**传统 Vibe Coding 循环（人在环路中判断）：**

```
开发者 —(意图)→ AI 生成代码 —(执行)→ 验证结果 —(截图)→ 开发者 —(判断)→ AI 修复
                                                          ↑
                                              ——注意力必须介入——
```

**Flow Coding 自愈闭环（人只在起点和终点）：**

```
开发者 —(意图)→ AI 生成代码 —(执行)→ 验证结果 —(截图/报错)→ AI 自主分析
                                                                    ↓
                                                          问题定位 → 代码修复 → 重新验证
                                                                    ↓
                                                              通过？
                                                            否 ↙    ↘ 是
                                                    继续修复循环    → 开发者 —(看最终结果)→ "OK"
           ↑
——开发者注意力只在意图层和最终判断层——
```

这意味着 Flow Coding 有两个运行模式：

| 模式 | 人参与环节 | 适用场景 | 循环速度 |
|------|------------|----------|----------|
| 人判断模式 | 每轮验证都需要开发者确认 | 低信任层（核心算法/安全路径） | 受限于人的响应速度 |
| 自愈模式 | 仅起点意图 + 终点确认 | 高信任层（CRUD/UI/样板代码） | 仅受限于 Agent 推理速度 |

在自愈模式中，Coding Agent 拿到 Playwright 截图后可以：

1. 视觉比对：与设计稿或上一轮截图做像素 diff，定位渲染偏差
2. 报错解析：读取 console error / network error / assertion failure，定位根因
3. 自主修复：根据 diff + 报错修改代码，重新触发验证
4. 收敛判定：当截图与基线一致、断言全部通过时，向开发者报告"已完成"

开发者从"每轮都要'变成'只看最后一轮"——注意力守恒从"减少切换"升级为"消除中间轮次的注意力消耗"。

#### 自愈的范围：端到端，而非只改前端

自我修复**不限于修改前端代码**。Flow Coding 验证的是**端到端的产品功能完整性**，因此碰到问题时必须：

1. **先定位问题来源**：根据 console error / network error / 断言失败 / API 响应，判断根因在前端、后端、数据层还是接口契约。
2. **在正确的位置修改**：前端、后端代码均可修改，遵循"最小上游修复优于下游绕过"，对症修复根因而非掩盖症状。

#### 自愈的边界：3 × 3 原则（防止无限迭代）

自愈循环**禁止无限制迭代**。采用 3 × 3 收敛策略：

- **单方向最多 3 次**：沿同一修复方向（同一根因假设）最多迭代尝试 3 次修正。
- **方向最多切换 3 次**：若一个方向 3 次仍未解决，判定该假设错误，切换到新方向（新的根因假设）；方向切换最多 3 次。
- **触顶即停、回报开发者**：达到 3 × 3 上限（最多 9 次尝试）仍未收敛时，停止自动循环，汇总各方向的尝试与失败证据，交回开发者判断。

```
方向 A：尝试 1 → 尝试 2 → 尝试 3   (未解决，切换方向)
方向 B：尝试 1 → 尝试 2 → 尝试 3   (未解决，切换方向)
方向 C：尝试 1 → 尝试 2 → 尝试 3   (仍未解决 → 停止，回报开发者)
```

这保证自愈在高信任层高效收敛的同时，不会陷入无意义的"反复试错"消耗。

### 原则 3：注意力守恒

开发者的注意力是稀缺资源。每一次从"对话窗口"切到"浏览器"再切回来，都有 ~15 秒的上下文切换成本（认知心理学中称为 Attention Residue，Sophie Leroy, 2009）。Flow Coding 的目标是将切换次数降到零。

这个原则不只是时间管理格言——它有坚实的神经科学基础。

#### 前额叶皮层：注意力的指挥中心

**前额叶皮层（Prefrontal Cortex, PFC）** 是大脑执行控制系统的核心，负责三项关键功能：

| PFC 功能 | 在开发中的表现 | 多任务切换时的消耗 |
|----------|----------------|-------------------|
| 工作记忆（Dorsolateral PFC） | 保持当前函数的上下文、变量依赖链、调用栈 | 每次切换需清空并重建工作记忆内容 |
| 抑制控制（Right Inferior PFC） | 抑制无关思路，聚焦当前意图 | 切换后需重新抑制上一个任务的残留思维 |
| 任务集重构（Medial PFC / ACC） | 从"写代码"模式切换到"验证 UI"模式 | 需要加载全新的规则集和目标层级 |

PFC 的代谢特性决定了它是最"昂贵"的脑区：它依赖慢速的谷氨酸能信号传递，葡萄糖消耗率是运动皮层的 2-3 倍。这意味着 PFC 的资源是硬性有限的——不是"努力一下就能多分配"，而是存在生理天花板。

#### 多任务切换：功能性前额叶损伤

神经科学中有一个令人警醒的发现：**频繁任务切换对前额叶的影响，类似于轻度前额叶损伤。**

| 前额叶损伤患者的典型症状 | 与频繁多任务切换者的认知表现对比 |
|--------------------------|----------------------------------|
| ✗ 工作记忆容量下降 | ← 切换后需上文，失去"涌流"当进任务 |
| ✗ 抑制无关刺激的能力减弱 | ← Attention Residue：上一个任务的思维"滞留"进当前任务 |
| ✗ 任务启动延迟增加 | ← 每次切换有 200-500ms 的"任务集重构"延迟（Rubinstein et al., 2001） |
| ✗ 错误率上升 | ← 规则混淆：把 A 任务的假设带入 B 任务 |
| ✗ 时间估计失真 | ← 主观感觉"只看一眼"实际花了 45 秒 |

这不是比喻。Rubinstein, Meyer & Evans（2001）的经典实验明，即使是在受控实验室中做简单的分类任务切换，被试的反应时间增加了 200-500ms，错误率也——而这些被试的前额叶完全健康。多任务切换让健康大脑暂时表现出损伤大脑的特征。

对开发者而言，这种"功能性损伤"的后果更严重，因为软件开发对工作记忆和抑制控制的要求远高于实验室分类任务：你需要同时保持 5-10 个变量的依赖关系、一个隐式状态机、以及"用户期望什么行为"的意图——这全部驻留在 PFC 的工作记忆中。每次切换，全部清空。

#### 为什么"只看一眼"不是零成本

开发者常有一种错觉：切到浏览器"只看一眼"只需要 2 秒。但认知科学的数据告诉我们：

**"只看一眼"的真实成本分解**

```
0.0s   按下 Alt+Tab
0.2s   视觉适应浏览器画面
0.3s   PFC 开始加载"验证模式"的任务集
0.3s   Attention Residue 编码上文仍在活跃，占用工作记忆位置
5-30s  处理验证信息（看 UI / 读报错）
0.5s   切回 IDE
0.3s   PFC 重新加载"编码模式"任务集
——10-15s 脑网络上下文重建，脑才在次调用多少变量？变量叫什么？——

总计：30-78 秒的认知开销，其中大部分是无意识的
```

关键洞察：**触发切换动作本身（不超过 0.5 秒），而是 PFC 任务集的卸载与重装——就像重启一个加载了 10GB 数据的服务器，重启只要 30 秒，但重新加载数据要 5 分钟。**

#### Flow Coding 的神经科学论证

```
传统开发（频繁切换）：
PFC 状态：[编码模式] → [加载] → [验证模式] → [加载] → [编码模式] → [加载] → ...
工作记忆：加载 → 清空 → 重建 → 清空 → 重建 → ...
总注意力消耗：高（持续的前额叶损耗）

Flow Coding（零切换）：
PFC 状态：[编码模式] ——持续 → 持续 → ...（只需一次，直到任务完成）
工作记忆：加载一次，持续使用（积累，而非反复清空）
总注意力消耗：低（只有意图层和最终判断层）
```

---

## 五、技术栈

Flow Coding 不依赖特定工具，但以下是当前最成熟的组合：

### 生产端（Vibe Coding）

| 组件 | 推荐工具 | 说明 |
|------|----------|------|
| AI 代码生成 | Windsurf Cascade / Cursor / GitHub Copilot | IDE 内对话式代码生成 |
| 上下文管理 | 项目级 Rules / AGENTS.md | 让 AI 理解项目约定 |
| Prompt 资产 | 团队 Prompt Library（Wiki / Git） | 沉淀高效 prompt 模板 |

### 验证端（Dev Automation）

| 组件 | 推荐工具 | 说明 |
|------|----------|------|
| 浏览器自动化 | Playwright（Python / Node） | 跨浏览器、Auto-wait、多 Context 隔离 |
| 状态直达 | Playwright 脚本 + Mock Token | 一键到达待验证页面状态 |
| 视觉回归 | `page.screenshot()` + pixelmatch | 像素级 UI 比对 |
| E2E 断言 | Playwright Test Assertions | 功能性正确性验证 |
| 组件隔离 | Playwright Component Testing | 无需后端的轻量 UI 验证 |

### 连接层

| 组件 | 实现方式 | 说明 |
|------|----------|------|
| 一键触发 | IDE Task / npm script / Makefile | 开发者在对话窗口说"跑一下"即可触发 |
| 结果回传 | 截图文件 + JSON 报告 | AI 可读取截图和报告，进入下一轮迭代 |

### 可复用模板：Playwright（TS）验证端脚手架

以下为开箱即用的 Playwright TS 模板，约定：**验证端只用 Playwright TS 脚本，不写任何 Python 测试脚本**，统一分辨率 1920×1080。将两个文件放入独立的 `test/e2e/` 目录即可作为一个自包含的验证工程。

**`test/e2e/package.json`**

```json
{
  "name": "<project>-e2e-tests",
  "private": true,
  "description": "E2E tests (Playwright)",
  "scripts": {
    "test": "npx playwright test",
    "test:headed": "npx playwright test --headed",
    "report": "npx playwright show-report"
  },
  "devDependencies": {
    "@playwright/test": "^1.60.0"
  }
}
```

**`test/e2e/playwright.config.ts`**

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 150_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 1, // Phase 4: Self-healing - retry once on failure
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.FRONTEND_URL || "http://localhost:3000",
    trace: "on-first-retry",
    video: "on-first-retry",
    screenshot: "on",
    headless: false, // Show browser window for visual confirmation
    launchOptions: {
      slowMo: 500, // Slow down operations for better visibility
    },
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1920, height: 1080 }, // Flow Coding standard resolution
      },
    },
  ],
});
```

**初始化与运行**

```bash
cd test/e2e
npm install
npx playwright install chromium
npx playwright test               # 运行全部 spec
npx playwright test <spec>.spec.ts  # 运行单个 spec
```

**模板约定**

- **只用 TS**：所有验证逻辑（含 API 断言）都写在 `*.spec.ts` 中，通过 `page.request` 直接调用后端，无需 Python 脚本。
- **固定分辨率**：viewport 统一 1920×1080，保证截图基线在不同机器上可复现。
- **自愈友好**：`retries: 1` + `trace/video/screenshot` 便于 AI 读取失败上下文并自动修复。
- **可视确认**：`headless: false` + `slowMo` 便于人在终点判断。

---

## 六、实战示例：UI Mockup 驱动的自愈闭环

一个完整示例，串联原则 1-4：验证端自动化（原则 1）、元自动化 + 自愈闭环（原则 2）、注意力守恒（原则 3）、分层信任（原则 4）。

场景：SCM 库存告警板页面——从 UI 设计精到代码实现的全自动闭环。

### Step 1：设计 UI Mockup

开发者在对话窗口上传一张 Figma 截图或手绘线框图：

```
开发者：[上传 inventory_alerts_mockup.png]
        "这是库存告警板的设计稿，帮我实现 /inventory/alerts 页面。"
```

开发者只做了一件事：表达意图 + 提供视觉锚点。此后进入自愈闭环，开发者注意力不再介入。

### Step 2：AI 理解 Mockup → 对比现状 → 生成改进计划

```
AI：  → 读取 mockup 截图，解析布局结构：
        - 顶部：SKU 表格（缺货行红色高亮）
        - 底部：导出 CSV 按钮
      → Playwright 截取 /inventory/alerts 页面截图
      → 逐区对比 mockup vs 现状，生成差异清单
```

**差异报告**

```
1. 筛选器：mockup 在表格上方，现状在左侧边栏
2. 缺货高亮：mockup 用 #FF4444 浅红，现状用 #BB0000
3. 导出按钮：mockup 有，现状缺失
4. 表格列顺序：mockup [SKU|库存|安全线|状态]
               现状 [SKU|库存|仓库|状态]
```

→ 输出改进计划（4 项修改，按依赖排序）

### Step 3：AI 生成 E2E Playwright 验证脚本

AI 基于 mockup 生成 Playwright 脚本——这是元自动化（原则 2）：用 AI 写验证脚本来自动化 AI 生成代码的验证。

```
AI：  → 生成 Playwright E2E 脚本 inventory_alerts_e2e.spec.ts：
        - 导航到 /inventory/alerts
        - 注入 mock 数据（3 台库存，20 SKU，5 缺货）
        - 断言筛选器位置（表格上方）
        - 断言缺货行背景色 = #FF4444
        - 断言导出 CSV 按钮存在且可点击
        - 断言表格列顺序
        - 截图保存为验证基准
```

### 实战示例 2：非浏览器 UI 的视觉自愈（以 PPT 生成为例）

Flow Coding 不局限于 Web 开发。在处理文档生成（如 PPTX/PDF）等不可见 UI 任务时，通过“截图自检”依然可以闭合心流。

**场景**：根据视频内容自动化生成 24 节气手绘风 PPT，并确保插画比例饱满。

**流程**：
1. **意图表达**：开发者要求将视频转换为 PPT，要求保持原始 UI 的手绘组件风格。
2. **生产端**：AI 使用 `python-pptx` 绘制几何图形（牛、人、云、树）。
3. **验证端自动化（核心步）**：AI 编写 `pptx_preview_spire.py` 调用组件库，自动将生成的 PPT 每一页渲染为 PNG 图片。
4. **视觉分析**：AI 通过 `read_file` 读取这些图片，利用视觉能力发现“文字溢出”、“组件比例过小”等排版问题。
5. **自愈循环**：
    - **发现**：Slide 1 的“惊蛰”标题离边缘太近，牛的比例太小。
    - **修复**：自动修改代码中的 `scale` 参数和 `top_pad` 偏移量。
    - **再验证**：重新生成 PPT → 重新截图 → 确认比例完美。

**价值**：开发者不需要反复“生成 -> 找到文件夹 -> 打开 PPT -> 翻页肉眼看 -> 关掉 -> 改代码”，注意力始终停留在 IDE 的意图层。

### Step 4：自愈闭环——AI 修改代码 → 执行脚本 → 读取反馈 → 修正 → 循环

```
——自愈闭环启动——

迭代 1：
AI → 修改组件代码（4 项改进并行全部实施）
系统 → 执行 Playwright E2E 脚本
结果 → 2 通过 / 2 失败
  ✗ 筛选器位置偏左（CSS flex 未生效）
  ✗ 缺货颜色 #FF4444 显示为 #FF3333
    （测试颜色空间转换导错误）
AI → 读取 console log + 截图 + 断言失败信息

迭代 2：
AI → 修复 CSS flex 布局 + 调整颜色为 sRGB 安全值
系统 → 重新执行 Playwright E2E 脚本
结果 → 4 通过 / 0 失败
截图 → 与 mockup 像素 diff < 2%（可接受阈值）

✅ 自愈闭环完成，向开发者报告

——自愈闭环结束——

开发者：（看最终截图 + diff 报告）"OK，上线。"
```

### 全流程注意力消耗分析

```
传统开发（手动验证）：
开发者参与环节：写代码 → 打开浏览器 → 导航 → 肉眼比对 → 切回 IDE → 改代码 → 重复
注意力切换次数：~10 次（每个修改点 2 次切换）
总注意力消耗：~10 × 45s = 7.5 分钟

Flow Coding（自愈闭环）：
开发者参与环节：上传 mockup + 说"帮我实现" → 最终报告说"OK"
注意力切换次数：0
总注意力消耗：~30 秒（仅起意图层 + 终点判断）

注意力节省：93%
```

### 原则回溯

| 原则 | 在本示例中的体现 |
|------|-----------------|
| 原则 1：验证端自动化 | Playwright E2E 脚本替代了手动导航 + 肉眼比对 |
| 原则 2：元自动化 + 自愈 | AI 生成验证脚本回流 AI，无需开发者介入中间轮次 |
| 原则 3：注意力守恒 | 开发者只参与起点和终点，中间 2 轮自愈循环零注意力消耗 |
| 原则 4：分层信任 | 库存告警属高信任层（CRUD + UI），允许全自动化；若涉及权限逻辑则通过触发提醒 |

---

## 七、适用边界

（待补充）

---

## 八、FAQ

（待补充）

---

## 九、相关概念

（待补充）

---

## Algorithm / Step-by-Step Process

When assigned a complex UI, component, API, or system refactoring task, follow this 5-phase algorithm:

### PHASE 1: ESTABLISH THE VERIFICATION BASELINE

Before making any edits, find or create the automated test representing the current feature state.

- **Frontend**: If a Playwright E2E spec exists, run it to confirm a 100% passing baseline.
- **Backend**: If a test endpoint or integration test exists, `curl` it to capture the current response shape.
- **Rule**: This baseline is your "safety guardrail" — any change must converge back to green.

### PHASE 2: INTENT EXPRESSION & CODE GENERATION (VIBE)

Express your architectural design and change requirements.

- **Action**: Perform edits on components, endpoints, or data models.
- **Standard**: Always make changes clean, compile-safe, and immediately runnable.
- **Pattern**: Prefer minimal upstream fixes over downstream workarounds. Identify root cause before implementing.

### PHASE 3: TEST SPEC ADAPTATION (META-AUTOMATION)

When major structural shifts occur, the selectors/assertions in existing tests will break. You must adapt the tests as part of the refactoring process.

- **Frontend**: Adjust locators, click targets, and state assertions in Playwright specs.
- **Backend**: Update expected response shapes, add new assertion fields, or create verification scripts.
- **Rule**: If features are intentionally removed, simplify or update corresponding assertions rather than letting stale tests break the build.

### PHASE 4: SELF-HEALING LOOP (AUTOMATED RUN & FIX)

Run the tests and feed failures back into the development engine. The goal is **end-to-end product integrity**, not just frontend correctness.

1. Run the test suite.
2. Capture any failures (locators missing, timing races, async state mismatches, wrong response shapes).
3. **Locate the source first**: Use console error / network error / assertion failure / API response shape to decide whether the root cause lives in the **frontend, backend, data layer, or API contract**. Do not assume it is always a frontend issue.
4. **Fix at the correct location**: Edit frontend **and/or** backend code as needed. Prefer minimal upstream fixes over downstream workarounds; fix the root cause, never mask the symptom.
5. **Bounded iteration — the 3 × 3 rule** (no infinite loops):
   - **Max 3 attempts per direction**: Iterate up to 3 fixes along the same root-cause hypothesis.
   - **Max 3 direction switches**: If 3 attempts fail, the hypothesis is likely wrong — switch to a new direction (new root-cause hypothesis), up to 3 switches.
   - **Stop at the ceiling**: If the 3 × 3 limit (max 9 attempts) is reached without convergence, halt the loop, summarize each direction's attempts and failure evidence, and hand back to the developer.
6. **Repeat**: Re-run and fix within the 3 × 3 budget until 100% of the tests pass.

### PHASE 5: FINAL CONVERGENCE & CONFIRMATION

Once the test suite passes completely (all green), take final screenshots or recordings of the UI, or capture the final API response, and present the verified, completed state to the user.
