# 圆桌：Subagent 可观测性 UI Demo 应如何设计？

> 用 **ljg-roundtable** 方法论讨论设计，不是给 ljg-roundtable 做产品 UI。  
> 现场材料：`demo-observability.html`、`methodology.md`、prod `right-panel` Execution Path。

#+filetags: :roundtable: :sub-agents:

## 议题与参会者

**议题**：SafeClaw 的 Subagent 可观测性 UI Demo——在个人自用 + Fail Fast 前提下——应以何种形态成立？

| 人物 | MBTI | 核心立场 | 选择理由 |
|------|------|----------|----------|
| 唐纳德·诺曼 (Don Norman) | INFJ | Demo 的「可感」= 用户心智模型与系统状态对齐；看不懂的观测等于没有 | 《设计心理学》；可观测性首先是 affordance / 反馈 |
| 爱德华·塔夫特 (Edward Tufte) | INTJ | 信息密度与诚实：默认展开须服务于比较与因果，禁止装饰性仪表盘 | 数据墨水；反对 chartjunk——暗色炫技壳已被否决 |
| 弗雷德·布鲁克斯 (Fred Brooks) | ISTJ | 概念完整性：Demo 必须长在 prod Exec 上，另起皮肤是第二种系统 | 《人月神话》；架构一致性 |
| 娜拉·尼尔森 (Nielsen) | INTP | 启发式：状态可见、用户控制、防错；硬闸门与 Stop/Steer 是可用性不是奢侈 | 十大可用性启发式；意外但贴合「个人可打断」 |
| 李继刚 | ENFP | **意外视角**：圆桌本身证明——结构（争议/框架/指令）比长文气泡更能「感测」；Demo 应露出结构而非只堆步骤 | 圆桌剑意：求真与结构可视化 |

---

## 开场：定义

【主持】：感谢各位。核心议题为「Subagent 可观测性 UI Demo 应如何设计」。现场已有：prod 壳 Demo、硬闸门「看三步」、双通道隔离、STOP / 纠正方向。

【主持】：在深入之前，我们应当如何定义「可感测的 Subagent UI」？它的核心要素是什么？

【唐纳德·诺曼】【陈述】：可感测不是「把日志摊开」。是用户能回答：谁在跑、为何委派、前瞻是什么、失败被谁拦住、主线程吃进了什么。若答案只存在于开发者脑中，Demo 失败。

**简言之**：可感测 = 心智模型可核对的状态。

【爱德华·塔夫特】【补充】：同意核对，但反对用皮肤制造「感觉有监控」。默认展开三步与 nested tools，只有在能并置比较（旧方向 vs 换向后、闸门失败 vs 成功）时才配称信息。否则是噪音的慷慨。

**简言之**：展开必须可比较，否则是噪音。

【弗雷德·布鲁克斯】【质疑】：两位先别谈密度。若 Demo 不长在 prod Execution Path 的点线 chips 合同上，你们讨论的是另一款产品。概念完整性优先于观测美学。

**简言之**：先寄生 prod，再谈感测。

【娜拉·尼尔森】【综合】：完整性与可核对之外，要有控制权：Stop、纠正方向、硬闸门失败可见——这是防错与用户控制。个人自用不是借口做只读仪表盘。

**简言之**：可见 + 可打断 + 防冒进。

【李继刚】【补充】：你们谈组件，我谈体裁。圆桌若只回落成 chat 长文，结构死亡。Subagent Demo 的「感」应像主持综述：争议、框架、指令——Exec 里的 sub-block / look_ahead 就是微型框架图。

**简言之**：感测靠结构体裁，不靠话多。

---

## 第 1 轮：Demo 的主战场在哪里？

【主持】：定义张力已现——心智核对、信息诚实、prod 寄生、可打断、结构体裁。请直接交锋：Demo 的主战场应是右侧 Exec 重构，还是主区圆桌式舞台？

【弗雷德·布鲁克斯】【反驳】：主区圆桌舞台是第二种系统。用户日常仍在 Chat+Exec；Demo 若教育另一套布局，落地时必撕裂。主战场只能是 `ExecutionPathPanel` 的嵌套与 brief 块。

**简言之**：主战场 = prod Exec，拒绝第二布局。

【李继刚】【质疑】：Exec 时间线擅长「步骤」，不擅长「张力」。若可感测包含「为何换向、争议何在」，纯点线会把圆桌式结构压扁成工具列表。可以寄生壳，但主区需要结构块——至少在 Demo 里。

**简言之**：壳可 prod，舞台不能只有点线。

【唐纳德·诺曼】【反驳】：李继刚要的结构，可以是 Exec 内的 sub-block（step_now / ①②③ / expected），不必新主区。用户已有「往右看执行」的习惯；再开舞台增加映射成本。

**简言之**：结构嵌进 Exec，勿新心智地图。

【爱德华·塔夫特】【补充】：同意嵌进 Exec。但当前 Demo 顶部 harness 条是诚实的——它标明「非 prod」。危险的是 harness 控件（S1/Stop）将来进 UI 时变成第三套 chrome。合同应写清：harness 可扔；Exec 嵌套合同不可扔。

**简言之**：扔掉 harness，留下 Exec 合同。

【娜拉·尼尔森】【修正】：Stop / 纠正方向不是 harness 玩具，是可用性控件，必须进 prod 某处（Exec 头或 Chat 顶）。否则「可打断」只在 Demo 成立。

**简言之**：急停与换向要进产品面，不是 Demo 特权。

【主持】：本轮核心争议点在于——

> **可感测的结构，应嵌在 prod Exec 时间线内，还是需要主区「舞台」级体裁？**

```
                 概念完整性 (Brooks)
                        │
          嵌进 Exec ─────┼───── 主区舞台
         (Norman/Tufte)  │    (李继刚)
                        │
              可打断控件必须进产品 (Nielsen)
                        │
              harness 可弃 / 合同不可弃 (Tufte)
```

【主持】：下一层问题：

> 若坚持「只改 Exec、不新主区」，`look_ahead×3` + nested tools 默认展开，在信息密度上如何避免塔夫特所说的噪音，又满足诺曼的可核对？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 第 2 轮：对着 Playwright 实拍继续

【主持】：用户指令相当于 **可**——我们打开 headed Playwright，回放了 S1 / 纠正方向 / STOP / S2 闸门，截图在 `~/Downloads/safe_claw_worksapce/workspace/subagent-demo-shots/`（`02-s1-done` `03-steer` `04-stop` `05-gate-fail`）。请就**眼睛看见的界面**发言，勿空谈。

【爱德华·塔夫特】【陈述】：看 `02-s1-done`。右侧 Exec 的信息墨水大多花在该花的地方：sub-block 里 `step_now` / `expected` / 三条 look_ahead，nested `web_search` 与 `self_correct` 可并置。这比左侧 Channels 那串 SSE 复读有用。左侧「观测通道」与 Exec **双重叙述同一故事**——这是 chartjunk 的近亲：同一因果讲两遍，密度假象。

**简言之**：Exec 子块成立；左侧 SSE 清单与 Exec 重复，应降级或折叠。

【唐纳德·诺曼】【补充】：同一帧里我能回答：谁在跑（general-purpose）、前瞻三条、主聊只有最终摘要、nested 被拒进主 messages。心智核对通过。但顶部深色 harness 抢走第一眼——用户会以为 SafeClaw 本体就是黑条工具箱。映射错误：壳声称 prod，第一像素却是 Demo 操作系统。

**简言之**：核对成功；harness 抢戏，破坏「这是 prod」的第一印象。

【弗雷德·布鲁克斯】【反驳】：诺曼，harness 可以丑，只要边界诚实。截图右上写着对齐 ChatLayout+Execution Path——点线、chips、`✓ done`、rail 上的 Exec/Skills/Prompts，这是概念完整性。我担心的是左侧又塞了 Channels 卡片：prod Sidebar 不是这么用的。Demo 在教错误的 Sidebar 语义。

**简言之**：右侧像 prod；左侧 Channels 污染 Sidebar 合同。

【娜拉·尼尔森】【质疑】：看 `05-gate-fail`：红框 Fail Fast、`blocked` chip、主聊一句话说清「未启动」——防错启发式满分。再看 `04-stop`：红条 + Exec 里 STOP 节点 + 现场 look_ahead 仍在——状态可见、可恢复（重置）。但 Stop/Steer **只活在 harness**：若扔掉黑条（塔夫特/诺曼所望），控件无家可归。可用性要求：在截图的 Execution Path 标题行放 Halt/Steer，而不是永远挂在 Demo 顶栏。

**简言之**：闸门与急停「看得懂」；控件必须迁入 Exec 头，否则落地蒸发。

【李继刚】【综合】：`03-steer` 最像圆桌体裁——黄条 REDIRECT、主区 `[USER_STEER]`、Exec 出现 `USER REDIRECT` 再 `换向后再看三步`。张力被结构标出，不是埋在工具列表。这证明：不必另起主区舞台，**换向事件本身就是舞台高潮**，嵌在时间线即可。塔夫特要的「可比较」也在：换向前 subagent 卡与换向后新实例可上下对照——若 Demo 滚走旧节点就输了；应保留灰显的旧 sub 树。

**简言之**：换向帧已是结构剧场；旧树应灰显保留以便对照。

【唐纳德·诺曼】【修正】：同意李继刚的灰显对照。再补一条：`02` 里主聊极干净是对的；但用户若只看主区，会错过闸门失败细节——`05` 幸好 Exec 与聊都有。合同应是：主区一句话 + Exec 展开证据，两者分工，不是双份全文。

**简言之**：主区摘要 / Exec 证据，禁止双份倾倒。

【主持】：本轮（实拍后）核心争议收束为——

> **左侧 SSE Channels 与顶栏 harness 是否应退出「假 prod」画面，把可感测合同收束到：主区摘要 + 右侧 Exec 嵌套（含灰显对照）+ Exec 头上的 Stop/Steer？**

```
        眼见为实 (Playwright)
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
 Exec子块成立   左SSE重复    harness抢戏
 (Tufte赞)    (Tufte/Brooks剔) (Norman剔)
                 │
                 ▼
      Stop/Steer 迁入 Exec 头 (Nielsen)
      换向旧树灰显对照 (李继刚)
      主区摘要 ≠ Exec 证据 (Norman)
```

【主持】：下一层问题：

> 落地 React 时，第一刀是否应为：删掉 Demo 专属左侧 Channels、把 Halt/Steer 钉进 `Execution Path` 面板头，并实现「redirected 旧 sub 树灰显保留」？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)
