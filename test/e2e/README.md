# E2E 测试指南

## 测试目的

验证 SafeClaw 全链路功能正常：前端页面加载 → 会话创建 → 对话流（SSE stream） → 多轮对话 → 自愈。

基于 [Flow Coding 5 阶段算法](/docs/flow_coding.md)：

| 阶段 | 目标 |
|------|------|
| Phase 1 | **验证基线** — 页面加载无致命错误，textarea 可见 |
| Phase 2 | **基础对话** — 发送消息、收到有意义的 LLM 回复 |
| Phase 3 | **多轮对话** — 上下文保持，user/assistant 消息计数正确 |
| Phase 4 | **自愈修复** — 连续发送消息，失败时自动重建 session 重试 |
| Phase 5 | **最终确认** — 截图存档，确认全部功能正常 |

---

## 测试文件

**统一测试入口：`test/e2e/`**（已从 `safeclaw-ui/my-app/tests/e2e/` 合并）

| 文件 | 说明 |
|------|------|
| `memory-panel.spec.ts` | Memory 面板 + `/remember` |
| `memory-safety-sessions-smoke.spec.ts` | Memory/Safety/Sessions API smoke |
| `deepseek-chat-memory.spec.ts` | DeepSeek 实网聊天 + 记忆召回（需 key） |
| `memory-jargon-zh.spec.ts` | 黑话中文问句黄金路径（见 `docs/features/memory-system/e2e.md`） |
| `basic-chat-flow-coding.spec.ts` | 基础对话 5 阶段 E2E 测试 |
| `skill-tree.spec.ts` | **Skill Tree 4 主目录 E2E 测试** |
| `skill-recognition-flow-coding.spec.ts` | Skill 路由识别测试 |
| `skills-path-activation.spec.ts` | Skills Path 面板激活测试 |
| `skills-path-panel.spec.ts` | Skills Path 面板 UI 测试 |
| `skill-tree-reload-consistency.spec.ts` | Skill Tree 重载一致性测试 |
| `skill-tree-session-switch.spec.ts` | Skill Tree 会话切换一致性测试 |
| `skill-autocomplete.spec.ts` | Skill 自动补全测试 |
| `sidebar.spec.ts` | 侧边栏 UI 测试 |
| `safeclaw.spec.ts` | SafeClaw 综合测试 |
| `chat-input-dropzone.spec.ts` | 聊天输入拖拽区测试 |
| `exec-panel-chat.spec.ts` | 执行面板聊天测试 |
| `prompt-inspect-panel.spec.ts` | Prompt 检查面板测试 |
| `prompt-inspect-flow-coding.spec.ts` | **Prompt Inspect + Private Skills E2E (Flow Coding 5阶段)** |
| `right-panel-resize.spec.ts` | 右侧面板调整大小测试 |
| `right-panel-toggle.spec.ts` | 右侧面板开关测试 |
| `playwright.config.ts` | Playwright 配置（headless: false） |
| `global-teardown.ts` | 全局清理（kill 服务进程） |

### Skill Tree 4 主目录

| 目录 | 路径 | 类型 | 预期 skills |
|------|------|------|-------------|
| Private Skills | `skills/private_skills/` | 本地目录 | 6-10 |
| Anthropic Skills | `linked_skills/anthropic_skills` | symlink → `/Users/nicole/workspace/github/skills/skills` | 15-20 |
| Ljg Skills | `linked_skills/ljg-skills` | symlink → `/Users/nicole/workspace/github/ljg-skills/skills` | 18-25 |
| Superpowers Skills | `linked_skills/superpowers_skills` | symlink → `/Users/nicole/workspace/github/superpowers/skills` | 12-18 |

---

## 运行方法

### 前置条件

1. **LM Studio** 手动启动（本地 LLM 服务）
2. **Proxy bypass** — 必须设置：
   ```bash
   export NO_PROXY="192.168.50.30,localhost,127.0.0.1,192.168.50.204"
   export no_proxy="192.168.50.30,localhost,127.0.0.1,192.168.50.204"
   ```

### 启动服务

```bash
# 1. 设置 proxy bypass
export NO_PROXY="192.168.50.30,localhost,127.0.0.1,192.168.50.204"
export no_proxy="192.168.50.30,localhost,127.0.0.1,192.168.50.204"

# 2. 启动 API server (port 8000)
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw
cd /Users/nicole/workspace/github/a476678244/python_gallery
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level warning &

# 3. 验证 API 就绪
curl -s http://localhost:8000/health
# 预期: {"status":"healthy","safe_claw_loaded":true,"version":"1.0.0"}

# 4. 启动前端 (port 3000)
cd safeclaw-ui/my-app
npm run dev &

# 5. 验证前端就绪
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 预期: 200
```

### 运行测试

```bash
# 运行 Skill Tree 测试（headed 模式，推荐）
cd /Users/nicole/workspace/github/a476678244/python_gallery/safeclaw-ui/my-app
npx playwright test --config ../../test/e2e/playwright.config.ts skill-tree.spec.ts

# 运行全部 E2E 测试
npx playwright test --config ../../test/e2e/playwright.config.ts

# 运行特定测试文件
npx playwright test --config ../../test/e2e/playwright.config.ts basic-chat-flow-coding.spec.ts

# 查看测试报告
npx playwright show-report
```

---

## 测试要求

### 必须满足

- **API + 前端都已启动** — 测试不会自动启动服务，必须手动确保
- **LM Studio 已运行** — 提供本地 LLM 推理；无 LM Studio 时走 fallback 模式（仍可通过测试）
- **NO_PROXY 已设置** — 否则 localhost 请求会经过代理返回 503

### 测试判定标准

| 测试 | 通过条件 |
|------|----------|
| Phase 1 | 页面加载无致命 JS 错误，textarea 可见 |
| Phase 2 | 发送消息后收到 assistant 回复，回复长度 > 10，不含 "Error" |
| Phase 3 | 2 轮对话后 user 消息 ≥ 2，assistant 消息 ≥ 2 |
| Phase 4 | 连续 3 条消息均获得回复（失败时自动重建 session） |
| Phase 5 | 最终回复长度 > 20，截图保存成功 |
| Skill Tree T1-T10 | 4 主目录加载、toggle、persist、API 一致 |

---

## 测试实践

### 踩过的坑

1. **Proxy 导致 503** — `all_proxy=127.0.0.1:8001` 会拦截 localhost 请求。必须设置 `NO_PROXY`
2. **Session 未创建导致 textarea disabled** — `ensureSession()` 通过 API 直接创建 session 并导航，比点击 "New Chat" 按钮更可靠
3. **Python urllib 也受 proxy 影响** — 使用 `urllib.request.ProxyHandler({})` bypass
4. **uvicorn `--reload False` 无效** — uvicorn 的 `--reload` 是 flag，不接受 boolean 值，直接去掉即可
5. **subprocess.Popen stdout=PIPE 导致挂起** — 服务器 stdout 管道满后阻塞，改用 `os.devnull`
6. **前端 dev server 启动慢** — 需要等待 ~15 秒才能真正可用

### 关键设计决策

- **playwright.config.ts 中 `headless: false`** — 默认有头模式，方便 Flow Coding 可视化确认
- **`slowMo: 500`** — 降速操作，便于肉眼观察测试流程
- **`retries: 1`** — Phase 4 自愈：失败后自动重试一次
- **`globalTeardown`** — 测试完毕自动 kill 临时启动的服务进程
- **`ensureSession` 双策略** — 先用 API 创建 session，再 fallback 到点击按钮

### 典型成功输出

```
Running 5 tests using 1 worker

✅ Phase 1: Verification baseline established
  ✓  Phase 1: 验证基线 - 页面加载 (2.0s)
✅ Phase 2: Intent expression works
  ✓  Phase 2: 基础对话 (27.4s)
✅ Phase 3: Multi-turn chat (6 user, 6 assistant)
  ✓  Phase 3: 多轮对话 (8.9s)
✅ Phase 4: Self-healing loop completed
  ✓  Phase 4: 自我修复 (13.1s)
✅ Phase 5: Final convergence complete
  ✓  Phase 5: 最终验证 (6.5s)

🎉 Flow Coding: 基础对话功能测试完成

5 passed (1.0m)
```
