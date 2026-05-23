python version: 3.11

conda activate safe_claw

## ⚠️ WORKSPACE DIRECTORY — MANDATORY RULE

**ALL temporary files, agent outputs, and working files MUST be written to:**

```
WORKSPACE_DIR = ~/Downloads/safe_claw_worksapce/workspace/
```

- This is the **only** designated working directory for the SafeClaw agent.
- **Never** write temporary files to the project source tree, `/tmp`, or any other location.
- Code reference: `WORKSPACE_DIR = Path.home() / "Downloads" / "safe_claw_worksapce" / "workspace"` in `streamlit_ui/api/main.py`
- The directory is auto-created on startup. Do not hardcode alternative paths.

For package import under streamlit_ui. follow below practice:
- start from streamlit_ui.safe_claw.
- Don`t from safe_claw.

For package import under safe_claw. follow below practice:
- start from safe_claw.
- Don`t from streamlit_ui.safe_claw.

## Debug Mode Configuration

### IntelliJ IDEA Debug Configuration

1. **Create Run/Debug Configuration:**
   - Go to `Run` → `Edit Configurations...`
   - Click `+` → `Python`
   - **Name:** `Streamlit Debug`
   - **Module name:** `streamlit`
   - **Parameters:** `run streamlit_ui/app.py --server.port 8502 --server.headless false --logger.level debug`
   - **Python interpreter:** Select your project's Python interpreter
   - **Working directory:** Set to your project root directory (e.g., `/path/to/python_gallery`)

2. **Environment Variables:**
   ```
   STREAMLIT_SERVER_PORT=8502
   STREAMLIT_SERVER_HEADLESS=false
   STREAMLIT_LOGGER_LEVEL=debug
   PYTHONPATH=./streamlit_ui
   ```

3. **Debugging Steps:**
   - Set breakpoints in `app.py` or any imported modules
   - Click the debug button (🐛) or press `Ctrl+D` (or `Cmd+D` on Mac)
   - Use IntelliJ's debugger: variables panel, console, step over/into
   - Streamlit automatically hot-reloads on file changes

### Common Debugging Locations
- `initialize_session_state()` function (lines ~50-120)
- LLM service initialization
- Memory manager setup
- Graph builder creation

## Fail Fast 实践要求

核心原则：**永远不要掩盖错误，让问题立即暴露**

### 1. 禁止 Silently Fallback

当遇到无法处理的输入/状态时，**禁止**使用 fallback 默认值或静默忽略。

❌ **错误做法：**
```python
if not collection_name:
    # 错误：掩盖问题，导致下游逻辑出错
    collection_name = skill_path.parent.name
    collection_path = skill_path.parent
```

✅ **正确做法：**
```python
if not collection_name:
    raise ValueError(
        f"[SkillTree] Cannot determine collection for skill '{skill_name}'\n"
        f"  Path: {path_str}\n"
        f"  Parts: {parts}\n"
        f"  Expected pattern: linked_skills/<collection>/<skill>"
    )
```

### 2. 异常信息必须包含上下文

抛出异常时，必须包含足够的信息来定位问题：

```python
raise ValueError(
    f"[ComponentName] 具体问题描述\n"
    f"  Variable: {variable_name}\n"
    f"  Path: {file_path}\n"
    f"  Expected: 预期格式/值\n"
    f"  Actual: 实际值"
)
```

### 3. 路径解析必须严格验证

处理文件路径时，验证每一级目录是否符合预期结构：

```python
# 严格匹配，不使用模糊匹配
if part == "linked_skills":  # ✅ 精确匹配
    ...

if "linked" in part:  # ❌ 太宽松，可能导致误判
    ...
```

### 4. 开发阶段使用 INFO 级日志

在关键路径添加详细的 INFO 日志，便于调试：

```python
logger.info(f"[SkillTree] Processing skill '{skill_name}' at path: {path_str}")
logger.info(f"[SkillTree]   -> {collection_name} (from {source})")
```

### 5. 生产环境可配置降级

如果某些场景确实需要容错，使用显式配置而非隐式 fallback：

```python
if config.STRICT_MODE:
    raise ValueError("...")
else:
    logger.warning("Using fallback for compatibility")
    # 显式的降级逻辑
```

### 应用示例

以 `build_complete_skill_tree` 为例：

1. 每个 skill 必须能确定所属 collection
2. 无法确定时立即抛出异常
3. 异常包含完整的路径信息
4. 开发时通过日志追踪路径解析过程