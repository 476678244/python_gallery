# Human Non-Accept 过程报告 — 2026-08-01

记录 Memory / DeepSeek 验收过程中 **人工明确不接受** 的节点、原因与纠偏。  
对照 [acceptance.md](./acceptance.md)；通过项见 [acceptance-report-2026-08-01.md](./acceptance-report-2026-08-01.md)。

## 总览

| # | 时间点（约） | 人工判定 | 阻断点 | 是否已闭环 |
|---|--------------|----------|--------|------------|
| NA-01 | 验收前 | **不接受** | New Chat 后默认模型显示 Qwen3.5 9B，不是 DeepSeek | 修复中 / 待复验 |
| NA-02 | 修复讨论 | **不接受** | Agent 把「验收要 DeepSeek」误当成可擅自改产品默认，又一度提议改回 Qwen | 已澄清：DeepSeek **就是**全局默认 |
| NA-03 | 自查后 | **不接受（过程质量）** | 自动化全绿但人工路径失败；验收标准未覆盖「New Chat 继承全局默认」 | 已补 C2 + E2E |
| NA-04 | 原则声明 | **永不接受** | 静默 fallback；永远要求 Fail Fast | **常驻硬约束**（见下） |

---

## NA-01 — New Chat 默认不是 DeepSeek（硬阻断）

### 现象（人工）

1. 打开 SafeClaw UI  
2. 点击 **+ New Chat**  
3. Header 与输入框 chip 显示 **Qwen3.5 9B**  
4. 人工结论：**就这一条就无法验收** Memory / DeepSeek 场景  

### 根因

- `SessionCreateRequest.model` Pydantic 默认写死 `qwen3.5-9b-vlm`  
- 前端 New Chat 不传 `model` 时，该默认值盖掉 `_selected_model`（`agent_config` 里已是 `deepseek-v4-flash`）  
- UI 回退链曾用 `AVAILABLE_MODELS[0]` / 硬编码 Qwen，进一步放大错误展示  

### 为何自动化没拦住

- E2E 多在建会话后 **再显式切换** DeepSeek，或直接在请求体里带 `model`  
- `acceptance.md` 原先无「New Chat → 即 DeepSeek」条款  
- 报告写 PASS=14 时，**未走人工同一条路径**  

### 纠偏

- `model: Optional[str] = None`，缺省继承 `_selected_model`  
- `DEFAULT_MODEL` / 前端 `isDefault` 对齐为 `deepseek-v4-flash`  
- `model-store` + New Chat 拉 `/settings/model`  
- 新增 `test/e2e/new-chat-default-model.spec.ts` 与 acceptance **C2**  

### 复验门槛（人工）

硬刷新 → + New Chat → header / chip **必须**为 DeepSeek V4 Flash，**禁止**再选手动切换才开始测 Memory。

---

## NA-02 — 擅自改默认 / 又提议改回 Qwen（过程不被接受）

### 现象（人工）

- 追问：在什么情况下擅自改了默认模型？  
- Agent 曾反思为「不该改 isDefault」，并提议 **改回 Qwen**、只保留继承逻辑  

### 人工澄清

> **DeepSeek 就是全局的默认模型选择。**

### 纠偏原则（写入本报告）

| 允许 | 不允许 |
|------|--------|
| 把全局默认明确为 DeepSeek，并让 New Chat / 冷启动 / Settings 一致 | 为「凑验收」偷偷改默认却不写进 acceptance |
| 缺省参数继承全局 `_selected_model` | 用另一套产品默认（Qwen）覆盖全局已选 |
| Fail Fast：全局模型加载失败要可观测 | 静默 `getDefaultModel()` / 硬编码盖掉真实配置 |

---

## NA-03 — 「测试全绿」不能代替人工验收路径

### 现象（人工）

- Agent 侧：pytest / Playwright / headed jargon 已绿，acceptance-report 写完整通过  
- Human：打开 UI 点 New Chat → 仍是 Qwen → **拒绝验收**  

### 过程教训

1. **验收报告必须区分**：API/E2E 绿 ≠ 人工主路径绿  
2. **必须单列 Non-Accept 报告**（本文），避免只写成功叙事  
3. 驱动场景若依赖 DeepSeek，acceptance 必须包含：**默认即 DeepSeek，无需额外点击**  

---

## NA-04 — 永不接受静默 Fallback（常驻）

### 人工原话

> 我永远不接受静默 fallback。我永远要求 fail fast。  
> 系统是给我自己用的。

### 产品语境

SafeClaw 是 **个人自用** 系统，不是面向陌生用户的 SaaS。  
因此：**不要**为「产品友好 / 别吓到用户」做静默兜底；错了就立刻爆出来，方便本人排查。

### 含义（对本主题强制）

| 禁止 | 要求 |
|------|------|
| `.catch(() => {})` 吞掉模型/配置错误 | 抛错 + 可见错误（alert / 红字 / console 带上下文） |
| API 缺 `model` 时前端 invent `getDefaultModel()` | 拒绝解析 / 拒绝 New Chat / 拒绝发消息 |
| New Chat 加载全局模型失败仍建会话 | `await loadGlobalModel()` 失败则中止 |
| Settings 拉模型失败显示空列表装正常 | 显示错误，不假装「没有模型」 |
| 为「通用产品默认」覆盖你的全局选择 | DeepSeek 就是你的全局默认；以 `agent_config` / `/settings/model` 为准 |

### 已落地纠偏（模型路径）

- `model-store.ts`：空/未知 model → throw，无产品默认回填  
- Sidebar New Chat / Header / ChatInput / Settings：错误可见，不吞  
- 发消息前无 `currentModelId` → throw  

### 2026-08-01 全库自纠（第二轮）

| 区域 | 原静默行为 | 现 Fail Fast |
|------|------------|--------------|
| `api/main.py` chat stream | mock「fallback mode」回复 | `type:error` + 中止，无假回复 |
| `api/main.py` Phase 4 self-healing | DeepAgent 失败改写 mock | 失败即 error SSE |
| `llm_gateway.py` | 初始化失败 → MockLLMGateway | 抛错；仅 `SAFECLAW_ALLOW_MOCK_LLM=1` 允许 mock |
| sessions/messages JSON | 损坏 → `[]` | RuntimeError |
| agent_config / secrets | 损坏吞掉 | RuntimeError |
| `/llm-calls` | 无日志 invent 假 prompt | HTTP 404 |
| memory storage save/load/list | 返回 False/None/[] | raise |
| BFF `.catch(() => ({}))` / `success: true` | 假装成功 | 400/502 + detail |
| ChatContainer 拉消息 | 失败当空聊天 | 红字错误，禁用输入 |
| 消息 persist /clear / upload | empty catch | alert + throw |

---

## 仍待人工 Accept 的检查项

- [ ] NA-01 复验：New Chat → DeepSeek（C2）  
- [ ] 「什么是101」在 **默认 DeepSeek 新会话** 下仍给投资黑话义项（非大学导论）  
- [ ] Memory 面板在该会话下可见 jargon  

---

## 相关文档

- [acceptance.md](./acceptance.md) § C2  
- [acceptance-report-2026-08-01.md](./acceptance-report-2026-08-01.md)  
- [e2e.md](./e2e.md) — `new-chat-default-model.spec.ts`  
- 截图证据：会话开始时 UI 显示 Qwen（人工提供，2026-08-01）  
