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

| 文件 | 说明 |
|------|------|
| `basic-chat-flow-coding.spec.ts` | 基础对话 5 阶段 E2E 测试 |
| `playwright.config.ts` | Playwright 配置（已废弃，使用 safeclaw-ui 中的配置） |

**正式测试入口在 `safeclaw-ui/my-app/tests/e2e/`：**

| 文件 | 说明 |
|------|------|
| `basic-chat-flow-coding.spec.ts` | 基础对话功能测试 |
| `skill-recognition-flow-coding.spec.ts` | Skill 路由识别测试 |

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
# headed 模式（可视化浏览器，推荐调试）
cd /Users/nicole/workspace/github/a476678244/python_gallery/safeclaw-ui/my-app
npx playwright test tests/e2e/basic-chat-flow-coding.spec.ts --headed

# headless 模式（CI/无头）
npx playwright test tests/e2e/basic-chat-flow-coding.spec.ts

# 运行全部 E2E 测试
npx playwright test tests/e2e/

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
- **`afterAll` 中 cleanup** — 测试完毕自动 kill 临时启动的服务进程
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
