---
name: flow_coding_testing
description: 实践 Flow Coding（心流编程）范式，通过5阶段算法实现AI辅助开发与自动化验证的闭环。适用于复杂UI、组件、API或系统重构任务，确保开发效率和代码质量。
---

# Flow Coding Testing Skill

## 核心理念

**Flow Coding = Vibe Coding（生产端自动化） + Dev Automation（验证端自动化）**

在 Vibe Coding（AI 辅助代码生成）基础上，通过浏览器自动化工具将验证环节也完全自动化，使开发者的注意力始终停留在「意图表达」与「判断」层面，持续处于心流状态。

### 🔥 核心驱动力：反馈，反馈，反馈！

**反馈是 AI 能力提升的唯一途径。** Flow Coding 相比 Vibe Coding 的根本区别不在于"多了一个自动化步骤"，而在于**反馈的质量和速度发生了质变**：

| 维度 | Vibe Coding | Flow Coding |
|------|-------------|-------------|
| **反馈来源** | 单元测试断言（间接） | 真实浏览器截图（直接） |
| **反馈内容** | "assertEqual failed: expected 42, got 41" | **一张真实的页面截图** |
| **AI 看到什么** | 抽象的数字和字符串 | 用户真正看到的 UI |
| **反馈速度** | 需要开发者手动打开浏览器验证 | 截图自动回传，秒级 |
| **反馈循环** | 生成 → 等待人工验证 → 修复 | 生成 → 截图 → 对比 → 自动修复 |
| **AI 学习效率** | 低（反馈稀疏且间接） | **高（反馈密集且直接）** |

**关键洞察：**
- Vibe Coding 的反馈是**符号化的**——AI 只知道"某个值不对"，但不知道"页面看起来不对"
- Flow Coding 的反馈是**视觉化的**——AI 看到截图，能理解布局错位、颜色偏差、元素缺失等真实问题
- **AI 看到截图 = AI 获得了和人类开发者一样的视觉反馈**，这是 AI 自主修复能力的基础
- 反馈越直接，AI 的修复越精准；反馈越快，AI 的迭代越高效

---

## 适用场景

- 复杂 UI 页面开发与重构
- 组件库开发与迭代
- API 端点开发与测试
- 系统集成与重构任务
- 任何需要反复验证迭代的开发工作

---

## 5阶段算法（执行流程）

### **PHASE 1: 建立验证基线**

在修改任何代码之前，先找到或创建代表当前功能状态的自动化测试。

**前端**: 如果存在 Playwright E2E 测试，先运行它确认 100% 通过的基线  
**后端**: 如果存在测试端点或集成测试，使用 `curl` 捕获当前响应结构  
**规则**: 此基线是你的"安全护栏"——任何变更都必须收敛回绿色状态

---

### **PHASE 2: 意图表达与代码生成（VIBE）**

表达你的架构设计和变更需求。

**行动**: 对组件、端点或数据模型执行编辑  
**标准**: 始终使变更干净、可编译、可立即运行  
**模式**: 优先最小化上游修复而非下游变通方案。在实施前识别根本原因。

---

### **PHASE 3: 测试规范适配（元自动化）**

当发生主要结构变更时，现有测试中的选择器/断言将失效。你必须作为重构过程的一部分来适配测试。

**前端**: 调整 Playwright 规范中的定位器、点击目标和状态断言  
**后端**: 更新预期的响应结构，添加新的断言字段，或创建验证脚本  
**规则**: 如果功能被故意移除，简化或更新相应断言，而不是让陈旧的测试破坏构建

---

### **PHASE 4: 自愈闭环（自动运行与修复）**

运行测试并将失败反馈回开发引擎。

1. 运行测试套件
2. 捕获任何失败（定位器缺失、时序竞争、异步状态不匹配、错误的响应结构）
3. **分析根本原因**: 精确定位是渲染时序延迟、React 状态更新竞争、数据模型缺口，还是缺失字段
4. **自动纠正**: 直接编辑代码解决问题
5. **重复**: 重新运行并修复直到 100% 的测试通过

---

### **PHASE 5: 最终收敛与确认**

一旦测试套件完全通过（全绿），截取最终的 UI 截图或录制，或捕获最终的 API 响应，并向用户呈现经过验证的完成状态。

---

## 核心原则

### 原则 1: 验证端自动化是 Vibe Coding 的天花板
Vibe Coding 的核心风险是 AI 生成"看起来对但实际错"的代码。**验证越自动化，vibe coding 的安全边界越大。**

### 原则 2: 元自动化 + 自愈闭环
验证结果可以直接回流到 Coding Agent，由 Agent 自主判断并修复问题，无需开发者介入中间轮次。

| 模式 | 人参与环节 | 适用场景 |
|------|------------|----------|
| 人判断模式 | 每轮验证都需要开发者确认 | 低信任层（核心算法/安全路径） |
| 自愈模式 | 仅起点意图 + 终点确认 | 高信任层（CRUD/UI/样板代码） |

### 原则 3: 注意力守恒
开发者的注意力是稀缺资源。每次从"对话窗口"切到"浏览器"再切回来，都有 ~15 秒的上下文切换成本。Flow Coding 的目标是将切换次数降到零。

---

## 技术栈推荐

### 生产端（Vibe Coding）
| 组件 | 推荐工具 |
|------|----------|
| AI 代码生成 | Windsurf Cascade / Cursor / GitHub Copilot |
| 上下文管理 | 项目级 Rules / AGENTS.md |

### 验证端（Dev Automation）
| 组件 | 推荐工具 |
|------|----------|
| 浏览器自动化 | Playwright（Python / Node） |
| 状态直达 | Playwright 脚本 + Mock Token |
| 视觉回归 | `page.screenshot()` + pixelmatch |
| E2E 断言 | Playwright Test Assertions |

---

## 使用方法

当接收到复杂开发任务时，遵循以下决策流程：

1. **识别任务类型**: 是否涉及 UI/组件/API 变更？
2. **确认验证基线存在**: 是否有可运行的 Playwright/E2E 测试？
   - 无 → 先创建基础验证脚本（PHASE 1）
   - 有 → 运行确认基线通过
3. **执行 5 阶段算法**: 从 PHASE 2 开始迭代，直到 PHASE 5 完成
4. **呈现结果**: 向用户展示最终截图/报告 + "已完成"确认

---

## 注意事项

- **分层信任**: 核心算法/安全路径采用"人判断模式"；CRUD/UI/样板代码可采用"自愈模式"
- **测试先行**: 没有验证基线的代码变更是高风险的
- **根因修复**: 在自愈闭环中，始终分析失败的根本原因，而不是表面修复

---

## 实际执行功能

本 Skill 不仅提供 Flow Coding 的理论指南，还集成了实际的自动化测试执行能力。

### Action 类型

| Action | 功能 |
|--------|------|
| `get_guide` | 获取 5 阶段算法指南和核心原则 |
| `check_phase` | 检查指定阶段的完成清单 |
| `run_playwright` | **启动真实浏览器，执行可见测试并截图** |
| `compare_screenshots` | **对比两张截图的差异（像素级）** |
| `run_self_healing_loop` | 获取自愈闭环模式的说明 |
| `report_completion` | 报告任务完成 |

### run_playwright - 真实浏览器测试

```python
# 示例：打开可见浏览器，导航到页面并截图
run(
    action="run_playwright",
    url="http://localhost:3000",
    screenshot_path="/tmp/test_result.png",
    viewport={"width": 1280, "height": 720},
    steps=[
        {"action": "click", "selector": "#login-btn"},
        {"action": "fill", "selector": "#username", "value": "testuser"},
        {"action": "wait", "selector": ".dashboard"}
    ]
)
```

**返回结果：**
- `screenshot_path`: 截图保存路径
- `screenshot_base64`: Base64 编码的截图（供 AI 直接查看）
- `page_title`: 页面标题
- `steps_executed`: 执行步骤的状态
- `page_info`: 页面信息

### compare_screenshots - 截图对比

```python
# 示例：对比当前截图与基线
run(
    action="compare_screenshots",
    baseline_path="/tmp/baseline.png",
    screenshot_path="/tmp/current.png",
    threshold=0.1  # 10% 差异阈值
)
```

**返回结果：**
- `match`: 是否匹配（True/False）
- `diff_percentage`: 差异百分比
- `diff_image_path`: 差异可视化图路径（不匹配时生成）

### 完整自愈闭环示例

```python
# 1. 建立基线（PHASE 1）
baseline = run(
    action="run_playwright",
    url="http://localhost:3000",
    screenshot_path="/tmp/baseline.png"
)

# 2. 修改代码（PHASE 2-3）...

# 3. 运行测试并对比（PHASE 4）
current = run(
    action="run_playwright",
    url="http://localhost:3000",
    screenshot_path="/tmp/current.png"
)

# 4. 对比结果
comparison = run(
    action="compare_screenshots",
    baseline_path="/tmp/baseline.png",
    screenshot_path="/tmp/current.png",
    threshold=0.05
)

# 5. 根据 comparison['match'] 判断是否需要修复
# 如果不匹配，AI Agent 自动分析 diff_image 并修复代码
```

---

## 依赖安装

```bash
# Playwright 浏览器自动化
pip install playwright
playwright install

# 图像对比
pip install Pillow numpy
```
