# SafeClaw + DeepAgents 集成架构

## 概述

SafeClaw 现在与 DeepAgents 完全集成，提供了两套独立的工具系统：
1. **Builtin Tools** - 内置的核心工具
2. **Skills System** - 动态渐进式技能系统

## 架构设计

### 1. Builtin Tools (内置工具)
始终可用的核心功能，优化了性能和安全性：

```python
safe_claw_memory_search(query)     # 搜索内存和上下文
safe_claw_log_operation(op, details)  # 审计日志
safe_claw_file_read(path)          # 安全读取文件（限制2000字符）
safe_claw_file_write(path, content) # 安全写入文件（自动创建目录）
```

### 2. Skills System (技能系统)
基于文件夹的动态发现系统，采用3级渐进式加载：

#### 渐进式披露 (Progressive Disclosure)
- **Level 1**: 元数据 (~100 tokens/skill, 始终加载)
  - name, description, category, tags
  - 快速索引和匹配
  
- **Level 2**: SKILL.md 内容 (~5k tokens, 触发时加载)
  - 完整的技能逻辑
  - 支持变量替换和动态注入
  
- **Level 3**: 支持文件 (无限制, 按需加载)
  - 脚本、模板、参考文件
  - 仅在需要时访问

#### Skills 工具接口
```python
skill_discover_and_execute(query, arguments)  # 自然语言发现并执行
skill_list_available(category)                # 按类别浏览技能
skill_get_prompt(skill_name, arguments)      # 预览技能逻辑
```

## 技能类别

| 类别 | 描述 | 示例 |
|------|------|------|
| data | CSV, JSON, SQL 处理 | 数据转换、分析 |
| web | HTTP, 爬虫, API | 网站抓取、API调用 |
| file | 高级文件操作 | 批量处理、格式转换 |
| code | 代码分析、格式化 | 静态分析、重构 |
| image | 图像处理分析 | OCR、格式转换 |
| text | NLP、文本处理 | 摘要、提取 |
| finance | 金融分析 | 股票分析、投资组合 |

## 集成流程

### 1. 初始化
```python
# app.py
scanner = get_skill_scanner()
discovery = SkillDiscovery(scanner)
executor = SkillExecutor()

# DeepAgents 集成
agent = SafeClawDeepAgent(llm_service)
# 自动加载所有 builtin + skills 工具
```

### 2. 工具传递给 DeepAgents
```python
# _get_safe_claw_tools() 返回 7 个工具：
# - 4 个 builtin tools
# - 3 个 skills system tools
tools = self._get_safe_claw_tools()
deep_agent = create_deep_agent(model=model, tools=tools)
```

### 3. 执行流程
```
用户查询 → DeepAgents → 工具选择 → 执行
                     ↓
        [Builtin Tool] 直接执行
        [Skills Tool] → 渐进式加载 → 执行
```

## 使用示例

### 使用 Builtin Tools
```
用户: "读取 config.json 文件"
DeepAgents: 调用 safe_claw_file_read("config.json")
```

### 使用 Skills System
```
用户: "分析这个CSV文件的销售趋势"
DeepAgents: 调用 skill_discover_and_execute("analyze csv sales trends", "data.csv")
系统: 
  1. L1 匹配: 找到 "csv_analyzer" 技能
  2. L2 加载: 读取 SKILL.md 内容
  3. L3 按需: 加载分析脚本
  4. 执行: 返回分析结果
```

## 性能优化

### 1. 内存效率
- Level 1 仅加载元数据，最小化内存占用
- Level 2/3 按需加载，避免浪费
- 智能缓存机制，重复使用已加载内容

### 2. 启动速度
- 启动时仅扫描 Level 1 元数据
- 避免加载大量技能内容
- 快速索引构建

### 3. 执行效率
- 语义匹配快速定位相关技能
- 并行加载 Level 2/3 内容
- 缓存执行结果

## 安全特性

### 1. 权限控制
- `allowed-tools` 前端字段限制工具使用
- `context: fork` 隔离执行环境
- 审计日志记录所有操作

### 2. 输入验证
- 参数类型检查
- 路径遍历防护
- 资源限制

### 3. 错误处理
- 优雅降级机制
- 详细错误报告
- 失败驱动的技能扩展

## 扩展性

### 1. 添加新 Builtin Tool
```python
@tool
def safe_claw_custom_tool(param: str) -> str:
    """Tool description"""
    # 实现
    return result
```

### 2. 添加新 Skill
创建文件夹结构：
```
skills/
  my_category/
    my_skill/
      SKILL.md  # 包含 frontmatter 和内容
      script.py  # 支持文件
      template.md  # 模板文件
```

### 3. 自定义技能类别
在 SKILL.md frontmatter 中指定：
```yaml
category: custom_category
tags: [custom, processing]
```

## 监控和调试

### 1. 日志记录
```python
logger.info(f"Loaded {len(tools)} tools: {builtin_count} builtin + {skills_count} skills")
```

### 2. 性能指标
- L1 加载时间
- L2/L3 按需加载统计
- 技能执行成功率
- 缓存命中率

### 3. 调试工具
- `skill_get_prompt()` 预览技能逻辑
- `skill_list_available()` 浏览可用技能
- 详细的执行结果报告

## 总结

这个架构实现了：
1. **清晰分离**: Builtin tools vs Skills system
2. **高效加载**: 3级渐进式披露
3. **动态扩展**: 基于文件夹的技能发现
4. **安全执行**: 权限控制和隔离
5. **性能优化**: 缓存和按需加载
6. **易于使用**: 自然语言接口

通过这种设计，SafeClaw 既能提供稳定的核心功能，又能灵活扩展领域特定的能力，同时保持高性能和安全性。
