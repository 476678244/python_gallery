# 脚本

本期以 API / pytest / Playwright 为主；辅助脚本按需追加。

## 快速核对 SoT

```bash
# 当前持久化 enabled 列表
python3 - <<'PY'
import json
from pathlib import Path
p = Path.home() / "Downloads/safe_claw_worksapce/Data/agent_config.json"
d = json.loads(p.read_text())
skills = d.get("enabled_skills") or []
print("model:", d.get("model"))
print("enabled_count:", len(skills))
for s in skills[:30]:
    print(" -", s)
if len(skills) > 30:
    print(f" ... +{len(skills)-30} more")
PY

curl -s http://127.0.0.1:8000/settings/model
curl -s -o /dev/null -w "skills:%{http_code}\n" http://127.0.0.1:8000/skills
```

## 建议新增（Phase A/B）

| 脚本 | 用途 |
|------|------|
| `scripts/skills/verify_enabled_filter.sh` | Toggle 关 Ljg → 严格匹配，private 不被误伤 |

```bash
bash scripts/skills/verify_enabled_filter.sh
```

## 测试入口

```bash
# API
python -m pytest test/api/test_skills.py -q

# E2E（落地后）
cd test/e2e && npx playwright test skills-activation.spec.ts --retries=0
```
