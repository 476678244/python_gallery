from datetime import datetime

import portfolio_analysis as pa

# =========================================================
# 1. 股票池 & 原始 WCM 权重
# =========================================================
RAW_WEIGHTS = {
    "SE": 0.098,
    "APP": 0.073,
    "TSM": 0.057,
    "SPOT": 0.051,
    "ASML": 0.039,
    "PM": 0.038,
    "IBN": 0.034,
    "LIN": 0.034,
    "CPNG": 0.033,
    "AMZN": 0.029,
    "MELI": 0.026,
}

TICKERS = list(RAW_WEIGHTS.keys())
N = len(TICKERS)

# =========================================================
# 2. 权重生成器
# =========================================================
def get_weights(mode="wcm"):
    if mode == "wcm":
        return pa.normalize_weights(RAW_WEIGHTS)
    elif mode == "equal":
        return pa.equal_weights(TICKERS)
    else:
        raise ValueError("weight mode must be 'wcm' or 'equal'")

# =========================================================
# 3. 数据下载
# =========================================================
def download_prices(tickers, start, end):
    return pa.download_close_prices(tickers, start, end)

def get_sp500(start, end):
    return pa.download_index_close("^GSPC", start, end)

# =========================================================
# 4. 构建组合净值（严格金融定义）
# =========================================================
def build_portfolio(prices, weight_mode="wcm"):
    weights = get_weights(weight_mode)
    return pa.build_portfolio_close(prices, weights)

# =========================================================
# 5. Synthetic OHLC（仅用于 K 线）
# =========================================================
def make_synthetic_ohlc(close_df):
    return pa.make_synthetic_ohlc(close_df)

# =========================================================
# 6. 当年 Trend（log scale）
# =========================================================
def plot_year_trend(df, title):
    df = df / df.iloc[0]

    # NOTE: 保留函数签名以兼容你之前的使用方式。
    # 如需通用 trend 画图，可在 portfolio_analysis.py 扩展相应 API。
    raise NotImplementedError("plot_year_trend is not used in the current CLI")

def plot_three_way_trend(p_wcm, p_eq, sp500, year_label, start_date=None, end_date=None):
    return pa.plot_three_way_trend(
        p_wcm,
        p_eq,
        sp500,
        year_label,
        label_a="WCM-weighted",
        label_b="Equal-weight",
        benchmark_label="S&P 500",
        fund_name="WCM",
        start_date=start_date,
        end_date=end_date,
    )

# =========================================================
# 7. K 线绘图
# =========================================================
def plot_ytd_candlestick(ohlc, title):
    return pa.plot_ytd_candlestick(ohlc, title)

# =========================================================
# 8. Main（开始日期 hard code 在这里）
# =========================================================
if __name__ == "__main__":

    # ======== 核心参数（你只需要改这里）========
    START_DATE = "2025-01-01"
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    YEAR_LABEL = "2025 YTD"
    # ===========================================

    print("WCM-style Portfolio Trend Tool")
    print("1. WCM / 等权 / SP500 当年 Trend")
    print("2. WCM 组合 K 线")
    print("3. 等权组合 K 线")
    print("4. 全部执行")

    choice = input("请选择要执行的操作 (1-4): ")

    prices = download_prices(TICKERS, START_DATE, END_DATE)
    p_wcm = build_portfolio(prices, "wcm")
    p_eq = build_portfolio(prices, "equal")
    sp500 = get_sp500(START_DATE, END_DATE)

    if choice in {"1", "4"}:
        plot_three_way_trend(p_wcm, p_eq, sp500, YEAR_LABEL, start_date=START_DATE, end_date=END_DATE)

    if choice in {"2", "4"}:
        ohlc = make_synthetic_ohlc(p_wcm)
        plot_ytd_candlestick(ohlc, "WCM-weighted Portfolio | YTD")

    if choice in {"3", "4"}:
        ohlc = make_synthetic_ohlc(p_eq)
        plot_ytd_candlestick(ohlc, "Equal-weight Portfolio | YTD")
