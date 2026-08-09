# 完整验收报告 — 2026-08-01

对照 [acceptance.md](./acceptance.md)。  
过程中人工拒绝项见 **[human-non-accept-report-2026-08-01.md](./human-non-accept-report-2026-08-01.md)**（必读，不可只看本表）。

## 一、自动化结果（上午轮次，修订前）

| 项 | 结果 |
|----|------|
| UI / API health | ✓ 200 |
| DeepSeek configured | ✓ |
| A 检索（101 / 什么是101 / 黑话 / 皮夹克 / layer=400） | ✓ |
| D verify + ingest 脚本 | ✓ |
| pytest API + memory unit | ✓ **27 passed** |
| E2E headless（jargon+memory+slash+model+deepseek+skill-ac） | ✓ **27 passed** |
| E2E **HEADED** `memory-jargon-zh` | ✓ **5 passed** |
| Live stream「什么是101」 | ✓ `5 relevant memories` + 散户/接盘义项 |

> 上表曾汇总为 PASS=14 FAIL=0。**人工随后以 NA-01 拒绝完整验收**（New Chat 默认 Qwen）。

## 二、C2 全局默认 DeepSeek（修订后自纠）

| 项 | 状态 |
|----|------|
| `DEFAULT_MODEL = deepseek-v4-flash` | 已改代码 |
| 前端 `isDefault` → DeepSeek V4 Flash | 已改代码 |
| `POST /sessions` 无 model → 继承全局 | 已修 + API 测试 |
| `/settings/models` 含 DeepSeek + `default` 字段 | 已改代码 |
| UI New Chat → header/chip DeepSeek | 已接线 `model-store` |
| E2E `new-chat-default-model.spec.ts` | ✓ **2 passed** |
| Fail Fast（禁止静默 fallback，NA-04） | ✓ 模型路径已按硬约束改完 |
| **人工复验 C2（UI 硬刷新 + New Chat）** | ⏳ 待 Human Accept |

## 三、当前验收结论

| 维度 | 结论 |
|------|------|
| Memory 检索 / 注入 / jargon E2E | 自动化通过（见第一节） |
| New Chat = 全局默认 DeepSeek | **待人工 Accept（C2）** — 此前 NA-01 不通过 |
| 完整产品验收 | **未关闭**，直到 C2 人工勾选 |

### 人工复验命令

```bash
# API
curl -s http://127.0.0.1:8000/settings/model
curl -s -X POST http://127.0.0.1:8000/sessions -H 'Content-Type: application/json' -d '{"title":"New Chat"}'

# E2E
cd test/e2e && npx playwright test new-chat-default-model.spec.ts --retries=0
```

UI：硬刷新 → + New Chat → 确认 DeepSeek V4 Flash → 再测「什么是101」。
