# 验收标准

勾选表示已满足。个人自用；Fail Fast；方法论见 [methodology.md](./methodology.md)。

## A. 硬闸门（防冒进）

- [x] 缺 `look_ahead` / 不足 3 条 / 空 `expected_output` / 未知 `agent_name` → **不 spawn**  
- [x] 失败有显式错误（SSE `subagent` `status: failed` 或等价 ToolMessage），含缺字段名  
- [x] Prompt 不是唯一防线（包装层必校验）  

## B. SSE / 后端观测

- [x] `task`（或 fork）成功时 SSE 出现 `step_type: subagent`，含 `step_now`、`look_ahead`[3]、`expected_output`  
- [x] Nested 工具为 `tool_call` 且 `parent_step_id` 指向该 subagent  
- [x] `done` 路径无未定义 `skill_names`  

## C. 前端默认展开

- [x] Exec **默认展开**前瞻三步（DOM 可读三条，非仅 store）  
- [x] Nested 中间工具/推理 **默认展开**（可手动折叠）  
- [x] 闸门失败原因在 Exec 可见  

## D. 主上下文不污染

- [x] 子代理中间 transcript **不**进入主 agent `messages` / 下一轮 prompt  
- [x] 观测事件只进 SSE / Exec / 关联 llm-calls，不回写主 chat message 正文为完整子轨迹  
- [ ] 不合格结果通过 **重新 spawn** 纠正，而非把失败子轨迹合并进主上下文续聊  
- [x] 用户「纠正方向」只注入短控制信号（如 `[USER_STEER]`），不回灌旧子轨迹；main 换向后新 spawn  

## D2. 用户控制（产品已接）

- [x] Stop the World：一键冻结，现场可检（Exec Halt + world-stopped banner；Esc）  
- [x] 纠正方向：取消 subagent + 注入 `[USER_STEER]` 并 **stream 新一轮**（非仅写 store；R 开 modal）

## E. Skill fork / ToolManager（Phase C）

- [ ] `context: fork` 真执行（非仅 config）  
- [ ] `skill_discover_and_execute` 对 `type: subagent` 无空壳 success  
- [ ] 子代理 skills/tools 尊重 skills-activation enabled SoT  

## F. 有头黄金路径

- [x] [e2e.md](./e2e.md) S1–S3 通过（有头可选复验）  
- [x] 有 `acceptance-report-YYYY-MM-DD.md`  
- [x] 有 [evidence/](./evidence/README.md)（截图 + pytest/Playwright 日志 + DOM JSON）  

## G. 文档 / 回归

- [x] 本目录与行为一致  
- [ ] skills-activation 回归不破  

## 明确不验收（本期）

- Cursor 全类型 subagent 全家桶  
- Streamlit 对等 UI  
- 修改 DeepAgents 上游  
- Per-session 独立 skill 配置  
