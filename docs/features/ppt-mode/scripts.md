# 脚本 — PPT Mode

实现阶段补充；Phase 0 仅占位合同。

## 建议脚本（目标路径）

| 脚本 | 用途 |
|------|------|
| `scripts/features/ppt-mode/validate_tools.sh` | pytest：`test/tools/test_ppt_tools.py` + mode policy |
| `scripts/features/ppt-mode/probe_preview.sh` | 对样例 pptx 调 preview；断言 PNG 数量 |
| `scripts/features/ppt-mode/probe_sse_preview.sh` | POST `/chat/stream` `mode=ppt`，过滤 `ppt_preview` |

## 手工 / Live LLM

```bash
# API :8000 已起
bash scripts/features/ppt-mode/probe_live_llm.sh
# 证据写入 ~/Downloads/safe_claw_worksapce/workspace/ppt/_evidence_*/
```

## 产物目录

```text
~/Downloads/safe_claw_worksapce/workspace/ppt/
  <deck_id>_vN.pptx
  previews/<deck_id>_vN/slide_XX.png
```
