# 具体的坑与诊断命令

## 一、音频

家庭录制的音频问题比画面严重得多，而且是评委唯一无法忽略的部分。

### 先诊断，别瞎调

```bash
V=out/final.mp4
# 平均音量 / 峰值
ffmpeg -i "$V" -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"
# 真峰值（volumedetect 会漏掉采样间峰值）
ffmpeg -i "$V" -af astats=metadata=1 -f null - 2>&1 | grep -m1 "Peak level dB"
# 停顿分布
ffmpeg -i "$V" -af "silencedetect=noise=-35dB:d=0.8" -f null - 2>&1 | grep silence_duration
# 底噪：挑一段没说话的时间窗单独测
ffmpeg -ss 13.5 -to 14.8 -i raw/speaker.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume
```

判读：
- `max_volume` ≥ 0 dB → **削波**，播放会爆音
- 人声均值 − 底噪均值 = 信噪比。低于 20 dB 就必须先降噪再提增益
- 停顿总时长 / 全片 > 20% → 节奏拖沓

### 坑 1：单遍 loudnorm 在极轻的素材上会削波

`-af loudnorm=I=-14:TP=-1.5` 看着设了 TP，实际动态模式守不住。实测源片均值 −37.8 dB，一遍归一后峰值 **+2.16 dB**，已经削了。

正确做法是**测量 + 线性第二遍 + 限幅器**：

```bash
# 第一遍只测量
ffmpeg -i in.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | tail -14
# 第二遍把测出来的值填回去，linear=true，再串一个 alimiter 兜底
ffmpeg -i in.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=...:measured_TP=...:\
measured_LRA=...:measured_thresh=...:offset=...:linear=true,alimiter=limit=0.891:level=disabled" out.mp4
```

`compose_overlay.py` 的 `mux_audio()` 已经实现了这个两遍流程。

### 坑 2：提了 20 dB 增益，房间底噪跟着上来

信噪比只有 15 dB 时，把人声推到 −16 LUFS 意味着底噪也被推到 −31 dB，全片嘶嘶响。

**必须在增益之前降噪**（`CLEANUP` 常量就干这个）：

```
highpass=f=90                                   低频隆隆声
afftdn=nr=12:nf=-45:tn=1                        自适应降噪
agate=threshold=0.010:ratio=3:attack=15:release=350:makeup=1   停顿处压掉房间音
equalizer=f=3000:t=q:w=1.2:g=3                  3 kHz 提亮，童声吐字更清楚
```

实测停顿底噪 −34.7 dB → **−61 dB**，人声电平不变。

### 坑 3：噪声门可能吃掉轻辅音——用 ASR 复测来证伪

调完降噪不要靠耳朵猜，**把处理后的音频重新转写一遍，和原始逐字稿比对**。相似度 ≥ 0.97 且没有整块缺失，就说明没丢字。`compare_transcripts.py` 直接给结论。

顺带的好处：降噪后 ASR 准确率会上升。实测有一句原本识别成「汪荣之城」，降噪后正确识别为「光荣之城」——证明孩子念对了，省掉一次无谓的补录。

---

## 二、抠像与合成

### 坑 4：人物边缘出现悬浮的矩形块

源视频通常把人的腿在画面底边切平了。如果合成时在人物下方留了边距（哪怕 14 px），那条平边加上间隙就变成一个看得见的矩形。

**贴底放**（`oy = H - rh`），平边和画面底边重合，看起来就是「站在画框外」。

### 坑 5：挥手时胳膊半透明

运动模糊让 RVM 给出的 alpha 只有 0.3~0.6，胳膊透出背景，这是「换过背景」最明显的破绽。

修法是给 alpha 加对比度曲线，把 0.6 以上推成全不透明，再留 1 px 羽化：

```python
a = np.clip((alpha - 0.06) / 0.54, 0, 1)
```

源素材本身的运动模糊救不回来，手部还是会偏软。真要清晰只能重录（提高快门速度 / 加光 / 让孩子动作慢一点）。

### 坑 6：人物在角落里游走、忽大忽小

逐帧算包围盒会导致抖动。**对整段视频取包围盒的并集，得到一个固定裁切框**，全片不变。

用「最大连通域」找人，否则零星的 alpha 噪点会把框撑到全画面（`largest_component_bbox`）。

### 坑 7：抠像跑一次要几分钟，每改一次构图都重跑

按 `(variant, downsample)` 把前景和 alpha 缓存成两个 mp4。之后改构图、改分镜、改剪辑都直接读缓存。

**剪辑也不需要重跑抠像**——按帧号跳过不要的帧即可（`--keep-frames`），比先剪源视频再重新抠像快得多。

### 坑 8：剪辑点会看到人物"跳"一下

三招叠加基本看不出来：
1. 尽量剪在静音处（人相对静止）
2. 把背景切换点压在剪辑点上，注意力被背景吸走
3. 剪切点做 3 帧溶解（`DISSOLVE = [0.70, 0.45, 0.22]`）

人物只占画面 1/4 宽时，跳切本来就不明显。

### 坑 9：抠出来的人像「贴」在背景上

加 light wrap：把背景颜色渗进人物外缘几个像素。

```python
edge = np.clip(cv2.GaussianBlur(person_a, (0, 0), 4.0) - person_a, 0, 1)[..., None]
p = p * (1 - edge * 0.55) + roi * (edge * 0.55)
```

再配一个很淡的椭圆投影（strength ≈ 0.22）。投影太重反而假。

### downsample-ratio 怎么选

RVM 训练在 512×288 附近。让 `画面宽度 × ratio ≈ 512`：

| 输入宽度 | ratio |
|---|---|
| 1280 | 0.4 |
| 1920 | 0.27 |
| 3840 | 0.13 |

调大不会更清晰，反而可能变差。想更快用 `--variant mobilenetv3`。

### 只改音频，不重跑合成

视频流直接 copy，几秒钟就好：

```bash
ffmpeg -y -i out/final.mp4 -i raw/speaker.mp4 -map 0:v:0 -map 1:a:0 -c:v copy \
  -af "aselect='$(cat work/audio_select.txt)',asetpts=N/SR/TB,<CLEANUP>,<loudnorm二遍>,alimiter=limit=0.891" \
  -c:a aac -b:a 160k -shortest out/final_newaudio.mp4
```

---

## 三、配图

### 选图

- **讲到什么配什么**。说「我看过手稿」，画面就该是手稿展板，不是外景。
- 优先用**内景**。外景蓝天白云容易和室内光线的人物对不上；室内墙面做背景，人物反而自然。
- **避开背景里的人脸**，会跟主讲者抢注意力。
- 首尾用同一张，呼应感很强。
- 底板要**留出左下角**给人物。主体在右侧或中上部的图最好用。

### 处理

- 统一 1280×720 cover 裁切，不能出现黑边（`prep_plates.py`）
- 手机截图先去白边，否则合成画面四周会有白框
- 裁切重心略偏上（脚本里 `0.4`），建筑和室内的主体一般在中线以上

### 来源

学校作业通常要能说明出处。`prep_plates.py --sources-md` 会生成登记表，逐行填：自己拍的写「本人拍摄」，网上取的写链接与许可（Wikimedia Commons、官网公开图等）。**别用来源不明的图**。
