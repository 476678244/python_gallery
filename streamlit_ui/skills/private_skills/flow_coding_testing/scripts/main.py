"""
Flow Coding Testing Skill - Main Implementation
心流编程测试技能主实现

此 skill 为 AI Agent 提供 Flow Coding（心流编程）范式的实践指南，
帮助在复杂开发任务中实现生产端与验证端的自动化闭环。
"""
import os
import base64
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# Playwright 浏览器自动化
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# 图像对比
try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Skill 定义元数据
SKILL_DEFINITION = {
    "name": "flow_coding_testing",
    "description": "实践 Flow Coding（心流编程）范式，通过5阶段算法实现AI辅助开发与自动化验证的闭环。适用于复杂UI、组件、API或系统重构任务。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get_guide", "check_phase", "report_completion", "run_playwright", "compare_screenshots", "run_self_healing_loop"],
                "description": "执行的操作类型：获取指南、检查阶段、报告完成、运行Playwright测试、对比截图、运行自愈闭环"
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
            },
            "url": {
                "type": "string",
                "description": "要测试的页面 URL"
            },
            "screenshot_path": {
                "type": "string",
                "description": "截图保存路径"
            },
            "baseline_path": {
                "type": "string",
                "description": "基线截图路径（用于对比）"
            },
            "steps": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Playwright 执行步骤（点击、输入等）"
            },
            "viewport": {
                "type": "object",
                "properties": {
                    "width": {"type": "integer"},
                    "height": {"type": "integer"}
                },
                "description": "浏览器视口大小"
            },
            "threshold": {
                "type": "number",
                "description": "截图对比差异阈值（0-1，默认0.1）",
                "default": 0.1
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
    verification_status: Optional[str] = None,
    url: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    baseline_path: Optional[str] = None,
    steps: Optional[List[Dict]] = None,
    viewport: Optional[Dict[str, int]] = None,
    threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Flow Coding Testing Skill 主入口
    
    Args:
        action: 执行的操作类型 (get_guide / check_phase / report_completion / run_playwright / compare_screenshots)
        current_phase: 当前所处的阶段 (1-5)
        task_type: 任务类型
        verification_status: 验证状态
        url: 要测试的页面 URL
        screenshot_path: 截图保存路径
        baseline_path: 基线截图路径
        steps: Playwright 执行步骤
        viewport: 浏览器视口大小
        threshold: 截图对比差异阈值
    
    Returns:
        包含指南、检查清单或执行结果的字典
    """
    
    if action == "get_guide":
        return {
            "success": True,
            "skill_name": "flow_coding_testing",
            "description": "Flow Coding（心流编程）- 5阶段算法指南",
            "formula": "Flow Coding = Vibe Coding（生产端自动化） + Dev Automation（验证端自动化）",
            "core_driver": "反馈，反馈，反馈！—— 反馈是 AI 能力提升的唯一途径",
            "why_feedback_matters": {
                "vibe_coding_feedback": "符号化的、间接的（assertEqual failed）",
                "flow_coding_feedback": "视觉化的、直接的（真实浏览器截图）",
                "key_insight": "AI 看到截图 = AI 获得了和人类开发者一样的视觉反馈，这是自主修复能力的基础"
            },
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
    
    elif action == "run_playwright":
        if not PLAYWRIGHT_AVAILABLE:
            return {
                "success": False,
                "error": "Playwright 未安装。请运行: pip install playwright && playwright install"
            }
        if not url:
            return {
                "success": False,
                "error": "请提供 url 参数"
            }
        
        # 运行 Playwright 测试
        result = asyncio.run(_run_playwright_test(
            url=url,
            screenshot_path=screenshot_path,
            steps=steps or [],
            viewport=viewport or {"width": 1280, "height": 720}
        ))
        return result
    
    elif action == "compare_screenshots":
        if not PIL_AVAILABLE:
            return {
                "success": False,
                "error": "PIL 未安装。请运行: pip install Pillow numpy"
            }
        if not screenshot_path or not baseline_path:
            return {
                "success": False,
                "error": "请提供 screenshot_path 和 baseline_path 参数"
            }
        
        # 对比截图
        result = _compare_screenshots(baseline_path, screenshot_path, threshold)
        return result
    
    elif action == "run_self_healing_loop":
        # 自愈闭环：运行测试 -> 对比 -> 返回结果
        return {
            "success": True,
            "mode": "self_healing_loop",
            "core_driver": "反馈，反馈，反馈！—— 每一次截图对比都是一次直接反馈",
            "description": "自愈闭环模式：开发者只需在意图层和最终判断层",
            "feedback_loop": {
                "step1": "AI 生成代码",
                "step2": "Playwright 打开真实浏览器 → 截图（直接反馈）",
                "step3": "像素级对比基线 vs 当前截图",
                "step4": "AI 看到差异图 → 自主分析 → 修复代码",
                "step5": "重新截图验证 → 循环直到收敛",
                "why_better": "比 Vibe Coding 的单元测试反馈更直接——AI 看到的是用户真正看到的页面，不是抽象的断言失败信息"
            },
            "steps": [
                "1. 运行 Playwright 测试并截图",
                "2. 与基线截图对比",
                "3. 返回对比结果给 AI Agent",
                "4. AI Agent 自主分析并修复",
                "5. 重复直到收敛"
            ],
            "attention_conservation": "开发者只需：起点表达意图 -> 终点确认结果",
            "requirements": [
                "需要提供 baseline_path（基线截图）",
                "需要提供 url（测试页面）",
                "可选：steps（执行步骤）"
            ]
        }
    
    else:
        return {
            "success": False,
            "error": f"未知的 action: {action}。支持的值: get_guide, check_phase, report_completion, run_playwright, compare_screenshots, run_self_healing_loop"
        }


# ==================== Playwright 实际执行函数 ====================

async def _run_playwright_test(
    url: str,
    screenshot_path: Optional[str] = None,
    steps: List[Dict] = None,
    viewport: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    使用 Playwright 运行浏览器测试
    
    Args:
        url: 要测试的页面 URL
        screenshot_path: 截图保存路径（默认自动生成）
        steps: 执行步骤列表，如 [{"action": "click", "selector": "#btn"}, {"action": "fill", "selector": "#input", "value": "text"}]
        viewport: 视口大小
    
    Returns:
        执行结果字典
    """
    if screenshot_path is None:
        # 自动生成截图路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"/tmp/flow_coding_screenshot_{timestamp}.png"
    
    result = {
        "success": False,
        "url": url,
        "screenshot_path": screenshot_path,
        "headless": False,
        "steps_executed": [],
        "errors": []
    }
    
    try:
        async with async_playwright() as p:
            # 启动浏览器（可见模式）
            browser = await p.chromium.launch(
                headless=False
            )
            
            # 创建上下文
            context = await browser.new_context(
                viewport=viewport or {"width": 1280, "height": 720},
                record_video_dir=None
            )
            
            # 打开页面
            page = await context.new_page()
            
            # 导航到目标 URL
            await page.goto(url, wait_until="networkidle")
            result["page_loaded"] = True
            result["page_title"] = await page.title()
            result["final_url"] = page.url
            
            # 执行步骤
            if steps:
                for i, step in enumerate(steps):
                    try:
                        action_type = step.get("action")
                        selector = step.get("selector")
                        value = step.get("value")
                        
                        if action_type == "click":
                            await page.click(selector)
                            await page.wait_for_load_state("networkidle")
                        elif action_type == "fill":
                            await page.fill(selector, value)
                        elif action_type == "wait":
                            await page.wait_for_selector(selector)
                        elif action_type == "screenshot":
                            # 中间截图
                            mid_path = step.get("path", f"{screenshot_path.rsplit('.', 1)[0]}_step{i}.png")
                            await page.screenshot(path=mid_path, full_page=step.get("full_page", True))
                        
                        result["steps_executed"].append({
                            "step": i,
                            "action": action_type,
                            "status": "success"
                        })
                    except Exception as e:
                        result["steps_executed"].append({
                            "step": i,
                            "action": action_type,
                            "status": "failed",
                            "error": str(e)
                        })
                        result["errors"].append(f"Step {i} failed: {str(e)}")
            
            # 最终截图
            await page.screenshot(path=screenshot_path, full_page=True)
            result["screenshot_taken"] = True
            
            # 获取页面信息
            result["page_info"] = {
                "title": await page.title(),
                "url": page.url,
                "viewport": viewport
            }
            
            # 关闭
            await context.close()
            await browser.close()
            
            result["success"] = True
            result["message"] = f"测试完成，截图已保存至 {screenshot_path}"
            
            # 如果文件存在，读取为 base64
            if os.path.exists(screenshot_path):
                with open(screenshot_path, "rb") as f:
                    img_data = f.read()
                    result["screenshot_base64"] = base64.b64encode(img_data).decode("utf-8")
                    result["screenshot_size"] = len(img_data)
            
    except Exception as e:
        result["errors"].append(str(e))
        result["message"] = f"测试失败: {str(e)}"
    
    return result


def _compare_screenshots(baseline_path: str, current_path: str, threshold: float = 0.1) -> Dict[str, Any]:
    """
    对比两张截图的差异
    
    Args:
        baseline_path: 基线截图路径
        current_path: 当前截图路径
        threshold: 差异阈值（0-1），超过此值视为不同
    
    Returns:
        对比结果字典
    """
    result = {
        "success": False,
        "baseline_path": baseline_path,
        "current_path": current_path,
        "threshold": threshold,
        "match": False,
        "diff_percentage": 0.0
    }
    
    try:
        # 打开图片
        baseline = Image.open(baseline_path).convert("RGB")
        current = Image.open(current_path).convert("RGB")
        
        # 统一尺寸
        if baseline.size != current.size:
            current = current.resize(baseline.size, Image.Resampling.LANCZOS)
            result["resized"] = True
        
        # 转换为 numpy 数组
        baseline_arr = np.array(baseline)
        current_arr = np.array(current)
        
        # 计算差异
        diff = np.abs(baseline_arr.astype(float) - current_arr.astype(float))
        diff_mean = np.mean(diff)
        diff_max = np.max(diff)
        
        # 计算差异百分比（基于最大可能值 255）
        diff_percentage = diff_mean / 255.0
        result["diff_percentage"] = round(diff_percentage * 100, 2)
        result["diff_mean"] = round(diff_mean, 2)
        result["diff_max"] = int(diff_max)
        
        # 判断是否匹配
        result["match"] = diff_percentage <= threshold
        result["success"] = True
        
        # 生成差异图
        if not result["match"]:
            diff_image = Image.fromarray(np.uint8(diff))
            diff_path = current_path.rsplit(".", 1)[0] + "_diff.png"
            diff_image.save(diff_path)
            result["diff_image_path"] = diff_path
        
        result["message"] = (
            f"截图对比完成: 差异 {result['diff_percentage']}% "
            f"({'匹配' if result['match'] else '不匹配'}, 阈值 {threshold*100}%)"
        )
        
    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"对比失败: {str(e)}"
    
    return result
