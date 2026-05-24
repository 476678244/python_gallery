"""
Stock 13F Analysis Skill - Main Implementation
13F 机构持仓分析技能主实现
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date

# 添加 stock/13f 到路径
STOCK_13F_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / "stock" / "13f"
if str(STOCK_13F_PATH) not in sys.path:
    sys.path.insert(0, str(STOCK_13F_PATH))

from base_portfolio import BasePortfolio


# 动态导入可用的组合类
FUND_REGISTRY: Dict[str, type] = {}


def _register_funds():
    """自动发现并注册可用的基金组合类"""
    global FUND_REGISTRY
    
    fund_files = [
        ("wcm_portfolio", "WCMPortfolio"),
        ("coatue_portfolio", "CoatuePortfolio"),
        ("viking_portfolio", "VikingPortfolio"),
        ("akre_portfolio", "AkrePortfolio"),
        ("ark_portfolio", "ArkPortfolio"),
        ("bakerbrothers_portfolio", "BakerBrothersPortfolio"),
        ("fundsmith_portfolio", "FundsmithPortfolio"),
        ("lonepine_portfolio", "LonePinePortfolio"),
        ("madison_portfolio", "MadisonPortfolio"),
        ("newlands_portfolio", "NewlandsPortfolio"),
        ("pershing_portfolio", "PershingPortfolio"),
        ("thirdpoint_portfolio", "ThirdPointPortfolio"),
        ("tiger_portfolio", "TigerPortfolio"),
    ]
    
    for module_name, class_name in fund_files:
        try:
            module = __import__(module_name, fromlist=[class_name])
            fund_class = getattr(module, class_name, None)
            if fund_class and issubclass(fund_class, BasePortfolio):
                fund_name = fund_class.FUND_NAME.lower()
                FUND_REGISTRY[fund_name] = fund_class
        except Exception:
            pass


# 初始化注册
_register_funds()


def run(
    fund: str,
    start_date: str,
    end_date: Optional[str] = None,
    mode: str = "fund",
    benchmark: str = "^GSPC",
    save_chart: bool = True,
) -> Dict[str, Any]:
    """
    分析 13F 基金持仓表现
    
    Args:
        fund: 基金名称（如 wcm, coatue, viking）
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)，默认今天
        mode: 权重模式 (fund/equal)
        benchmark: 基准指数，默认 S&P 500
        save_chart: 是否保存趋势图
    
    Returns:
        分析结果字典
    """
    # 参数处理
    fund = fund.lower()
    if end_date is None:
        end_date = date.today().strftime("%Y-%m-%d")
    
    # 检查基金是否可用
    if fund not in FUND_REGISTRY:
        available = ", ".join(FUND_REGISTRY.keys())
        return {
            "success": False,
            "error": f"未知基金 '{fund}'。可用基金: {available}",
        }
    
    # 获取基金类
    FundClass = FUND_REGISTRY[fund]
    
    try:
        # 创建组合实例
        portfolio = FundClass()
        
        # 下载价格数据
        prices = portfolio.download_prices(start_date, end_date)
        
        # 计算组合收益
        fund_returns = portfolio.build_portfolio(prices, fund)
        equal_returns = portfolio.build_portfolio(prices, "equal")
        
        # 获取基准数据
        benchmark_prices = portfolio.download_index_close(benchmark, start_date, end_date)
        
        # 计算统计指标
        def calc_stats(series, name):
            total_return = (series.iloc[-1] / series.iloc[0] - 1) * 100
            return {
                "name": name,
                "start_value": round(series.iloc[0], 2),
                "end_value": round(series.iloc[-1], 2),
                "total_return_pct": round(total_return, 2),
            }
        
        fund_stats = calc_stats(fund_returns, f"{portfolio.FUND_NAME}-weighted")
        equal_stats = calc_stats(equal_returns, "Equal-weight")
        benchmark_stats = calc_stats(benchmark_prices, "S&P 500")
        
        result = {
            "success": True,
            "fund": portfolio.FUND_NAME,
            "period": f"{start_date} to {end_date}",
            "holdings": portfolio.tickers,
            "weights": portfolio.get_weights(fund) if mode == "fund" else portfolio.get_weights("equal"),
            "performance": {
                "fund": fund_stats,
                "equal_weight": equal_stats,
                "benchmark": benchmark_stats,
            },
        }
        
        # 生成图表
        if save_chart:
            try:
                from portfolio_analysis.portfolio_analysis import plot_three_way_trend
                
                fund_df = fund_returns.to_frame("Close")
                equal_df = equal_returns.to_frame("Close")
                
                year_label = f"{start_date.split('-')[0]} YTD"
                plot_three_way_trend(
                    fund_df,
                    equal_df,
                    benchmark_prices,
                    year_label,
                    label_a=f"{portfolio.FUND_NAME}-weighted",
                    label_b="Equal-weight",
                    benchmark_label="S&P 500",
                    fund_name=portfolio.FUND_NAME,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                safe_fund = portfolio.FUND_NAME.replace(" ", "_")
                chart_path = f"three_lines/{safe_fund}_{start_date}_{end_date}.png"
                result["chart_saved"] = chart_path
                
            except Exception as e:
                result["chart_error"] = str(e)
        
        # 生成文本摘要
        summary = f"""【{portfolio.FUND_NAME} 组合分析】
分析区间: {start_date} ~ {end_date}
持仓股票: {', '.join(portfolio.tickers)}

【收益表现】
- {portfolio.FUND_NAME}-weighted: {fund_stats['total_return_pct']}%
- Equal-weight: {equal_stats['total_return_pct']}%
- S&P 500 基准: {benchmark_stats['total_return_pct']}%

【相对表现】
vs 等权: {fund_stats['total_return_pct'] - equal_stats['total_return_pct']:+.2f}%
vs 基准: {fund_stats['total_return_pct'] - benchmark_stats['total_return_pct']:+.2f}%"""
        result["summary"] = summary
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"分析失败: {str(e)}",
        }


def list_funds() -> List[str]:
    """列出所有可用的基金"""
    return list(FUND_REGISTRY.keys())


# 技能定义（用于注册表）
SKILL_DEFINITION = {
    "name": "stock_13f_analyze",
    "description": "分析 13F 机构持仓组合表现。输入基金名称和日期范围，返回收益统计和对比分析。",
    "parameters": {
        "type": "object",
        "properties": {
            "fund": {
                "type": "string",
                "description": "基金名称，如 wcm, coatue, viking",
                "enum": list(FUND_REGISTRY.keys()),
            },
            "start_date": {
                "type": "string",
                "description": "开始日期，格式 YYYY-MM-DD",
            },
            "end_date": {
                "type": "string",
                "description": "结束日期，格式 YYYY-MM-DD，默认今天",
            },
            "mode": {
                "type": "string",
                "description": "权重模式",
                "enum": ["fund", "equal"],
                "default": "fund",
            },
            "save_chart": {
                "type": "boolean",
                "description": "是否保存趋势图",
                "default": True,
            },
        },
        "required": ["fund", "start_date"],
    },
}


if __name__ == "__main__":
    # CLI 测试
    import json
    
    if len(sys.argv) < 2:
        print("用法: python main.py <fund> [start_date] [end_date]")
        print(f"可用基金: {', '.join(list_funds())}")
        sys.exit(1)
    
    fund = sys.argv[1]
    start = sys.argv[2] if len(sys.argv) > 2 else "2025-01-01"
    end = sys.argv[3] if len(sys.argv) > 3 else date.today().strftime("%Y-%m-%d")
    
    result = run(fund, start, end)
    print(json.dumps(result, indent=2, ensure_ascii=False))
