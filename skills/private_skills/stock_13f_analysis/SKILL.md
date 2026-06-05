---
name: stock_13f_analysis
description: 分析 13F 机构持仓组合表现，对比基金权重 vs 等权 vs S&P500 基准。输入基金名称（如 wcm, coatue, viking）和日期范围，返回收益统计、持仓明细和趋势分析。
---

# Stock 13F Analysis Skill

## 用途

用于分析知名机构投资者（13F 申报机构）的持仓组合表现，包括：
- 基金实际权重组合表现
- 等权重组合对比
- S&P 500 基准对比

## 支持基金

- WCM (WCM Investment Management)
- Coatue (Coatue Management)
- Viking (Viking Global Investors)
- Akre (Akre Capital Management)
- ARK (ARK Investment Management)
- Baker Brothers
- Fundsmith
- Lone Pine
- Madison
- Newlands
- Pershing Square
- Third Point
- Tiger Global

## 使用方法

通过工具调用格式：
```
TOOL_CALL: stock_13f_analyze{"fund": "wcm", "start_date": "2025-01-01", "end_date": "2025-12-31", "mode": "fund"}
```

## 参数说明

- `fund` (必填): 基金名称，如 wcm, coatue, viking
- `start_date` (必填): 开始日期，格式 YYYY-MM-DD
- `end_date` (可选): 结束日期，默认今天
- `mode` (可选): 权重模式，fund=基金权重, equal=等权重，默认 fund
- `save_chart` (可选): 是否保存趋势图，默认 true

## 输出

返回分析结果，包括：
- 区间收益统计
- 持仓股票列表
- 与基准对比表现
- 趋势图文件路径
