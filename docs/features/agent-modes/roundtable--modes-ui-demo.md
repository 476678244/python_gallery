# 圆桌：Agent Modes UI / Demo 应如何成立？

> 用 **ljg-roundtable** 方法论讨论设计，不是给 ljg-roundtable 做产品 UI。  
> 现场材料：[`demo-modes.html`](./demo-modes.html)、[`methodology.md`](./methodology.md)、prod slash（`commands.ts`）与 session model。

#+filetags: :roundtable: :agent-modes:

## 议题与参会者

**议题**：SafeClaw 的 `/ask` `/agent` `/plan` `/loop`——在个人自用 + Fail Fast 前提下——应以何种形态出现在会话与 Demo 中？

| 人物 | MBTI | 核心立场 | 选择理由 |
|------|------|----------|----------|
| 唐纳德·诺曼 (Don Norman) | INFJ | Mode 必须是可感知状态：用户随时知道「现在允不许写」；看不见的 mode = 模式错误温床 | 《设计心理学》；mode error 经典议题 |
| 弗雷德·布鲁克斯 (Fred Brooks) | ISTJ | 概念完整性：mode 寄生已有「会话级 settings」（同 model），禁止第二种全局开关系统 | 《人月神话》；拒第二套配置平面 |
| 娜拉·尼尔森 (Jakob Nielsen) | INTP | 防错优先：Ask/Plan 须硬门禁可见；软 prompt「请勿写入」不算可用性 | 十大启发式：防错、状态可见、用户控制 |
| 杰罗姆·萨尔策 (Jerome Saltzer) | INTJ | 最小权限：只读 mode = 工具未授予，不是模型「自觉」；Fail Fast 对齐安全原则 | Saltzer–Schroeder；least privilege |
| 李继刚 | ENFP | **意外视角**：四 mode 是结构体裁而非四个按钮皮肤；Loop 是时间结构、Plan 是框架结构，须在 Demo 露出骨相 | 圆桌剑意：结构可视化 / 求真 |

---

## 开场：定义

【主持】：感谢各位。现场已有：四 mode 合同、会话级粘性、`demo-modes.html`（prod 壳 + 策略芯片 + 四并列剧本）。核心议题为——Agent Modes 的 UI / Demo 应如何成立。

【主持】：在深入之前，我们应当如何定义「会话 Mode」？它的核心要素是什么？

【唐纳德·诺曼】【陈述】：Mode 是系统状态的用户可感知切片。核心要素只有三样：当前是什么、能做什么、如何退出。Badge 若只是装饰色块而侧栏策略与 Exec 闸门对不上，那是假反馈——比没有 mode 更糟。

**简言之**：Mode = 可核对的能力边界状态。

【杰罗姆·萨尔策】【补充】：诺曼说「能做什么」，我把它钉成机制：Ask/Plan 下写工具必须未注册或调用即失败。定义里若只含 UI 词汇而无权限集合，这不是 mode，是皮肤。

**简言之**：Mode 定义含权限集合，否则无效。

【弗雷德·布鲁克斯】【质疑】：别把 Mode 做成第五个产品。你们已有 SessionSettings.model。Mode 的定义应是：**同构于 session model 的策略枚举**——粘在会话、slash 切换、New Chat 默认 agent。另起全局 `agent_config.mode` 就是第二种系统。

**简言之**：Mode ⊂ 会话 settings，拒绝全局双轨。

【娜拉·尼尔森】【综合】：同意会话粘性。再补防错：从 Agent 切到 Ask 必须立刻改变可观察结果（blocked chip / 无 write），否则用户学不会边界。Loop 的 Stop 同理——调度状态必须可见且可取消。

**简言之**：切换必有即时、可学的边界反馈。

【李继刚】【补充】：你们在定义「开关」，我在定义「体裁」。Ask 是问答体，Plan 是框架体（步骤/风险），Loop 是节拍体（tick），Agent 是行动体。Demo 若四个剧本都长成同款气泡 + 换个 badge 颜色，结构死亡——合同写了四个一等公民，画面却只有一个体裁。

**简言之**：四 mode = 四体裁，不是四染色。

---

## 第 1 轮：Mode 的「家」在哪里？

【主持】：定义张力已现——可感知边界、最小权限、会话同构、即时反馈、四体裁。请交锋：Mode 的主战场应是输入区 slash+badge，还是右侧 Exec/策略面板，或必须三者同构？

【弗雷德·布鲁克斯】【陈述】：家在 SessionSettings；门面是 slash（与 `/model` 同族）。Exec 只汇报本回合闸门结果，不拥有 mode 所有权。否则出现「Exec 显示 ask、session 仍是 agent」的概念分裂。

**简言之**：所有权在 session；slash 是门；Exec 是证言。

【唐纳德·诺曼】【反驳】：所有权归 session 可以，但用户眼睛不读 settings 对象。第一眼必须在 Chat 头 / 输入区看到 badge。Demo 侧栏 Tool policy 有教育价值，落地时若与 badge 冲突，用户信哪一个？合同应写：badge 与请求 `mode` 与闸门结果三者同构，侧栏可折叠为 Inspect。

**简言之**：可见主锚在 badge；侧栏不得另立真相。

【娜拉·尼尔森】【补充】：Ask 剧本里 Exec 出现 `safe_claw_file_write · blocked` 是防错教材，必须保留进产品——不是 Demo 特权。没有这次失败可见，用户会以为「我说了别写」就安全了。

**简言之**：硬拒绝要进 Exec，证明门禁不是文案。

【杰罗姆·萨尔策】【质疑】：尼尔森要可见拒绝，我担心「拒绝」做成模型道歉而工具仍在。Demo 写了 gate 节点——好。落地验收必须断言工具列表，不只断言气泡说「未写入」。

**简言之**：验收盯工具集，不盯道歉。

【李继刚】【综合】：家可以在 session，但 Plan 的「家」还得有主区结构块——否则 Plan  degenerate 成 Ask。Loop 的家在调度条（interval / next tick / Stop），挂在 Exec 下沿即可，不必新 App。四体裁共享壳，分形露出骨。

**简言之**：共享 session 壳；Plan/Loop 要专用结构骨相。

【主持】：本轮核心争议点在于——

> **Mode 的权威真相只有一份（SessionSettings），但用户可感的「家」应落在 badge，还是必须强制 Exec 闸门证言与 Plan/Loop 结构块同时在场？**

```
              SessionSettings.mode
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
      slash门       badge锚      Exec证言
     (Brooks)     (Norman)     (Nielsen/
                                Saltzer)
                       │
              Plan 框架 / Loop 节拍
                   (李继刚)
                       │
         禁止：侧栏策略与 badge 双真相
```

【主持】：下一层问题：

> Demo 已用四并列 harness 按钮回放剧本——落地时是否应删除「场景按钮」心智，只保留 slash 切换 + 真实发送，以免用户以为 Mode 是「演示档」而非会话状态？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 第 2 轮：对着 Demo 四剧本继续

【主持】：用户指令按 **可** 推进——请就 `demo-modes.html` 四剧本的**眼睛可见结构**发言，勿空谈合同。

【爱德华·塔夫特】——（本轮未入席；改由在场者就信息诚实发言。）

【杰罗姆·萨尔策】【陈述】：点 Ask：侧栏写文件=禁止，Exec 出现 write blocked，主区声明未写入——三角一致，这是诚实的最小权限演示。点 Agent：write ✓——对照成立。信息墨水花在「允许集差异」上，而不是花在装饰。

**简言之**：Ask↔Agent 对照成立；门禁可教。

【唐纳德·诺曼】【补充】：Plan 剧本出现紫色 Plan artifact（步骤+风险）——体裁终于不同于 Ask，心智上「我在规划」成立。但顶部 harness 四按钮与 slash 面板功能重复：用户会以为有两套切换。落地应扔掉 harness，只留 slash；Demo 可保留 harness 并标明非产品。

**简言之**：Plan 骨相过关；双切换入口需收敛。

【弗雷德·布鲁克斯】【反驳】：诺曼，harness 在 Demo 标明「非产品」即可，不必道德清洗。我更担心 Loop：剧本把 session mode 留在 agent，又渲染 loop 策略卡——好，合同说 loop 不改写 mode。但 badge 仍显示 agent 时，侧栏标题写「loop（调度）」——新手可能以为 mode 变成了 loop。命名上 loop 是调度器不是第五执行 mode——Demo 文案要更狠：`scheduler · inherit agent`。

**简言之**：Loop≠第五执行 mode；文案防概念漂移。

【娜拉·尼尔森】【质疑】：Loop 的 Stop 在 Exec 下沿——对。但 5s tick 在 Demo 里会一直刷助手气泡，主区变节拍垃圾场。产品要：tick 摘要进 Exec，主区只留关键变更或可折叠「loop log」。否则可用性被自己的心跳淹死。

**简言之**：节拍证据进 Exec；主区禁止 tick 洪水。

【李继刚】【综合】：四剧本并列本身就是圆桌式结构——Ask 拒绝、Agent 写入、Plan 框架、Loop 节拍，并置才见骨。塔夫特式「可比较」在 harness 一排按钮上成立。落地失去 harness 后，比较能力应转移：会话内可回看「上次在 plan 产出的 artifact」与「agent 执行后」——灰显或钉住 plan 卡，而非滚走消失。

**简言之**：并列比较要迁入会话时间线，不随 harness 死。

【唐纳德·诺曼】【修正】：同意钉住 plan 卡。再补：New Chat 默认 agent 正确——避免惊吓；但从满权限切到 ask 的确认不必 modal（个人自用），badge 变色 + 一句 slash notice 足够，多一层对话框是仪式噪音。

**简言之**：默认 agent；切换用轻反馈，勿 modal 盖头。

【主持】：本轮（Demo 实见后）核心争议收束为——

> **落地时扔掉 harness 场景按钮之后，如何保留「四体裁可比较」与「Loop 不冒充执行 mode」，并避免 tick 洪水破坏主区？**

```
        Demo 四剧本并置 (可比较)
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
 Ask/Agent门禁  Plan骨相    Loop节拍
 三角一致      artifact     inherit≠mode
 (Saltzer赞)  (Norman赞)   (Brooks钉名)
                 │
                 ▼
      落地：仅 slash + badge (扔 harness)
      Plan 卡钉住可对照 (李继刚)
      Tick → Exec；主区防洪水 (Nielsen)
      切换轻 notice，无 modal (Norman)
```

【主持】：下一层问题：

> React 第一刀是否应为：`SessionSettings.mode` + slash 四命令 + header badge 同构传给 `/chat/stream`，并以 Ask 工具剥离单测为门禁——Plan 卡片与 Loop 调度放第二刀？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 第 3 轮：除四 mode 外，还缺什么 Mode？

【主持】：用户指令转向**讨论现有 mode 集合是否完备**——不急着钉 React 第一刀。请就「还需要哪些 mode」交锋。候选常被点名：`/debug`、`/review`（审代码）、`/explore`（只调研可 spawn）、`/yolo`（少确认）、`/teach`。先定义：什么资格配称「一等 Mode」，什么只该是开关或体裁皮肤？

【弗雷德·布鲁克斯】【陈述】：概念预算极紧。已有 ask / agent / plan，外加 loop 这个**调度器**（上轮已钉：非第五执行 mode）。再加 debug/review/explore/yolo，用户要记的状态空间爆炸——这是第二种系统的温床。缺的不是 mode，是 agent 内的**策略旋钮**（是否自动确认、是否允许 spawn）。

**简言之**：四已满；再增是概念通胀。

【杰罗姆·萨尔策】【补充】：同意少枚举。权限应是轴，不是名：`read | write | execute | spawn | memory_write`。Ask/Plan 是只读配置档；Agent 是满配。所谓 `/explore` 若只是「只读 + 允许 explore spawn」，它是 **ask 的权限变体**，不配新 badge——否则 Saltzer 原则被「每个用例一个 mode」稀释。

**简言之**：用权限档位，勿用用例名堆 mode。

【唐纳德·诺曼】【质疑】：轴很干净，但用户不读权限矩阵。他们认名字：Ask、Plan。问题是 mode 过多导致 **mode error**——以为在 Ask 却在 Agent。四已经在边界；再加 Debug/Review，切换成本与误操作风险上升。若某能力极少用，宁可 slash **动作**（`/review 这段 diff` 跑一轮审阅 skill）而非粘性 mode。

**简言之**：粘性 mode 宜少；偶发能力用动作，勿新粘性态。

【娜拉·尼尔森】【反驳】：诺曼把 `/review` 降成动作可以，但 **Debug** 有持续状态需求：复现→假设→探针→收敛，很像 Plan 的「框架体」却工具集不同（要跑测试、看日志）。若强塞进 Agent，用户失去「我在排障、请少重构」的防错边界。或许不配第五 badge，但配 **Agent 子策略** `agent:debug`——仍一个 badge 色，Exec 显示 profile。

**简言之**：Debug 要防错边界；优先子策略，慎新顶层 mode。

【李继刚】【综合】：听骨相，不听品牌。现有四体裁覆盖：问答 / 行动 / 框架 / 节拍。审代码是「框架+只读」→ Plan 或 Ask 的特化提示，不是新维度。探索调研是「问答+可委派」→ 权限轴上的 spawn 位。YOLO 是确认策略，连体裁都不是。真可能缺的维度只有一个：**人机共驾密度**——每步确认 vs 长跑——那是 harness 旋钮，挂在 Agent 上，别叫 mode。

**简言之**：体裁已齐；缺的是 Agent 上的共驾旋钮，不是新 mode 名。

【杰罗姆·萨尔策】【修正】：李继刚的「共驾密度」若做成静默 YOLO，违反 Fail Fast 透明。应显式：`require_confirm: true|false`，默认 true（或保持今日 prompt 确认习惯），UI 可见——仍不是 `/yolo` mode。

**简言之**：YOLO→显式确认开关；禁止伪装成 mode。

【弗雷德·布鲁克斯】【综合】：共识草案：顶层执行 mode 维持 **ask | agent | plan**；**loop = 调度**；不新增 debug/review/explore/yolo 为 badge。Explore spawn 进 ask/plan 权限表（methodology 已留 explore-only）；Debug/Review = agent profile 或单次动作；确认策略独立字段。概念完整性保住。

**简言之**：顶层三执行 + 一调度；其余降维为轴/动作/profile。

【主持】：本轮核心争议点在于——

> **产品压力会诱使「一场景一 mode」；圆桌倾向把完备性放在权限轴与 Agent 子策略上，而非扩充 badge 枚举——那是否足以覆盖 Debug / Review / Explore，还是将来仍要破例升格某一个？**

```
        用例诱惑 (debug/review/explore/yolo)
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
      新 badge      权限轴/档位    单次动作
     (拒·Brooks/   (Saltzer主)   (Norman)
      Norman)            │
                         ▼
              ask|agent|plan  +  loop调度
                         │
              agent:debug profile (Nielsen可)
              require_confirm 旋钮 (李/Saltzer)
              explore spawn ⊂ ask/plan 轴
```

| 候选 | 圆桌结论 | 落点 |
|------|----------|------|
| ask / agent / plan | **保留** 顶层执行 mode | SessionSettings.mode |
| loop | **保留** 调度器，非执行 mode | scheduler · inherit |
| explore | **不升格** | ask/plan 上 `spawn=explore-only` |
| debug | **不升格**（可后置） | `agent` profile 或提示词档 |
| review | **不升格** | 单次动作 / skill / plan 特化 |
| yolo / auto | **不升格** | `require_confirm` 显式开关 |
| teach / explain | **不升格** | ask 体裁 + 提示 |

【主持】：下一层问题：

> 是否把上述「不再扩充顶层 mode」写入 methodology 的明确非目标，并加一节「权限轴 / profile」，以免后续 PR 以 Cursor 对标为由偷加 `/debug` badge？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 第 4 轮：用户修订 — 喜欢 Debug，且 = 打开全部可观测

【主持】：用户指令——**I like debug mode. 对应打开所有的可观测选项。** 这不是「再议要不要 debug」，而是修订合同：Debug 升格，且主语义绑定 Observability Full pack。请表态，勿再劝退 debug badge。

【娜拉·尼尔森】【陈述】：接受。上轮我把 debug 降成 profile，是怕 badge 通胀；用户把它钉在「全开观测」上，防错价值立刻清晰——排障时状态可见是启发式正中红心。badge 显示 debug，右侧 Exec / Prompts / Skills 全展开，比藏在设置里的十个 checkbox 可学。

**简言之**：Debug = 可观测全开；接受顶层 badge。

【杰罗姆·萨尔策】【补充】：工具权限与 agent 同档，观测是正交强制态——可以。但合同必须写清 Full pack 清单（Exec、嵌套、Prompt Inspect、Skills、闸门证据、Halt/Steer、SSE 不丢事件）。禁止「debug」只换颜色、面板仍折叠。

**简言之**：同权 agent + 强制观测清单；禁止空壳 badge。

【唐纳德·诺曼】【修正】：同意。切进 `/debug` 必须瞬间看见面板变化（映射：我开了观测）。切到 `/agent` 必须能安静回来——否则 mode error：以为还在安静 agent，实际仍全开噪音。

**简言之**：切入可见全开；切出必须解除强制。

【弗雷德·布鲁克斯】【质疑】：概念完整性：loop 仍是调度；debug 是第四执行 mode（ask/plan/agent/debug）。不要再发明 `agent:debug` 双轨。Demo 与 methodology 只认一个枚举。

**简言之**：debug ∈ 执行 mode 枚举；拒绝双轨 profile 名。

【李继刚】【综合】：体裁上 Debug 是「透视图」——把骨架外翻。与 Plan 的框架体、Loop 的节拍体并列：不是第五染色，是观测体裁。Demo 应加 Debug 剧本：一点击，三面板齐开 + Exec 深挖。

**简言之**：Debug = 透视体裁；Demo 要演「全开」。

【主持】：本轮收束——

> **`/debug` 升格为会话执行 mode：工具同 agent；硬绑定 Observability Full pack；切出解除强制。explore/review/yolo 仍不升格。**

已写入 [methodology.md](./methodology.md) §4 Debug、§5 Full pack、§7 修订表。

```
     用户修订
         │
         ▼
   /debug 顶层 mode
         │
    ┌────┴────┐
    ▼         ▼
 工具=agent  观测=Full pack
              (强制开)
         │
         ▼
  切出 ask/agent/plan → 解除强制
```

【主持】：下一层问题：

> Demo 是否立即加第五并列剧本 Debug（一点击三面板全开 + 深 Exec），并作为 React 验收的视觉合同？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 第 5 轮：用户修订 — 还需要 Subagent 强制打开的 mode

【主持】：用户指令——**还需要 subagent 强制打开的 mode。** 与 `/debug` 并列：不是把 subagent 塞进 Full pack 就完事，而是要有**专用会话 mode**，强制打开子代理可观测面。请修订，勿劝退。

【弗雷德·布鲁克斯】【陈述】：接受第二个观测向 mode，但概念上要切开：`debug` = 全局透视；`subagent` = 委派透视。枚举写成 `ask|agent|plan|debug|subagent`，外加调度 `loop`。命名上 `AgentMode.subagent` 与 SSE `step_type=subagent` 必须分命名空间，否则第二种系统从变量名开始。

**简言之**：独立 mode；与 step_type 隔离命名。

【娜拉·尼尔森】【补充】：用途清晰——用户要看主/子树、闸门、Halt/Steer，却不想被 Prompt Inspect / Skills 三面板同时砸脸。`/subagent` 只强制 Subagent pack；`/debug` 才 Full。防错：spawn 在此 mode **必须启用**，否则 badge 撒谎。

**简言之**：窄观测包 + spawn 必开。

【杰罗姆·萨尔策】【质疑】：强制「打开观测」不等于放宽 brief 硬闸门。`/subagent` 不得变成「免 look_ahead 也可 spawn」。最小权限在委派质量上仍由 sub-agents 闸门守门。

**简言之**：观测全开 ≠ 闸门放水。

【唐纳德·诺曼】【修正】：切入 `/subagent` 第一眼应是 Exec 展开 +（有委派时）子块外翻；切回 `/agent` 解除强制。与 debug 切换矩阵写进合同，避免「从 debug 切到 subagent 后 Inspect 仍钉死打开」。

**简言之**：切入见子树；切出解除；与 debug 交接要干净。

【李继刚】【综合】：体裁上这是「委派剧场」——look_ahead / 换向 / 旧树灰显是骨相。Demo 应有独立剧本：武装 subagent mode → 合法委派子树默认展开 → 不必开 Prompts。与 debug 剧本并置比较，用户才懂两个强制开的差别。

**简言之**：委派体裁独立剧本；与 debug 可对照。

【主持】：本轮收束——

> **`/subagent` 升格：工具同 agent + spawn 必开 + Subagent Observability pack；不强制 Full pack；不放宽 spawn brief 闸门。**

已写入 [methodology.md](./methodology.md) §4 Subagent、§5b、§7。

```
        /debug                    /subagent
     Full pack                 Subagent pack
   (含嵌套观测)          Exec+子树+闸门+Halt/Steer
         │                        │
         └──────── spawn ─────────┘
              (均允许；subagent 必开)
         │
         ▼
   brief 硬闸门仍归 sub-agents（不放水）
```

【主持】：下一层问题：

> Demo 是否同时加 **Debug** 与 **Subagent** 两个并列剧本，并在侧栏标明 Full pack vs Subagent pack 差异？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 第 6 轮：用户修订 — Safe mode（克制写，禁改删）

【主持】：用户指令——**再加一个 safe mode：在保证安全的前提下允许克制的写操作，但不允许 delete/remove/update。** 请修订合同。

【杰罗姆·萨尔策】【陈述】：这正是最小权限中间档：Ask=零写，Safe=create-only，Agent=满写。`update` 与 `delete` 是破坏性轴；`create` 在隔离工作区相对可逆（仍可能填满磁盘，故要 size 上限——backend 已有）。门禁必须在 FS：`allow_edit=False`、`allow_delete=False`、`write` 仅新建。Prompt 说「请勿修改」不算数。

**简言之**：Safe = create-only 硬档；禁 edit/delete。

【娜拉·尼尔森】【补充】：用户心智：Ask 看、Safe 添、Agent 改。侧栏芯片应三色对照：create ✓ / update ✗ / delete ✗。Demo 剧本：新建成功 + 覆盖已存在文件失败 + edit 被拒——否则学不会边界。

**简言之**：三态芯片 + 失败可见。

【弗雷德·布鲁克斯】【质疑】：概念上 Safe 是权限档，不是观测档——与 debug/subagent 正交维度。枚举继续膨胀，但语义轴清晰（权限 vs 观测）。接受，条件是矩阵表把「新建写 / update / delete」拆列，禁止再用含糊的「写文件=是/否」。

**简言之**：拆列写权限；Safe 入枚举。

【唐纳德·诺曼】【修正】：命名 `/safe` 好懂。风险：用户以为 safe=完全只读。Badge 旁短文案或 notice：「可新建，不可改删」。从 plan → safe 是自然路径（审完计划后只准落新文件）。

**简言之**：防「safe=只读」误读；plan→safe 路径成立。

【李继刚】【综合】：体裁是「添纸不改稿」。与 Ask 的静、Agent 的动手、Plan 的框架并列。Skill execute 若无法证明不改删，应 Fail Fast——宁可不跑，不可假装克制。

**简言之**：添纸体裁；技能越权即失败。

【主持】：本轮收束——

> **`/safe` 升格：读 + 新建写；禁 update/edit、delete/remove；skill 克制且受 FS 门禁；无 spawn；无强制观测 pack。**

已写入 [methodology.md](./methodology.md)。

```
   写权限光谱
   ask ─── safe ─────────── agent/debug/subagent
   零写    create-only      新建+改+删*
              │
              ├─ update ✗
              └─ delete ✗
```

【主持】：下一层问题：

> Demo 是否增加 Safe 剧本（新建 ✓ / 覆盖 ✗ / edit ✗），并与 Ask、Agent 三列对照策略芯片？

【主持】：(指令: 可 / 止 / 深入此节 / 引入新人物)

---

## 主持附记：Design & Plan 已沉淀（非发言轮）

用户指令 **design and plan** 后，已写入：

- [design.md](./design.md) — ModePolicy、两轴（权限/观测）、数据流、UI/后端接线  
- [plan.md](./plan.md) — Phase 0→F（Demo 补齐 → API → UI → 观测 pack → Plan → Loop → 有头验收）  
- [milestones.md](./milestones.md) — M0–M6  

圆桌未正式「止」；若需知识网络终章，发指令 **止**。

---

## 附：与现场 Demo 的映射（非发言）

| 圆桌主张 | Demo 已有 | 落地注意 |
|----------|-----------|----------|
| Session 粘性 | badge + SessionSettings 文案 | 真写入 session store |
| 硬门禁可见 | Exec gate / blocked chips | API 剥工具，勿只 prompt |
| 四体裁 | 四剧本内容形态不同 | Plan 卡、Loop 调度条进 prod |
| Loop≠mode | 策略卡写「继承」 | badge 保持 ask/agent/plan |
| harness 非产品 | 顶栏已标 Harness | 实现勿复制场景按钮为唯一入口 |
