# 问题 — PPT Mode

## 驱动场景

用户要在 SafeClaw 里**迭代做 PPT**：边改边看、对着某一页提需求。今天只能靠通用 `/agent` +（若有）pptx 类 skill 黑盒出文件，结果是：

1. **不可观测**：不知道改了哪一页、落盘哪个版本、预览是否刷新。  
2. **不可预览**：要下载到本地开 PowerPoint 才看得见。  
3. **难提需求**：只能在聊天里打长段自然语言，模型容易整份重做或静默「已改」却无新文件。  
4. **执行面过瘦**：复杂改稿若只依赖 skill 脚本，失败难定位，且与 ModePolicy / Exec 脱节。

## 根因（产品）

- Agent modes 仅有权限/观测轴，**无创作体裁**；PPT 被当成普通写文件任务。  
- 缺少**一等 PPT tools**（结构编辑、版本化存盘、预览）。  
- 缺少 **PPT Observability pack** 与预览面板合同。  
- 缺少类似 `[USER_STEER]` 的**页级短信号**合同。

## 成功时可见差异

| 之前 | 之后（`/ppt`） |
|------|----------------|
| 黑盒 skill / 手搓文件 | `safe_claw_ppt_*` 步进 Exec 可见 |
| 无页预览 | Deck Preview 强制打开并自动刷新 |
| 长聊天改需求 | `[PPT_STEER] slide=N` / `scope=deck` |
| 覆盖写风险 | 仅 create-only + `_vN` 版本链 |

## 非本问题

- 替代 Keynote/PowerPoint 专业桌面编辑。  
- 多租户协作编辑锁。  
