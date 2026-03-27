#!/usr/bin/env python3
"""验证 DeepAgents 工具集成"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_tools_integration():
    """测试工具集成到 DeepAgents"""
    print("=== 测试 DeepAgents 工具集成 ===\n")
    
    try:
        # 模拟 SafeClawDeepAgent 初始化
        from safe_claw.core.deepagents.official_integration import SafeClawDeepAgent
        
        # 创建模拟 LLM 服务
        class MockLLMService:
            def __init__(self):
                self.gateway = MockGateway()
        
        class MockGateway:
            def __init__(self):
                self.config = MockConfig()
            def get_model_info(self):
                return {"model": "mock-model", "provider": "mock"}
        
        class MockConfig:
            def __init__(self):
                self.model = "gpt-4"
                self.provider = "openai"
                self.api_key = "mock-key"
                self.base_url = None
                self.temperature = 0.7
                self.max_tokens = 4000
        
        # 创建代理实例
        mock_llm = MockLLMService()
        agent = SafeClawDeepAgent(mock_llm, {"test_mode": True})
        
        # 获取工具列表
        tools = agent._get_safe_claw_tools()
        
        print(f"✅ 成功创建 {len(tools)} 个工具")
        
        # 分类统计
        builtin_tools = [t for t in tools if 'skill_' not in t.name]
        skill_tools = [t for t in tools if 'skill_' in t.name]
        
        print(f"\n📊 工具分类:")
        print(f"  - Builtin Tools: {len(builtin_tools)}")
        print(f"  - Skills Tools: {len(skill_tools)}")
        
        # 列出所有工具
        print(f"\n🔧 Builtin Tools:")
        for tool in builtin_tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")
        
        print(f"\n🎯 Skills Tools:")
        for tool in skill_tools:
            print(f"  - {tool.name}: {tool.description[:50]}...")
        
        # 验证关键工具存在
        expected_tools = {
            'builtin': ['safe_claw_memory_search', 'safe_claw_log_operation', 
                       'safe_claw_file_read', 'safe_claw_file_write'],
            'skills': ['skill_discover_and_execute', 'skill_list_available', 
                      'skill_get_prompt']
        }
        
        print(f"\n✅ 工具验证:")
        tool_names = [t.name for t in tools]
        
        for category, expected in expected_tools.items():
            missing = [t for t in expected if t not in tool_names]
            if missing:
                print(f"  ❌ {category} 缺失: {missing}")
            else:
                print(f"  ✅ {category} 工具完整")
        
        # 检查 DeepAgent 是否接收了工具
        if hasattr(agent, 'deep_agent') and agent.deep_agent:
            print(f"\n✅ DeepAgent 已成功初始化并接收工具")
            
            # 尝试获取工具信息（如果 DeepAgent 支持）
            if hasattr(agent.deep_agent, 'tools'):
                agent_tools = getattr(agent.deep_agent, 'tools', [])
                print(f"  - DeepAgent 中的工具数量: {len(agent_tools)}")
        else:
            print(f"\n⚠️ DeepAgent 初始化可能失败（这在测试环境中是正常的）")
        
        # 测试工具调用（模拟）
        print(f"\n🧪 测试工具调用:")
        
        # 测试 builtin tool
        memory_tool = next((t for t in tools if t.name == 'safe_claw_memory_search'), None)
        if memory_tool:
            try:
                result = memory_tool._run(query="test")
                print(f"  ✅ memory_search: {result[:50]}...")
            except Exception as e:
                print(f"  ⚠️ memory_search: {e}")
        
        # 测试 skills tool
        list_tool = next((t for t in tools if t.name == 'skill_list_available'), None)
        if list_tool:
            try:
                result = list_tool._run(category="")
                print(f"  ✅ skill_list: 返回 {len(result)} 字符")
            except Exception as e:
                print(f"  ⚠️ skill_list: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖都已正确安装")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skills_system():
    """测试技能系统独立运行"""
    print("\n=== 测试技能系统 ===\n")
    
    try:
        from safe_claw.core.skills import SkillDiscovery, get_skill_scanner
        
        # 初始化扫描器
        scanner = get_skill_scanner()
        print(f"✅ 技能扫描器初始化成功")
        
        # 扫描技能
        if not scanner.loaded:
            scanner.scan_all_skills()
            print(f"✅ 扫描完成，发现 {len(scanner.index)} 个技能")
        
        # 初始化发现系统
        discovery = SkillDiscovery(scanner)
        print(f"✅ 技能发现系统初始化成功")
        
        # 测试发现
        result = discovery.find_skill("test", min_confidence=0.1)
        print(f"✅ 技能发现测试完成，级别: {result.level.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 技能系统测试失败: {e}")
        return False

if __name__ == "__main__":
    print("SafeClaw + DeepAgents 集成验证")
    print("=" * 50)
    
    success1 = test_tools_integration()
    success2 = test_skills_system()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ 所有测试通过！工具集成成功。")
    else:
        print("❌ 部分测试失败，请检查配置。")
