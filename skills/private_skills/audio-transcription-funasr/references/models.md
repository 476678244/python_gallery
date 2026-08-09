# FunASR Models Reference

## Default stack (Chinese live / podcast)

```python
model = AutoModel(
    model="paraformer-zh",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    disable_update=False,  # set True after first successful download
)
```

| Component | Role | Approx size |
|-----------|------|-------------|
| `paraformer-zh` | Mandarin ASR | ~200 MB |
| `fsmn-vad` | Voice activity detection | ~50 MB |
| `ct-punc` | Chinese punctuation | ~30 MB |

**Total first-run download:** ~300 MB from **ModelScope** (not HuggingFace).

## Why ModelScope instead of HuggingFace

FunASR pulls weights from Alibaba ModelScope by default. In environments where HuggingFace downloads fail (corporate proxy, `ProxyError` on `huggingface.co`), FunASR often still works. This is the main reason to prefer this skill over faster-whisper for local transcription on CN networks.

Cache locations (typical):

- `~/.cache/modelscope/`
- May also appear under `~/.cache/huggingface/hub/` depending on FunASR version

## Available models

### Speech recognition

#### Paraformer series

- **paraformer-zh** — Chinese (default). ~95% CER on benchmarks. Best for 南添直播、播客、中文视频。
- **paraformer-en** — English. ~180 MB.
- **paraformer-multilingual** — Multi-language, lower per-language accuracy.

### VAD

- **fsmn-vad** — Segment speech before ASR; improves long noisy recordings.

### Punctuation

- **ct-punc** — Adds `，。！？` etc.; strongly recommended for readable transcripts.

## Performance (observed)

| Input | Hardware | Wall time |
|-------|----------|-----------|
| 101 min audio, 21×5 min chunks | Apple Silicon CPU, `safe_claw` | ~10 min transcribe (+ ~5 s split, ~4 s extract) |
| First run | Same | +1–3 min model download (silent stdout) |

Real-time factor roughly 0.1–0.2× on modern Mac CPU after models are cached.

## CLI flags (transcribe.py)

```bash
--model paraformer-zh      # ASR model
--offline                  # disable_update=True, cached models only
--markdown out.md          # timestamped sections for chunk mode
--chunk-duration 300       # seconds per section label
--total-duration 6067      # ffprobe duration for last section end time
```

## Hardware

| | Minimum | Recommended |
|---|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB |
| GPU | optional | CUDA speeds up but not required on Mac |

## References

- FunASR GitHub: https://github.com/alibaba-damo-academy/FunASR
- Model Hub: https://modelscope.cn/models
