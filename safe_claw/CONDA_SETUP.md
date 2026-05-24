# SafeClaw Conda 环境配置指南

> 使用 Conda 管理 Python 环境和依赖

---

## 快速开始

### 1. 创建环境

```bash
cd safe_claw
conda env create -f environment.yml
```

### 2. 激活环境

```bash
conda activate safe_claw
```

### 3. 启动应用

```bash
streamlit run app.py
```

---

## 环境文件说明

### `environment.yml` 结构

```yaml
name: safe_claw           # 环境名称
channels:                 # 包源
  - conda-forge          # 推荐社区源
  - defaults             # Anaconda 官方源
dependencies:             # 依赖列表
  - python>=3.11,<3.13   # Python 版本
  - pip                  # pip 工具（必须）
  - pip:                 # pip 专用包
    - langgraph>=1.1.1
    ...
```

---

## 常用命令

### 环境管理

```bash
# 创建环境
conda env create -f environment.yml

# 创建并指定名称
conda env create -f environment.yml -n my_safe_claw

# 更新环境（依赖变更后）
conda env update -f environment.yml

# 删除环境
conda env remove -n safe_claw

# 查看所有环境
conda env list

# 导出当前环境（生成 lock 文件）
conda env export > environment-lock.yml
```

### 包管理

```bash
# 激活环境后安装额外包
conda install numpy pandas

# 使用 pip（conda 没有时）
pip install some-package

# 查看已安装包
conda list

# 搜索可用包
conda search langgraph
```

---

## 频道（Channels）推荐

| 频道 | 用途 | 优先级 |
|------|------|--------|
| `conda-forge` | 社区维护，包最全 | 首选 |
| `defaults` | Anaconda 官方 | 备选 |
| `pytorch` | PyTorch 相关 | 特定需求 |

### 配置频道

```bash
# 添加频道
conda config --add channels conda-forge

# 设置严格频道优先级
conda config --set channel_priority strict

# 查看配置
conda config --show channels
```

---

## 与其他工具对比

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| 纯 pip 项目 | `requirements.txt` | 简单直接 |
| 需要 C 库依赖 | `environment.yml` | conda 管理二进制依赖 |
| 数据科学/ML | `environment.yml` | numpy/pandas 预编译包 |
| 团队协作 | `environment.yml` + lock | 可复现环境 |

---

## 故障排除

### 解决包冲突

```bash
# 查看冲突
conda env create -f environment.yml --dry-run

# 创建最小环境排查
conda create -n test python=3.11
conda activate test
pip install langgraph  # 逐个安装定位问题
```

### 清理缓存

```bash
# 清理未使用包
conda clean --packages

# 清理所有缓存
conda clean --all
```

### M1/M2 Mac 特定

```bash
# 确保使用 arm64 架构
conda create -n safe_claw python=3.11 -c conda-forge

# 如需要 Rosetta 模式（旧包）
CONDA_SUBDIR=osx-64 conda create -n safe_claw_x64 python=3.11
```

---

## 开发工作流

### 推荐设置

```bash
# 1. 创建并激活环境
conda env create -f environment.yml
conda activate safe_claw

# 2. 安装开发模式（如有 setup.py）
pip install -e .

# 3. 预提交钩子（可选）
pre-commit install

# 4. 运行测试
pytest
```

### 环境导出（用于 CI/CD）

```bash
# 精确版本锁定
conda env export --no-builds > environment-lock.yml

# 跨平台兼容版本
conda env export --from-history > environment-minimal.yml
```

---

## VS Code 集成

### 选择解释器

1. `Cmd/Ctrl + Shift + P` → "Python: Select Interpreter"
2. 选择 `safe_claw` 环境

### 自动激活

在 `.vscode/settings.json` 中添加：

```json
{
  "python.defaultInterpreterPath": "~/miniconda3/envs/safe_claw/bin/python",
  "python.terminal.activateEnvironment": true
}
```

---

## 参考

- [Conda 官方文档](https://docs.conda.io/)
- [Conda Forge](https://conda-forge.org/)
- [Mamba](https://mamba.readthedocs.io/) - Conda 的更快替代品
