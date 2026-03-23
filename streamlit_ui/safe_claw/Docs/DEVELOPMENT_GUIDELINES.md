# 🦞 SafeClaw 开发指南

## 📋 开发规范和最佳实践

### 🔍 常见错误和解决方案

本文档总结了 SafeClaw 开发过程中遇到的常见错误，帮助开发者避免重复犯错。

---

## 📦 **导入和模块相关错误**

### 1. **Emoji 文件名导入错误**

**问题描述**: Python 无法直接导入包含 emoji 的模块名

```python
# ❌ 错误做法
from streamlit_ui.pages._00_💬_Chat import render

# ✅ 正确做法  
import importlib.util
spec = importlib.util.spec_from_file_location("chat_module", pages_dir / "00_💬_Chat.py")
chat_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_module)
```

**解决方案**: 使用 `importlib.util.spec_from_file_location` 绕过文件名限制

**相关文件**: `streamlit_ui/pages/chat_page.py`, `memory_page.py`, `settings_page.py`, `stats_page.py`

---

### 2. **缺少必要的导入**

**问题描述**: 运行时出现 `NameError` 因为模块未导入

```python
# ❌ 错误做法
def some_function():
    return datetime.now() - timedelta(hours=24)  # NameError: name 'timedelta' not defined

# ✅ 正确做法
from datetime import datetime, timedelta  # 在文件顶部导入所有需要的模块
```

**解决方案**: 始终在文件顶部导入所有需要的模块

**相关文件**: `core/memory/retriever.py`, `core/memory/layers/active.py`

---

### 3. **循环依赖和初始化顺序**

**问题描述**: 在对象完全初始化前调用其方法

```python
# ❌ 错误做法
def _load_config():
    if not config_file.exists():
        self._save_config()  # 此时 self._config 还未设置
        return self.default_config

# ✅ 正确做法  
def _load_config():
    if not config_file.exists():
        self._config = self.default_config  # 先设置
        self._save_config()
        return self.default_config
```

**解决方案**: 注意初始化顺序，确保依赖的对象已正确初始化

**相关文件**: `services/config_service.py`

---

## 🔧 **类型和配置相关错误**

### 4. **枚举和字符串混用**

**问题描述**: API 只接受枚举但测试传入字符串

```python
# ❌ 错误做法
def delete_memory(self, memory_id: str, layer: MemoryLayer):  # 只接受枚举
    layer_path = self.storage_path / layer.value

# ✅ 正确做法
def delete_memory(self, memory_id: str, layer):  # 接受枚举或字符串
    layer_value = layer.value if hasattr(layer, 'value') else layer
    layer_path = self.storage_path / layer_value
```

**解决方案**: 设计 API 时支持多种输入类型，使用 `hasattr()` 检查

**相关文件**: `core/memory/storage.py`

---

### 5. **对象引用 vs 拷贝**

**问题描述**: 修改对象影响了不应该修改的原始对象

```python
# ❌ 错误做法
self._config = self.default_config  # 引用同一个对象
# 修改 self._config 会影响 default_config

# ✅ 正确做法
self._config = SafeClawConfig(**self.default_config.dict())  # 创建拷贝
```

**解决方案**: 区分对象引用和拷贝，使用 `dict()` 或 `model_dump()` 创建新对象

**相关文件**: `services/config_service.py`

---

### 6. **Pydantic 模型验证**

**问题描述**: Pydantic 模型缺少必需字段导致验证错误

```python
# ❌ 错误做法
config = LLMConfig(api_key='mock-key')  # 缺少 provider, model

# ✅ 正确做法
config = LLMConfig(
    provider='openai',
    model='gpt-3.5-turbo', 
    api_key='mock-key'
)
```

**解决方案**: 始终提供 Pydantic 模型所需的所有必需字段

**相关文件**: 所有使用 Pydantic 模型的文件

---

## 🏗️ **架构和服务相关错误**

### 7. **服务检查过于严格**

**问题描述**: 页面要求所有服务都可用才能加载

```python
# ❌ 错误做法
required_services = ['llm_service', 'memory_manager', 'graph_builder', 'skill_registry']
return all(service in st.session_state for service in required_services)

# ✅ 正确做法
essential_services = ['memory_manager']  # 只检查必需的
optional_services = ['llm_service', 'graph_builder']  # 可选的显示警告
```

**解决方案**: 设计优雅降级，允许部分功能在服务缺失时仍可用

**相关文件**: `streamlit_ui/pages/04_🔧_Tools.py`, `streamlit_ui/pages/05_🏠_Dashboard.py`

---

### 8. **异常处理不当**

**问题描述**: 静默失败导致难以调试

```python
# ❌ 错误做法
try:
    result = risky_operation()
except Exception:
    return  # 静默失败

# ✅ 正确做法
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return None
```

**解决方案**: 具体的异常处理和日志记录

---

## 🧪 **测试相关错误**

### 9. **测试用例假设错误**

**问题描述**: 测试依赖共享状态导致失败

```python
# ❌ 错误做法
def test_config_reset():
    service = ConfigService()
    custom_config = service.config  # 引用同一个对象！
    custom_config.debug = True
    # 修改会影响原始配置

# ✅ 正确做法
def test_config_reset():
    service = ConfigService()
    new_config = SafeClawConfig(**service.config.dict())  # 创建拷贝
    new_config.debug = True
    service.update_config(new_config)
```

**解决方案**: 确保测试的独立性，避免共享状态

**相关文件**: `tests/unit/test_services.py`

---

### 10. **Mock 配置不完整**

**问题描述**: Mock 对象缺少必要的方法

```python
# ❌ 错误做法
mock_llm_service = Mock()
mock_llm_service.invoke.return_value = "response"  # 缺少其他方法

# ✅ 正确做法
mock_llm_service = Mock(spec=LLMService)
mock_llm_service.invoke.return_value = "response"
mock_llm_service.stream.return_value = iter(["word", "by", "word"])
```

**解决方案**: 使用 `spec` 参数确保 Mock 对象完整模拟真实接口

---

### 11. **Streamlit 页面导航错误**

**问题描述**: `st.switch_page()` 需要文件路径而不是页面名称

```python
# ❌ 错误做法
st.switch_page("📚 Memory")  # StreamlitAPIException: Could not find page

# ✅ 正确做法
st.switch_page("pages/01_📚_Memory.py")  # 使用相对文件路径
```

**解决方案**: 使用相对于主脚本的文件路径，从 `pages/` 目录开始

**相关文件**: `streamlit_ui/components/dashboard.py`

---

### 12. **聊天页面显示为空**

**问题描述**: 聊天页面没有显示任何消息，包括欢迎消息

```python
# ❌ 错误做法
# 只显示现有消息，没有欢迎消息
for message in st.session_state.messages:
    render_message(message)

# ✅ 正确做法
# 显示欢迎消息如果聊天为空
if not st.session_state.messages:
    st.chat_message("assistant").write("👋 Hello! I'm SafeClaw...")

for message in st.session_state.messages:
    render_message(message)
```

**解决方案**: 添加欢迎消息和备选的消息渲染器

**相关文件**: `streamlit_ui/pages/00_💬_Chat.py`

---

### 13. **组件服务依赖检查缺失**

**问题描述**: 组件直接使用可能为 None 的服务对象

```python
# ❌ 错误做法
skill_registry = get_skill_registry()
render_skill_manager(skill_registry)  # skill_registry 可能为 None

# ✅ 正确做法
skill_registry = get_skill_registry()
if skill_registry:
    render_skill_manager(skill_registry)
else:
    st.warning("⚠️ Skill registry not available. Some features may be limited.")
```

**解决方案**: 在使用服务前检查是否可用，提供友好的降级信息

**相关文件**: `streamlit_ui/pages/04_🔧_Tools.py`

---

### 14. **Streamlit 过时参数警告**

**问题描述**: 使用已过时的 `use_container_width` 参数

```python
# ❌ 错误做法
st.button("Click me", use_container_width=True)
st.plotly_chart(fig, use_container_width=True)

# ✅ 正确做法
st.button("Click me", width='stretch')  # 或 width='content'
st.plotly_chart(fig, width='stretch')  # 或 width='content'
```

**解决方案**: 使用新的 `width` 参数替代 `use_container_width`

**相关文件**: 所有包含图表和按钮的组件

---

## 🎯 **通用开发原则**

### **关键教训总结:**

1. **防御性编程** - 假设外部依赖可能失败，提供降级方案
2. **明确错误处理** - 不要静默失败，提供有意义的错误信息
3. **测试独立性** - 确保测试不依赖共享状态
4. **API 设计灵活性** - 支持多种输入类型，向后兼容
5. **初始化顺序** - 明确依赖关系，避免循环依赖
6. **日志记录** - 关键操作要有日志，便于调试
7. **类型安全** - 使用类型提示，避免运行时错误
8. **资源管理** - 及时释放资源，避免内存泄漏

---

## 📋 **开发检查清单**

在提交代码前，请确保：

- [ ] 所有导入都在文件顶部？
- [ ] 对象引用vs拷贝使用正确？
- [ ] 异常处理具体且有日志？
- [ ] API 支持多种输入类型？
- [ ] 初始化顺序正确？
- [ ] 测试用例独立？
- [ ] Mock 配置完整？
- [ ] 服务检查有优雅降级？
- [ ] 使用了类型提示？
- [ ] 添加了适当的日志记录？

---

## 🚀 **SafeClaw 特定约定**

### **文件命名**
- 页面文件可以使用 emoji，但需要通过包装器导入
- 模块名使用下划线分隔的小写字母

### **服务初始化**
- 使用 Mock 服务作为降级方案
- 优雅处理服务不可用的情况
- 在侧边栏显示服务状态

### **错误处理**
- 使用 `logger.error()` 记录错误
- 对用户提供友好的错误信息
- 关键功能要有降级方案

### **测试策略**
- 单元测试覆盖率目标: 100%
- 集成测试测试主要工作流
- 使用 Mock 避免外部依赖

---

*记住: 代码不仅要能工作，还要在异常情况下优雅处理！*

**🦞 SafeClaw AI Safety Assistant - 开发团队**
