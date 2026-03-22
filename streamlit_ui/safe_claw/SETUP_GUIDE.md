# SafeClaw 环境搭建指南（手动版）

> 从 conda 创建环境到 pip 安装依赖的完整步骤

---

## 方式一：手动分步安装

### Step 1: 创建环境

```bash
# 创建 Python 3.11 环境
conda create -n safe_claw python=3.11 -y

# 激活环境
conda activate safe_claw
```

### Step 2: 升级基础工具

```bash
# 确保 pip 最新
pip install --upgrade pip

# 安装 conda 可用的基础包
conda install -c conda-forge pydantic python-dotenv -y
```

### Step 3: 安装核心依赖

```bash
# LangGraph + LangChain 生态
pip install "langgraph>=1.1.1,<2.0.0"
pip install "langchain>=0.2.16,<0.3.0"
pip install "langchain-core>=0.2.38,<0.3.0"
pip install "langchain-community>=0.2.16,<0.3.0"
pip install "langchain-openai>=0.1.23,<0.2.0"
pip install "langchain-anthropic>=0.1.23,<0.2.0"
```

### Step 4: 安装 LLM 网关

```bash
# LiteLLM + 各厂商 SDK
pip install "litellm>=1.51.0,<2.0.0"
pip install "openai>=1.40.0,<2.0.0"
pip install "anthropic>=0.34.2,<1.0.0"
```

### Step 5: 安装 UI 依赖

```bash
pip install "streamlit>=1.33.0,<2.0.0"
pip install "streamlit-graphviz>=0.0.6"
pip install "graphviz>=0.20.3"
```

### Step 6: 安装可选依赖（按需）

```bash
# 配置管理
pip install "pydantic-settings>=2.2.1,<3.0.0"

# RAG / 向量检索
pip install "chromadb>=0.5.5,<0.6.0"
pip install "sentence-transformers>=3.0.1,<4.0.0"

# 文件处理
pip install "pypdf>=4.3.1"
pip install "markdown>=3.6"

# 安全存储
pip install "keyring>=25.2.1"

# 执行沙箱（非 Windows）
pip install "docker>=7.1.0; sys_platform != 'win32'"
```

### Step 7: 安装开发依赖（可选）

```bash
pip install "pytest>=8.3.2"
pip install "pytest-asyncio>=0.23.7"
pip install "black>=24.8.0"
pip install "ruff>=0.6.2"
pip install "mypy>=1.11.1"
```

---

## 方式二：使用 requirements.txt（推荐）

```bash
# Step 1: 创建并激活环境
conda create -n safe_claw python=3.11 -y
conda activate safe_claw

# Step 2: 一键安装所有依赖
pip install -r requirements.txt
```

---

## 方式三：使用 environment.yml

```bash
# 一行命令创建完整环境
conda env create -f environment.yml

# 激活
conda activate safe_claw
```

---

## 验证安装

```bash
# 检查 Python 版本
python --version

# 检查核心包
python -c "import langgraph; print(f'langgraph: {langgraph.__version__}')"
python -c "import langchain; print(f'langchain: {langchain.__version__}')"
python -c "import streamlit; print(f'streamlit: {streamlit.__version__}')"

# 测试导入
python -c "from langgraph.graph import StateGraph; print('✅ LangGraph 正常')"
```

---

## 启动 SafeClaw

```bash
# 确保在 safe_claw 环境
conda activate safe_claw

# 启动 Streamlit
streamlit run app.py

# 或指定端口
streamlit run app.py --server.port 8501
```

---

## 常见问题

### 安装速度慢

```bash
# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或配置全局镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 版本冲突

```bash
# 查看冲突
pip check

# 强制重新安装
pip install --force-reinstall langgraph
```

### 包找不到

```bash
# 确保 pip 最新
pip install --upgrade pip

# 搜索包
pip search langgraph  # 或去 pypi.org 搜索
```

---

## 完整复制粘贴命令

```bash
# 一键执行（推荐）
conda create -n safe_claw python=3.11 -y && \
conda activate safe_claw && \
pip install --upgrade pip && \
pip install -r requirements.txt && \
python -c "import langgraph; print('✅ 安装成功')"
```
