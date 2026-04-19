"""
Market Data Provider — Real + simulated market data.
Supports Yahoo Finance (yfinance) for live data.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class MarketDataProvider:
    """
    Market data provider with optional live data from Yahoo Finance.
    
    Usage:
        # Simulated (no dependencies)
        provider = MarketDataProvider()
        
        # Real data (pip install yfinance)
        provider = MarketDataProvider(use_live=True)
    """

    # Simulated price data
    PRICE_DB = {
        "FXAIX": {"base": 192.50, "vol": 0.01, "sector": "Large Cap"},
        "FTEC": {"base": 145.30, "vol": 0.015, "sector": "Technology"},
        "FHLC": {"base": 72.80, "vol": 0.008, "sector": "Healthcare"},
        "FMAG": {"base": 17.20, "vol": 0.012, "sector": "Large Cap Growth"},
        "FBND": {"base": 44.20, "vol": 0.003, "sector": "Fixed Income"},
        "FIDU": {"base": 62.10, "vol": 0.01, "sector": "Industrials"},
        "FCOM": {"base": 31.50, "vol": 0.011, "sector": "Communication"},
        "AAPL": {"base": 198.50, "vol": 0.018, "sector": "Technology"},
        "MSFT": {"base": 415.20, "vol": 0.016, "sector": "Technology"},
        "NVDA": {"base": 875.30, "vol": 0.025, "sector": "Technology"},
        "JNJ": {"base": 155.80, "vol": 0.008, "sector": "Healthcare"},
        "V": {"base": 282.40, "vol": 0.012, "sector": "Financials"},
    }

    def __init__(self, use_live: bool = False):
        self.use_live = use_live
        self._yf = None
        if use_live:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                print("⚠️  yfinance not installed. Using simulated data.")
                print("   Install with: pip install yfinance")
                self.use_live = False

    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        if self.use_live and self._yf:
            try:
                ticker = self._yf.Ticker(symbol)
                info = ticker.fast_info
                return round(info.get("lastPrice", info.get("regularMarketPrice", 0)), 2)
            except Exception:
                pass

        if symbol in self.PRICE_DB:
            info = self.PRICE_DB[symbol]
            change = random.gauss(0, info["vol"])
            return round(info["base"] * (1 + change), 2)
        return None

    def get_historical_prices(self, symbol: str, days: int = 30) -> list[dict]:
        """Get historical prices."""
        if self.use_live and self._yf:
            try:
                ticker = self._yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                return [
                    {
                        "date": str(date.date()),
                        "open": round(row["Open"], 2),
                        "high": round(row["High"], 2),
                        "low": round(row["Low"], 2),
                        "close": round(row["Close"], 2),
                        "volume": int(row["Volume"]),
                    }
                    for date, row in hist.iterrows()
                ]
            except Exception:
                pass

        # Simulated
        if symbol not in self.PRICE_DB:
            return []
        info = self.PRICE_DB[symbol]
        prices = []
        price = info["base"] * 0.95
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
            change = random.gauss(0.001, info["vol"])
            price *= (1 + change)
            prices.append({
                "date": date,
                "open": round(price * 0.998, 2),
                "high": round(price * 1.01, 2),
                "low": round(price * 0.99, 2),
                "close": round(price, 2),
                "volume": random.randint(100000, 10000000),
            })
        return prices

    def get_market_overview(self) -> dict:
        """Get market overview."""
        return {
            "sp500": {"value": 5234.18, "change": round(random.uniform(-1.5, 1.5), 2)},
            "nasdaq": {"value": 16428.82, "change": round(random.uniform(-2.0, 2.0), 2)},
            "dow": {"value": 39512.84, "change": round(random.uniform(-1.0, 1.0), 2)},
            "vix": {"value": round(random.uniform(12, 25), 2), "label": "Fear Index"},
            "ten_year_yield": {"value": round(random.uniform(4.0, 5.0), 2)},
            "timestamp": datetime.now().isoformat(),
        }

    def get_fund_info(self, symbol: str) -> dict:
        """Get fund details."""
        fund_data = {
            "FXAIX": {"expense_ratio": 0.015, "category": "Large Blend", "aum": "503.4B", "inception": "1988-02-17"},
            "FTEC": {"expense_ratio": 0.084, "category": "Technology", "aum": "11.2B", "inception": "2013-10-21"},
            "FHLC": {"expense_ratio": 0.084, "category": "Healthcare", "aum": "2.8B", "inception": "2013-10-21"},
            "FMAG": {"expense_ratio": 0.520, "category": "Large Growth", "aum": "18.7B", "inception": "1963-05-02"},
            "FBND": {"expense_ratio": 0.036, "category": "Intermediate Bond", "aum": "5.1B", "inception": "2021-10-06"},
        }
        return fund_data.get(symbol, {"expense_ratio": None, "category": "Unknown"})
