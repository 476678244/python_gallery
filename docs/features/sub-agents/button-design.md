# Button 设计合同 — Subagent 可观测 UI

对齐圆桌结论（[roundtable--observability-ui-demo.md](./roundtable--observability-ui-demo.md) 第 2 轮）与 prod `right-panel`。

## 分层

| 层 | 谁用 | 视觉 | 按钮 |
|----|------|------|------|
| **A · 产品控制** | 真用户 / 落地 React | 落在 **Execution Path 面板头**，浅色、紧凑 | `纠正方向` · `Halt` |
| **B · Demo 场景** | 只 Demo | 顶栏 **降权**：浅底描边，不抢第一眼 | `S1` `S2` `S3` `重置` |
| **C · 对话确认** | Modal | 次要描边 + 一个实心主操作 | `取消` · `确认纠正并提示 Main` |

禁止：把 Halt/Steer 做成顶栏彩虹大钮（抢戏）；禁止第三套 chrome。

## A · 产品控制（Exec 头）

```
[ Execution Path ]     [ 纠正方向 ] [ Halt ]  [✓]
```

| 按钮 | 角色 | 样式 | 快捷键 |
|------|------|------|--------|
| 纠正方向 | secondary | 白底、`amber-800` 字、`#fde68a` 边；hover 浅琥珀底 | `R` |
| Halt | danger | 实心 `red-600` 白字；短标签 **Halt**（完整语义用 title/`Esc`） | `Esc` |

规则：

- 高度约 24–26px，字 11px，圆角 6px——贴合 37px panel-head，不撑破 accordion  
- Halt 不用「STOP THE WORLD」长文案上按钮（横幅/节点再说）  
- `world-stopped` 时：Halt 可保持可见（幂等）；场景钮禁用；Steer 禁用  

## B · Demo 场景（顶栏）

- 顶栏背景改为 **slate-100 / 白**，不再黑条操作系统感  
- 场景钮：统一 `ghost`——灰字、细边框；**当前正在回放**可用 brand 细边高亮  
- 文案短：`S1 合法` · `S2 闸门` · `S3 返工` · `重置`  
- 左侧小字标注 `harness · 非产品`

## C · Modal

- `取消`：ghost  
- `确认纠正并提示 Main`：实心琥珀（唯一主 CTA）  
- 勿再放第三颗红色大钮  

## 色义（克制）

| 色 | 用途 |
|----|------|
| brand blue | 仅场景「进行中」描边，或 prod 主 CTA（非本面板） |
| amber | 换向 / steer |
| red | 仅 Halt + 失败证据 |
| gray ghost | 一切次要 |

不用彩虹：S1/S2/S3 不再各染一色实心。

## React 落地映射

| Demo | prod |
|------|------|
| `.panel-head .btn-steer` / `.btn-halt` | `ExecutionPathPanel` 标题行右侧 |
| `.demo-bar` 场景钮 | **不进 prod**（E2E fixture / storybook） |
| Modal 确认 | 现有 dialog 模式即可 |

Demo 实现见 [demo-observability.html](./demo-observability.html)。
