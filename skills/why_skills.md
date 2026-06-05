# 为什么使用 Skills 系统？

## 核心理念

SafeClaw 采用 **Skills（技能）** 架构，让 LLM 通过工具调用扩展能力。这与传统的"提示词工程"方式有本质区别。

## 传统方式 vs Skills 方式

### 传统方式：提示词包含所有逻辑
```
[系统提示词 2000 tokens]
你是一个股票分析助手。分析步骤：
1. 获取股票代码
2. 调用 yfinance 下载数据
3. 计算收益率...
4. 生成图表...

用户问：分析 WCM 持仓
→ LLM 需要在上下文中维护所有逻辑
→ 每次都要重复解释如何分析
→ 容易出错、难以维护
```

### Skills 方式：声明式工具调用
```
用户问：分析 WCM 持仓
→ LLM 识别需要 stock_13f_analyze 技能
→ 生成: TOOL_CALL: stock_13f_analyze{"fund": "wcm", ...}
→ 系统执行预定义代码
→ LLM 获得结构化结果并回复
```

## Skills 的优势

| 维度 | 优势 |
|------|------|
| **可维护性** | 分析逻辑写在代码里，版本可控，测试可覆盖 |
| **可靠性** | 参数有 JSON Schema 校验，减少幻觉 |
| **安全性** | 敏感操作走 SafetyController，可审计 |
| **可复用** | 一个 skill 可被多个 Agent/会话复用 |
| **可扩展** | 新增能力只需添加 skill，不改核心架构 |
| **透明性** | 工具调用可见，执行过程可追踪 |

## Skills 的组成

```
Skill = 定义 (SKILL.md) + 实现 (main.py)

SKILL.md        # 声明式描述
  ├── name      # 技能标识
  ├── description  # LLM 看到的用途说明
  └── parameters   # JSON Schema 参数定义

main.py         # 实现代码
  ├── run(**kwargs)  # 执行入口
  └── SKILL_DEFINITION  # 注册信息
```

## 三种作用域

| 目录 | 用途 | 可见性 |
|------|------|--------|
| `private_skills/` | 个人/团队私有技能 | 仅当前工作区 |
| `shared_skills/` | 跨 Agent 共享 | 所有 Agent 可用 |
| `public_skills/` | 社区生态 | 可发布到技能市场 |

## 执行流程

```
用户输入
    ↓
[AgentNode] LLM 理解意图
    ↓
检测到工具调用 → 生成 TOOL_CALL: name{args}
    ↓
[SkillNode] SkillRegistry 查找并执行
    ↓
[SafetyController] 安全检查
    ↓
执行 main.py::run() → 返回结构化结果
    ↓
[AgentNode] LLM 整合结果生成回复
    ↓
用户看到答案
```

## 示例：13F 分析 Skill

```python
# main.py
def run(fund: str, start_date: str, end_date: str) -> dict:
    portfolio = load_fund(fund)
    returns = calculate_returns(portfolio, start_date, end_date)
    return {
        "success": True,
        "fund": fund,
        "performance": returns,
        "summary": generate_summary(returns)
    }

SKILL_DEFINITION = {
    "name": "stock_13f_analyze",
    "description": "分析 13F 机构持仓表现...",
    "parameters": {...}
}
```

LLM 看到：
> "有个技能叫 stock_13f_analyze，可以分析基金持仓。用户问 WCM 表现 → 我应该调用它。"

## 总结

Skills 系统让 SafeClaw 成为 **"可编程的 AI 助手"**：
- LLM 负责 **理解意图** 和 **生成回复**
- Skills 负责 **执行任务** 和 **返回数据**
- 两者通过标准化接口协作

这比让 LLM "凭空想象" 如何执行任务更可靠、更可控。
