---
name: cursor-theme-intellij-maple
description: 一键复刻「IntelliJ Light (Maple)」Cursor 外观——JetBrains 风格浅色配色（红蓝强调色）、Maple Mono NF CN 字体、JetBrains 图标主题、紧凑+带边框的标签栏、隐藏 Python 噪声目录。适用于在新机器/新环境快速重建该编辑器外观,或调整、扩展这套主题配置时。
disable-model-invocation: true
---

# Cursor 主题：IntelliJ Light (Maple)

把一套完整的 Cursor 外观（颜色主题 + 字体 + 图标 + 标签栏 + 文件隐藏）固化为可重用配置。所有资产都打包在本 skill 内,通过一个幂等脚本落地。

## 一键应用

```bash
python scripts/apply_theme.py            # 应用全部
python scripts/apply_theme.py --dry-run  # 只预览改动,不写盘
python scripts/apply_theme.py --no-icon  # 跳过图标主题安装(无网络时)
```

脚本做三件事(均幂等,只覆盖本 skill 管理的键):
1. 把 `assets/extension/` 复制到 `~/.cursor/extensions/intellij-light-maple-1.0.0/` 并写入 `extensions.json` 注册。
2. 把 `assets/settings.fragment.json` 合并进用户 `settings.json`（`files.exclude` 做深合并,其余键直接覆盖）。
3. 若 `cursor` CLI 在 PATH 上,自动 `cursor --install-extension chadalen.vscode-jetbrains-icon-theme`。

> 完成后在 Cursor 里执行 `Developer: Reload Window`（`Cmd/Ctrl+Shift+P`）即可生效。颜色主题改动必须 reload,设置类改动多数即时生效。

## 配置构成

| 维度 | 取值 | 落点 |
|------|------|------|
| 颜色主题 | `IntelliJ Light (Maple)`（浅色,`type: light`） | 本 skill 自带的扩展 |
| 代码字体 | `Maple Mono NF CN, Maple Mono NF, Maple Mono Nerd`,size 12,连字开启 | settings |
| 终端字体 | 同上,size 13 | settings |
| 图标主题 | `vscode-jetbrains-icon-theme-2023-light`（JetBrains 新 UI 浅色） | 市场扩展 |
| 标签栏 | 紧凑高度 + 收缩 + 可见边框 + 蓝色激活条 | settings + 主题 |
| 隐藏目录 | `.idea` / `.pytest_cache` / `.vscode` / `__pycache__`（任意层级） | settings |

> 字体说明：仓库优先使用 `Maple Mono NF CN`（中英 2:1 等宽,适合代码含中文）,未安装时回退到已装的 `Maple Mono NF`。CN 变体见 [Maple Mono releases](https://github.com/subframe7536/maple-font/releases)。

## 语法配色（红蓝强调,从真实截图逐像素采样反推墨色）

| 语法元素 | 颜色 | 含义 |
|----------|------|------|
| 关键字 `def`/`if`/`for`/`return`/`True` | `#2E5C97` | 柔和蓝（非电光蓝） |
| 函数/方法**声明**名 | `#A0211B` | 砖红 |
| 函数/方法**调用** | `#000000` | 黑（与声明区分） |
| 形参 | `#A0211B` | 砖红 |
| 局部变量 | `#080808` | 近黑（与形参区分） |
| 类型 `Optional`/`Dict`/`str`/`int` | `#000000` | 黑 |
| 字符串 | `#067D17` | 绿 |
| 数字 | `#1750EB` | 蓝 |
| 注释 | `#8C8C8C` 斜体 | 灰 |
| 常量/字段（`LOG_FILES`、`.attr`） | `#871094` | 紫 |
| 装饰器/注解 | `#9E880D` | 暗黄 |
| 括号/逗号/运算符 | `#000000` | 黑 |

> 关键区分由「TextMate scope + 语义高亮」双层实现：`function.declaration` 红 / `function`(调用) 黑；`variable.parameter` 红 / `variable`(局部) 黑。Cursor 的语义 token 来自 cursorpyright。

## UI 配色基调（JetBrains New UI Light）

- 编辑器 `#FFFFFF`,侧栏/标题栏/状态栏 `#F7F8FA`,强调蓝 `#3574F0`,选区 `#A6D2FF`。
- 标签栏：未激活标签浅灰 `#ECEDF1`,标签间可见竖分隔线 `#C9CCD6`,激活标签上下蓝色高亮条,底部分隔线 `#C2C5CE`。

完整调色板见扩展文件 `assets/extension/themes/intellij-light-maple-color-theme.json`。

## 如何修改

- **改某个语法颜色**：编辑 `assets/extension/themes/intellij-light-maple-color-theme.json` 的 `tokenColors` / `semanticTokenColors`,再 `apply_theme.py` 重装 + reload。
- **改字体/字号/标签栏/隐藏目录**：编辑 `assets/settings.fragment.json`,再 `apply_theme.py`。
- **新增隐藏目录**：在 fragment 的 `files.exclude` 加 `"**/<dir>": true`（深合并,不会覆盖用户已有条目）。
- 改完务必让两份资产与线上保持一致——线上的真源在 `~/.cursor/extensions/intellij-light-maple-1.0.0/` 与用户 `settings.json`,本 skill 是其快照与复现器。

## 目录结构

```
cursor-theme-intellij-maple/
├── SKILL.md
├── assets/
│   ├── settings.fragment.json                       # 本 skill 管理的设置键
│   └── extension/                                    # 颜色主题扩展(完整)
│       ├── package.json
│       └── themes/intellij-light-maple-color-theme.json
└── scripts/
    └── apply_theme.py                               # 幂等安装器
```

## 依赖

仅 Python 标准库。图标主题安装依赖 `cursor` CLI 与网络（可用 `--no-icon` 跳过后手动装）。
