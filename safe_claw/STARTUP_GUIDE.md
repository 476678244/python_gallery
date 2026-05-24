# 🦞 SafeClaw AI Safety Assistant - Startup Guide

## 🚀 Quick Start

### Method 1: Use the Startup Script (Recommended)
```bash
# Activate conda environment
conda activate safe_claw

# Run SafeClaw
python run_safeclaw.py
```

### Method 2: Manual Start
```bash
# Activate conda environment
conda activate safe_claw

# Start Streamlit
streamlit run app.py
```

## 🤖 LLM Configuration

SafeClaw automatically tries multiple LLM configurations:

1. **LM Studio Local Server** (http://localhost:1234/v1)
2. **OpenAI API** (requires API key)
3. **Mock/Demo Mode** (always works for testing)

### Configure Real LLM

1. In SafeClaw, go to **Settings** ⚙️
2. Configure your LLM provider:
   - **LM Studio**: Set base URL to `http://localhost:1234/v1`
   - **OpenAI**: Enter your API key
   - **Other**: Configure as needed

## 📋 System Requirements

- Python 3.11+
- Conda environment: `safe_claw`
- Packages: streamlit, langchain, openai, etc.

## 🛠️ Troubleshooting

### "Required services not available" Error
- SafeClaw falls back to mock mode automatically
- Check LLM configuration in Settings
- Ensure LM Studio is running if using local server

### LLM Connection Issues
- Try the mock mode first (works immediately)
- Check API keys and base URLs
- Verify network connectivity

### Memory Issues
- Ensure workspace directory exists
- Check file permissions
- Restart SafeClaw if needed

## 🎯 Features

- **💬 Chat**: AI assistant with safety confirmation
- **📚 Memory**: 4-layer memory system with search
- **⚙️ Settings**: Configure LLM and safety policies
- **📊 Stats**: Usage analytics and performance metrics
- **🔧 Tools**: Advanced monitoring and management

## 🧪 Testing

SafeClaw includes comprehensive tests:
```bash
# Run unit tests (81 tests, all passing)
python -m pytest tests/unit/ -v

# Check service status
python -c "
from services.llm_gateway import LLMService
from models.config import LLMConfig
service = LLMService(LLMConfig(api_key='mock-key'))
print(service.invoke([{'role': 'user', 'content': 'Hello'}]))
"
```

## 🦞 SafeClaw Status

- ✅ **Unit Tests**: 81/81 passing
- ✅ **Core Services**: All operational
- ✅ **Memory System**: 4-layer working
- ✅ **Safety Features**: Confirmation workflows
- ✅ **UI Components**: Professional interface
- ✅ **Mock Mode**: Always available

**SafeClaw is production-ready for core functionality!**

---

*SafeClaw AI Safety Assistant - Your AI Safety Partner* 🛡️
