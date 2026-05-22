"""
Flow Coding Testing Skill - Main Implementation
心流编程测试技能主实现

此 skill 为 AI Agent 提供 Flow Coding（心流编程）范式的实践指南，
帮助在复杂开发任务中实现生产端与验证端的自动化闭环。
"""
from typing import Dict, Any, List, Optional


# Skill 定义元数据
SKILL_DEFINITION = {
    "name": "flow_coding_testing",
    "description": "实践 Flow Coding（心流编程）范式，通过5阶段算法实现AI辅助开发与自动化验证的闭环。适用于复杂UI、组件、API或系统重构任务。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get_guide", "check_phase", "report_completion"],
                "description": "执行的操作类型：获取指南、检查阶段、报告完成"
            },
            "current_phase": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "当前所处的阶段（1-5）"
            },
            "task_type": {
                "type": "string",
                "enum": ["frontend_ui", "component", "api", "refactoring", "general"],
                "description": "任务类型"
            },
            "verification_status": {
                "type": "string",
                "enum": ["green", "red", "unknown"],
                "description": "验证状态：通过、失败、未知"
            }
        },
        "required": ["action"]
    }
}


# 5阶段算法指南
PHASES_GUIDE = {
    1: {
        "name": "建立验证基线 (ESTABLISH THE VERIFICATION BASELINE)",
        "description": "在修改任何代码之前，先找到或创建代表当前功能状态的自动化测试。",
        "actions": {
            "frontend": "如果存在 Playwright E2E 测试，运行它确认 100% 通过的基线",
            "backend": "如果存在测试端点或集成测试，使用 curl 捕获当前响应结构",
            "rule": "此基线是你的'安全护栏'——任何变更都必须收敛回绿色状态"
        }
    },
    2: {
        "name": "意图表达与代码生成 (INTENT EXPRESSION & CODE GENERATION)",
        "description": "表达你的架构设计和变更需求，执行代码编辑。",
        "actions": {
            "standard": "始终使变更干净、可编译、可立即运行",
            "pattern": "优先最小化上游修复而非下游变通方案。在实施前识别根本原因。"
        }
    },
    3: {
        "name": "测试规范适配 (TEST SPEC ADAPTATION - META-AUTOMATION)",
        "description": "当发生主要结构变更时，适配测试中的选择器/断言。",
        "actions": {
            "frontend": "调整 Playwright 规范中的定位器、点击目标和状态断言",
            "backend": "更新预期的响应结构，添加新的断言字段，或创建验证脚本",
            "rule": "如果功能被故意移除，简化或更新相应断言，而不是让陈旧的测试破坏构建"
        }
    },
    4: {
        "name": "自愈闭环 (SELF-HEALING LOOP)",
        "description": "运行测试并将失败反馈回开发引擎，自动修复直到全绿。",
        "actions": {
            "steps": [
                "1. 运行测试套件",
                "2. 捕获任何失败（定位器缺失、时序竞争、异步状态不匹配）",
                "3. 分析根本原因：精确定位问题来源",
                "4. 自动纠正：直接编辑代码解决问题",
                "5. 重复：重新运行并修复直到 100% 的测试通过"
            ]
        }
    },
    5: {
        "name": "最终收敛与确认 (FINAL CONVERGENCE & CONFIRMATION)",
        "description": "测试完全通过后，向用户呈现经过验证的完成状态。",
        "actions": {
            "frontend": "截取最终的 UI 截图或录制",
            "backend": "捕获最终的 API 响应",
            "output": "向用户呈现经过验证的完成状态"
        }
    }
}


# 核心原则
CORE_PRINCIPLES = [
    {
        "name": "原则 1: 验证端自动化是 Vibe Coding 的天花板",
        "content": "验证越自动化，vibe coding 的安全边界越大。没有自动化验证的 AI 生成代码是危险的。"
    },
    {
        "name": "原则 2: 元自动化 + 自愈闭环",
        "content": "验证结果直接回流到 Coding Agent，由 Agent 自主判断并修复问题。两种模式：人判断模式（每轮确认）vs 自愈模式（仅起点+终点确认）。"
    },
    {
        "name": "原则 3: 注意力守恒",
        "content": "每次从对话窗口切到浏览器再切回，都有 ~15 秒上下文切换成本。Flow Coding 将切换次数降到零。"
    }
]


# 技术栈推荐
TECH_STACK = {
    "production": {
        "ai_code_gen": ["Windsurf Cascade", "Cursor", "GitHub Copilot"],
        "context_mgmt": ["项目级 Rules / AGENTS.md"]
    },
    "verification": {
        "browser_auto": ["Playwright (Python/Node)"],
        "state_access": ["Playwright 脚本 + Mock Token"],
        "visual_regression": ["page.screenshot() + pixelmatch"],
        "e2e_assertions": ["Playwright Test Assertions"]
    }
}


def run(
    action: str,
    current_phase: Optional[int] = None,
    task_type: Optional[str] = None,
    verification_status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Flow Coding Testing Skill 主入口
    
    Args:
        action: 执行的操作类型 (get_guide / check_phase / report_completion)
        current_phase: 当前所处的阶段 (1-5)
        task_type: 任务类型
        verification_status: 验证状态
    
    Returns:
        包含指南、检查清单或完成报告的字典
    """
    
    if action == "get_guide":
        return {
            "success": True,
            "skill_name": "flow_coding_testing",
            "description": "Flow Coding（心流编程）- 5阶段算法指南",
            "formula": "Flow Coding = Vibe Coding（生产端自动化） + Dev Automation（验证端自动化）",
            "phases": PHASES_GUIDE,
            "core_principles": CORE_PRINCIPLES,
            "tech_stack": TECH_STACK,
            "usage": "当接收到复杂开发任务时，按顺序执行 5 个阶段，确保每一阶段完成后再进入下一阶段"
        }
    
    elif action == "check_phase":
        if current_phase is None or current_phase < 1 or current_phase > 5:
            return {
                "success": False,
                "error": "请提供有效的 current_phase (1-5)"
            }
        
        phase_info = PHASES_GUIDE.get(current_phase, {})
        checklist = []
        
        if current_phase == 1:
            checklist = [
                "已找到现有测试（Playwright/E2E/集成测试）或创建新测试",
                "已运行测试确认基线通过（绿色状态）",
                "已记录当前响应/UI状态作为对比基准"
            ]
        elif current_phase == 2:
            checklist = [
                "已明确表达架构设计和变更需求",
                "代码变更干净且可编译",
                "代码可立即运行",
                "已识别根本原因而非表面现象"
            ]
        elif current_phase == 3:
            checklist = [
                "已检查并更新选择器/定位器",
                "已调整断言以匹配新结构",
                "已添加新功能的验证点",
                "已移除或更新失效的测试断言"
            ]
        elif current_phase == 4:
            checklist = [
                "已运行测试套件",
                "已分析失败的根本原因",
                "已自动修复代码问题",
                f"当前验证状态: {verification_status or '待检查'}"
            ]
            if verification_status == "green":
                checklist.append("✅ 测试全部通过，可以进入 PHASE 5")
            elif verification_status == "red":
                checklist.append("❌ 仍有失败，继续修复循环")
        elif current_phase == 5:
            checklist = [
                "测试套件 100% 通过",
                "已截取最终 UI 截图或录制",
                "已捕获最终 API 响应（如适用）",
                "已准备向用户呈现完成状态"
            ]
        
        return {
            "success": True,
            "phase": current_phase,
            "phase_name": phase_info.get("name", ""),
            "description": phase_info.get("description", ""),
            "checklist": checklist,
            "next_action": "进入下一阶段" if verification_status == "green" else "完成当前阶段任务"
        }
    
    elif action == "report_completion":
        return {
            "success": True,
            "status": "completed",
            "message": "Flow Coding 5阶段算法已完成执行",
            "summary": {
                "phases_executed": 5,
                "verification_automated": True,
                "attention_switches": "最小化",
                "output": "经过验证的代码 + 测试基线 + 最终截图/报告"
            }
        }
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}。支持的值: get_guide, check_phase, report_completion"
        }
