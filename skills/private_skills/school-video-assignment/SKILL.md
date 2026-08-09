---
name: school-video-assignment
description: 把孩子在家录的口播视频（宣讲、演讲、朗诵、课题讲解）做成可提交的学校视频作业——用实景配图替换家里的背景，按逐字稿剪掉卡壳重录、修音频、卡提交规格。Use when a school video assignment must be produced from a home recording, when the family cannot shoot on location (weather, time, distance), when the user mentions 视频作业/宣讲视频/换背景/抠像/配图合成/红领巾/实景地标, or when a recorded speech needs NG takes trimmed and background stills aligned to what the child actually says.
category: media
tags:
  - video
  - school-assignment
  - matting
  - compositing
  - transcript
  - asr
  - audio-repair
  - ffmpeg
  - rvm
aliases:
  - 视频作业
  - 宣讲视频
  - 换背景
  - 抠像合成
  - school-video
argument_hint: "[recording.mp4] [背景图目录]"
user_invocable: true
auto_trigger: false
---

# 学校视频作业：家里录的口播 → 实景配图成片

## 适用场景

学校布置视频作业，要求「实景拍摄某地标 / 穿红领巾 / MP4 / 5 分钟内 / 200M 内」，但因为天气、距离或时间去不了现场。做法是：**在家录人，用实景照片当背景，抠像合成**。

顺带解决家庭录制的通病：孩子讲错了当场重录但没剪、停顿占三分之一时长、手机收音又轻又吵。

**核心方法：先转写，再对症。** 不要凭印象看片子找问题——先拿到带时间戳的逐字稿，卡壳、重录、念错、废停顿会自己浮出来，配图切换点也才能对准讲词。

---

## Step 0 · 先把提交规格问清楚

动手前确认，否则做完要返工：

```
- [ ] 格式与体积上限（常见：MP4 / ≤5 分钟 / ≤200 MB）
- [ ] 着装要求（红领巾、校服）—— 录之前就要穿好，事后补不了
- [ ] 是否必须「实景出镜」—— 若明文要求本人在现场，抠像合成不合规，别做
- [ ] 是否要求出现指定地标 / 主题词（如「光荣之城」）
- [ ] 配图能否说明来源（学校作业通常要能交代出处）
- [ ] 截止时间 —— 决定还来不来得及补录
```

第 3 条最关键。若只要求「体现某地标」，用该地标的照片当背景是可以的；若要求「本人在地标前实拍」，就只能实地补拍。**拿不准就问用户**。

---

## 环境

```bash
conda run -n rvm_matting python -c "import torch, cv2; print('ok')"   # 抠像+合成
conda run -n safe_claw   python -c "from funasr import AutoModel"      # 转写
ffmpeg -version | head -1
```

抠像依赖 RobustVideoMatting（本机已在 `~/Downloads/speech_composite/`）：

```bash
git clone https://github.com/PeterL1n/RobustVideoMatting
curl -LO https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50.pth
export RVM_REPO=/path/to/RobustVideoMatting
export RVM_CKPT_DIR=/path/to/models     # 内含 rvm_resnet50.pth
```

约定一个工作目录，后面所有命令都在它下面跑：

```
project/
├── raw/speaker.mp4              录好的人像
├── backgrounds/sources/         原始配图
├── backgrounds/ready/           裁好的 1280x720 底板
├── asr/                         转写结果
├── work/                        抠像缓存、时间轴
└── out/                         成片
```

---

## 七步流程

```
- [ ] 1 转写，拿到带时间戳的逐字稿
- [ ] 2 双跑对比，分清「念错了」和「识别错了」
- [ ] 3 生成剪辑计划，人工复核
- [ ] 4 准备配图底板，写来源
- [ ] 5 按讲词写分镜 anchors，构建时间轴
- [ ] 6 抠像合成 + 修音频
- [ ] 7 验收规格，抽帧检查
```

### 1 · 转写

```bash
S=/path/to/skills/school-video-assignment/scripts
conda run -n safe_claw python $S/transcribe_timestamps.py raw/speaker.mp4 asr --tag raw
```

产出 `asr/asr_raw.json`（含句级 + 字级时间戳）和可读的 `asr/asr_raw.txt`。
200 秒素材约 100 秒跑完，纯本地离线。

> 只要通顺文本不要时间戳时，用姊妹 skill `audio-transcription-funasr`。本流程必须要时间戳。

### 2 · 双跑对比：念错了，还是识别错了？

同一段音频跑两遍——原始的、降噪的。**两遍结论不同**说明音频含混，多半是噪声导致的误识；**两遍给出同样的错**，那大概率是真念错了。

```bash
conda run -n safe_claw python $S/transcribe_timestamps.py raw/speaker.mp4 asr --tag denoised --denoise
conda run -n safe_claw python $S/compare_transcripts.py \
    asr/asr_raw.json asr/asr_denoised.json --media raw/speaker.mp4 --clips asr/check_clips
```

这一步同时是**降噪安全性的客观检验**：噪声门可能吃掉轻辅音，如果两遍相似度 ≥ 0.97 且没有整块缺失，就证明没丢字。

⚠️ **两遍一致 ≠ 念对了**。专有名词（人名、型号、成语）ASR 会稳定地错成同一个字。凡是讲稿里的专名，都要照着讲稿逐个核对，把可疑处切成短音频让家长听。真念错了就补录那两三句——每句两三秒，比重录整段划算得多。

### 3 · 剪辑计划

```bash
conda run -n rvm_matting python $S/find_edit_points.py asr/asr_raw.json raw/speaker.mp4 -o edit_plan.json
```

自动识别三类问题并生成 `cuts`：句内长静默、相邻重复句、重复首字（「今今天」），外加过长的句间停顿。终端会打印**需要人工判断**的清单。

复核要点：
- **重复句不一定是废片**。结尾「就是新的长征，就是新的长征」是排比强调，要留；中间「那一刻我明白了……（卡 2.6 秒）……那一刻我明白了」是没剪的重录，要删。
- **句内卡壳默认按压缩处理**。如果静默之后是重录，把那条 cut 扩成整段删除。
- **情绪留白要留住**。金句之后的 1.2~1.5 秒是效果，不是废话；脚本对句末带 `。！？` 的位置已经留得更宽。

### 4 · 配图底板

```bash
conda run -n rvm_matting python $S/prep_plates.py backgrounds/sources backgrounds/ready \
    --sources-md backgrounds/SOURCES.md
```

统一裁成 1280×720（cover 裁切，先去掉截图的白边），并生成来源登记表待填。选图原则见 [references/pitfalls.md](references/pitfalls.md)。

### 5 · 分镜对齐讲词

编辑 `edit_plan.json` 的 `anchors`，把每个切换点的 `REPLACE.jpg` 换成真实底板。**时间写源视频的秒数**（就是逐字稿里的时间），脚本会自动映射到剪辑后的时间轴。

```json
"anchors": [
  [136.29, "ready/09_handwritten_letter.jpg", "在图书馆里，我看过钱老的手稿"],
  [142.91, "ready/10_corridor_mural.jpg",     "那一刻我明白了"]
]
```

- 讲到什么就配什么。说「我看过手稿」，画面就该是手稿。
- **把切换点压在剪辑点上**——背景一换，人物的跳切就不显眼了。
- 每段 5~15 秒。太碎显得慌，太长显得闷。

```bash
conda run -n rvm_matting python $S/build_timeline.py edit_plan.json --work work --backgrounds backgrounds
```

### 6 · 合成

```bash
conda run -n rvm_matting python $S/compose_overlay.py \
    --person raw/speaker.mp4 \
    --storyboard backgrounds/storyboard_aligned.json \
    --keep-frames work/keep_frames.json \
    --output out/final.mp4 \
    --variant resnet50 --downsample-ratio 0.4 \
    --height-frac 0.6667 --max-width-frac 0.42 --side left
```

抠像结果按 `(variant, downsample)` 缓存在 `work/`，**只跑一次**；之后改构图、改分镜、改剪辑都直接复用，一次几分钟而不是几十分钟。音频的裁剪、降噪、两遍响度归一在这一步一起做完。

只想换构图不想动剪辑时，可以只重做音轨，视频流直接 copy（见 pitfalls 文档）。

### 7 · 验收

```bash
conda run -n rvm_matting python $S/verify_output.py out/final.mp4 \
    --max-minutes 5 --max-mb 200 --contact-sheet /tmp/grid.jpg
```

检查时长、体积、容器、音频峰值（**必须 < 0 dB**，否则爆音）、底噪、停顿占比，并抽 6 帧拼图。**一定要看那张拼图**——抠像边缘、人物位置、配图和讲词对不对得上，只有眼睛能判断。

---

## 交付清单

```
- [ ] 成片：MP4，时长与体积在规格内，音频峰值 < 0 dB
- [ ] 逐字稿与校对清单（哪些字要补录、哪些已排除）
- [ ] 配图来源表 SOURCES.md 填完整
- [ ] 抽帧拼图已人工看过
```

## 更多

- [references/pitfalls.md](references/pitfalls.md) — 音频、抠像、配图三类具体坑与诊断命令
- [references/worked-example.md](references/worked-example.md) — 一个完整真实案例的数字与结论
