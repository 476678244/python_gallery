---
name: cursor-theme-intellij-maple
description: 一键复刻「IntelliJ Light (Maple)」编辑器外观,Cursor 与 Obsidian 两端通用——JetBrains 浅色配色（红蓝强调色）、Maple Mono NF CN 字体、JetBrains 图标/文件类型图标、紧凑带边框标签栏、隐藏 Python 噪声目录。适用于在新机器/新环境快速重建这套外观,或调整、扩展该主题配置时。
disable-model-invocation: true
---

# 编辑器主题：IntelliJ Light (Maple)（Cursor + Obsidian）

把一套完整的编辑器外观固化为可重用配置,**一个脚本两端复现**：
- **Cursor**：颜色主题扩展 + 字体 + 图标主题 + 标签栏 + 文件隐藏。
- **Obsidian**：CSS 主题（同款配色/代码高亮/文件类型图标）+ 字体 + accent。

所有资产都打包在本 skill 内,通过幂等脚本落地。

## 一键应用

```bash
python scripts/apply_theme.py                       # 仅 Cursor（安全默认）
python scripts/apply_theme.py --vault /path/to/vault   # Cursor + 指定 Obsidian vault
python scripts/apply_theme.py --no-cursor --vault X    # 仅 Obsidian
python scripts/apply_theme.py --all-vaults             # Cursor + 所有已知 vault
python scripts/apply_theme.py --list-vaults            # 列出 obsidian.json 里的 vault
python scripts/apply_theme.py --dry-run --vault X      # 预览,不写盘
python scripts/apply_theme.py --no-icon                # 跳过图标扩展安装(无网络时)
```

所有写操作幂等,只覆盖本 skill 管理的键/文件。

> 生效：Cursor 执行 `Developer: Reload Window`；Obsidian 执行 `Reload app without saving`（均 `Cmd/Ctrl+Shift+P` 或 `Cmd/Ctrl+P`）。

### 脚本行为

**Cursor**（除非 `--no-cursor`）：
1. 复制 `assets/extension/` → `~/.cursor/extensions/intellij-light-maple-1.0.0/` 并写入 `extensions.json` 注册。
2. 合并 `assets/settings.fragment.json` 进用户 `settings.json`（`files.exclude` 深合并,其余键覆盖）。
3. 若 `cursor` CLI 在 PATH,自动装 `chadalen.vscode-jetbrains-icon-theme`。

**Obsidian**（每个 `--vault`）：
1. 复制 `assets/obsidian/themes/IntelliJ Light (Maple)/` → `<vault>/.obsidian/themes/`。
2. 合并 `assets/obsidian/appearance.fragment.json` 进 `<vault>/.obsidian/appearance.json`（设 `theme=moonstone` 浅色、`cssTheme`、accent、三处字体；保留 `baseFontSize`/`translucency` 等其它键）。

## 配置构成

| 维度 | 取值 | Cursor 落点 | Obsidian 落点 |
|------|------|------|------|
| 主题 | `IntelliJ Light (Maple)`（浅色） | 自带扩展 | 自带 CSS 主题 |
| 字体 | `Maple Mono NF CN, Maple Mono NF, Maple Mono Nerd` | settings（代码 12 / 终端 13） | appearance（三处字体,baseFontSize 14） |
| 图标 | JetBrains 风格 | `vscode-jetbrains-icon-theme-2023-light` 扩展 | CSS 文件类型图标（无需插件） |
| 标签栏 | 紧凑+边框+蓝条 | settings + 主题 | 主题 CSS |
| 隐藏目录 | `.idea`/`.pytest_cache`/`.vscode`/`__pycache__` | settings（仅 Cursor） | — |

> 字体说明：优先 `Maple Mono NF CN`（中英 2:1 等宽,适合含中文）,未安装回退到 `Maple Mono NF`。CN 变体见 [Maple Mono releases](https://github.com/subframe7536/maple-font/releases)。

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

> Cursor 端关键区分由「TextMate scope + 语义高亮」双层实现：`function.declaration` 红 / `function`(调用) 黑；`variable.parameter` 红 / `variable`(局部) 黑（语义 token 来自 cursorpyright）。Obsidian 端映射到 `--code-*` 变量（阅读模式 Prism）+ `.cm-*` 类（编辑器代码块）。

## UI 配色基调（JetBrains New UI Light）

- 编辑器 `#FFFFFF`,侧栏/标题栏/状态栏 `#F7F8FA`,强调蓝 `#3574F0`,选区 `#A6D2FF`。
- 标签栏：未激活标签浅灰 `#ECEDF1`,标签间竖分隔线 `#C9CCD6`,激活标签蓝色高亮条,底部分隔线 `#C2C5CE`。
- Obsidian 额外：H1/H2 蓝色标题、行内代码红字灰底、文件浏览器按扩展名上色图标（文件夹灰、md/py 蓝、json 黄、图片绿、pdf 红）。

完整调色板见 `assets/extension/themes/intellij-light-maple-color-theme.json`（Cursor）与 `assets/obsidian/themes/IntelliJ Light (Maple)/theme.css`（Obsidian）。

## 如何修改

- **改语法色（Cursor）**：编辑扩展 theme JSON 的 `tokenColors`/`semanticTokenColors`。
- **改语法色/图标（Obsidian）**：编辑 `theme.css` 的 `--code-*`、`.cm-*` 或文件图标段。
- **改字体/字号/标签栏/隐藏目录（Cursor）**：编辑 `assets/settings.fragment.json`。
- **改字体/accent/明暗（Obsidian）**：编辑 `assets/obsidian/appearance.fragment.json`。
- 改完跑 `apply_theme.py` 重装 + reload。
- 新增 Obsidian 文件类型图标：在 `theme.css` 仿照 `.nav-file-title[data-path$=".xxx"]` 加一条 mask-image 规则。
- 真源是线上文件（`~/.cursor/extensions/...`、Cursor `settings.json`、`<vault>/.obsidian/...`）;本 skill 是其快照与复现器,**线上改动后记得回灌到 assets 保持一致**。

## 目录结构

```
cursor-theme-intellij-maple/
├── SKILL.md
├── assets/
│   ├── settings.fragment.json                       # Cursor 设置键
│   ├── extension/                                    # Cursor 颜色主题扩展
│   │   ├── package.json
│   │   └── themes/intellij-light-maple-color-theme.json
│   └── obsidian/
│       ├── appearance.fragment.json                 # Obsidian appearance 键
│       └── themes/IntelliJ Light (Maple)/
│           ├── manifest.json
│           └── theme.css                            # 配色 + 代码高亮 + 文件图标
└── scripts/
    └── apply_theme.py                               # 幂等双端安装器
```

## 依赖

仅 Python 标准库。Cursor 图标扩展安装依赖 `cursor` CLI 与网络（可 `--no-icon` 跳过后手动装）。Obsidian 端纯 CSS,无插件依赖。
