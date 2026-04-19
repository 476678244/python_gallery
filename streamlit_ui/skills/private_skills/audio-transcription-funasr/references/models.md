# FunASR Models Reference

## Available Models

### Speech Recognition Models

#### Paraformer Series
- **paraformer-zh**: Chinese speech recognition model
  - High accuracy for Mandarin Chinese
  - Supports streaming and non-streaming modes
  - Model size: ~200MB
  
- **paraformer-en**: English speech recognition model
  - Optimized for English language
  - Good performance on various accents
  - Model size: ~180MB

- **paraformer-multilingual**: Multilingual speech recognition
  - Supports multiple languages
  - Lower accuracy than language-specific models
  - Model size: ~250MB

### VAD (Voice Activity Detection) Models

#### FSMN-VAD
- **fsmn-vad**: Voice activity detection model
  - Detects speech segments in audio
  - Helps improve transcription accuracy
  - Model size: ~50MB

### Punctuation Models

#### CT-PUNC
- **ct-punc**: Chinese punctuation restoration model
  - Adds punctuation to transcribed text
  - Improves readability
  - Model size: ~30MB

## Model Selection Guide

### For Chinese Audio
```python
model = "paraformer-zh"
vad_model = "fsmn-vad"
punc_model = "ct-punc"
```

### For English Audio
```python
model = "paraformer-en"
vad_model = "fsmn-vad"
# English punctuation model may vary
```

### For Multilingual Audio
```python
model = "paraformer-multilingual"
vad_model = "fsmn-vad"
```

## Model Performance

### Accuracy
- Chinese (paraformer-zh): ~95% CER on test sets
- English (paraformer-en): ~90% WER on test sets
- Multilingual: ~85-90% depending on language

### Speed
- Real-time factor: 0.3-0.5x (faster than real-time)
- GPU acceleration available for faster processing

## Hardware Requirements

### Minimum Requirements
- CPU: 4 cores
- RAM: 8GB
- Storage: 1GB for models

### Recommended Requirements
- CPU: 8+ cores
- RAM: 16GB
- GPU: NVIDIA GPU with CUDA support (optional)
- Storage: 2GB for models

## Model Download

Models are automatically downloaded on first use from the FunASR model hub. Download locations:
- Default: `~/.cache/huggingface/hub/`
- Can be customized via environment variables

## References

- FunASR GitHub: https://github.com/alibaba-damo-academy/FunASR
- Model Hub: https://modelscope.cn/models
- Documentation: https://github.com/alibaba-damo-academy/FunASR/blob/main/docs/readme.md
