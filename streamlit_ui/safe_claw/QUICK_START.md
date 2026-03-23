# SafeClaw Quick Start Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Git
- Conda (recommended) or virtual environment

### Installation

#### Option 1: Using Conda (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd safe_claw

# Create conda environment
conda env create -f environment.yml
conda activate safe_claw

# Install the package
pip install -e .
```

#### Option 2: Using pip
```bash
# Clone the repository
git clone <repository-url>
cd safe_claw

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Configuration

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Edit `.env` file:**
```bash
# Add your API keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Running SafeClaw

#### Method 1: Direct Streamlit
```bash
streamlit run streamlit_ui/app.py
```

#### Method 2: Using the installed command
```bash
safe-claw
```

The application will open in your browser at `http://localhost:8501`

## 📋 First Steps

1. **Open the Settings page** to configure your LLM provider
2. **Test the connection** to ensure your API keys work
3. **Start chatting** on the main Chat page
4. **Explore memory management** to see how SafeClaw remembers conversations
5. **Check statistics** to monitor usage and performance

## 🛡️ Safety Features

SafeClaw includes built-in safety features:
- **Command blocking** for dangerous operations
- **Confirmation prompts** for risky actions
- **Audit logging** of all operations
- **File access restrictions** to protected paths

## 🧠 Memory System

SafeClaw uses a 4-layer memory system:
- **Active**: Recent and important memories
- **Dormant**: Less frequently accessed but still relevant
- **Deep**: Compressed long-term storage
- **Forgotten**: Archived memories

## 🔧 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check your `.env` file
   - Ensure API keys are valid and have credits

2. **Memory Issues**
   - Check workspace permissions
   - Ensure sufficient disk space

3. **Import Errors**
   - Verify all dependencies are installed
   - Check Python version (3.10+ required)

### Getting Help

- Check the [Documentation](./Docs/)
- Review the [Development Plan](./dev_plan.md)
- Open an issue on GitHub

## 📚 Documentation

- [Architecture](./Docs/ARCHITECTURE.md)
- [Memory System](./Docs/MEMORY.md)
- [Product Requirements](./Docs/PRD.md)
- [Development Plan](./dev_plan.md)

## 🎯 Next Steps

1. **Explore Skills**: Try file operations and code analysis
2. **Customize**: Add your own skills and agents
3. **Extend**: Integrate with external tools and APIs
4. **Contribute**: Help improve SafeClaw

---

**SafeClaw TRASA** - The Real AI Safety Assistant  
Version 0.1.0 | Built with ❤️ for safety
