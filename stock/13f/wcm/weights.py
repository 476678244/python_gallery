import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
from datetime import datetime


# ===== 组合成分 & 权重（百分比 → 小数）=====
weights = {
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
    "CP": 0.026,
    "ACGL": 0.025,
    "NU": 0.025,
    "STX": 0.025,
    "HOOD": 0.025,
}

print("sum(weights.values()): {}".format(sum(weights.values())))