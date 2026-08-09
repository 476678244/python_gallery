# Cross-check — Agent Modes vs 合同（2026-08-03）

对照 [methodology.md](./methodology.md) §3 行为矩阵，逐 mode 核对实现。

## 矩阵结论

| Mode | 读/写门禁 | Skill execute | Memory 自动写 | Spawn `task` | 观测 pack | 判定 |
|------|-----------|---------------|---------------|--------------|-----------|------|
| ask | FS + ToolManager 硬只读 | off（剥工具） | 否 | **SpawnGate 硬挡** | default；切出 Full 释 Skills/Prompts | ✅ |
| agent | 满写策略 | full | 是 | on（可跑） | default | ✅ |
| plan | 同 ask 硬只读 | off | 否 | explore_only **未接线 → 当 off 硬挡** | default | ✅（‡） |
| safe | create-only + `allow_edit=False` | restrained | 否 | **SpawnGate 硬挡** | default | ✅ |
| debug | 同 agent | full | 是 | on | Full pack；切出解除 Skills/Prompts | ✅ |
| subagent | 同 agent | full | 是 | required（策略+brief 闸） | Subagent pack（仅 Exec） | ✅ |
| loop | 非 `/chat/stream` mode；调度继承执行 mode | — | — | — | 继承 | ✅ |

‡ methodology：plan spawn=explore-only「若已接线；否则否」— 当前 **否**。

## 本轮修复

1. **`SpawnGateMiddleware`**：`spawn` ∉ `{on,required}` 时拦截 DeepAgents `task`（Fail Fast ToolMessage），不再只靠 prompt。  
2. **观测 pack 切出**：`applyObservabilityPack("default")` 释放 Full 强制的 Skills/Prompts；`subagent` pack 同样剥离它们。  
3. **Prompt 加严**：ask/plan/safe addendum 明确禁止 task/spawn。

## 已知残留（不挡本期核心验收）

| 项 | 说明 |
|----|------|
| ~~Plan 专用卡片 UI~~ | ✅ `PlanArtifactCard` + e2e S3 |
| ~~Debug 嵌套树 / Halt·Steer~~ | ✅ Exec 树 + Halt/Steer（Esc/R）+ world-stopped banner；Steer 经 `safeclaw:send-prompt` 真发流 |
| `allow_delete=True` | 策略位已传；backend 删除路径历史默认关闭，与 methodology「仍受 backend 约束」一致 |
| plan `explore_only` | 保留策略枚举；运行时等同 off，直至接线 |
| Legacy session 无 `mode` | UI `parseAgentMode` → agent；与 New Chat 默认一致 |

## 回归

```bash
# proxy unset if socksio missing
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  conda run -n safe_claw pytest test/deepagents/test_mode_policy.py test/api/test_agent_modes.py -q
```
