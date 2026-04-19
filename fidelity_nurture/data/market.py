"""
Market Data Provider — Simulated and extensible market data fetching.
Supports real API integration (Yahoo Finance, Alpha Vantage, etc.)
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class MarketDataProvider:
    """
    Market data provider with simulated data and API-ready architecture.
    
    For production, integrate with:
    - Yahoo Finance API (yfinance)
    - Alpha Vantage
    - Fidelity API (if available)
    - IEX Cloud
    """

    # Simulated price ranges by symbol
    PRICE_DB = {
        "FXAIX": {"base": 192.50, "vol": 0.01},
        "FTEC": {"base": 145.30, "vol": 0.015},
        "FHLC": {"base": 72.80, "vol": 0.008},
        "FMAG": {"base": 17.20, "vol": 0.012},
        "FBND": {"base": 44.20, "vol": 0.003},
        "FIDU": {"base": 62.10, "vol": 0.01},
        "FCOM": {"base": 31.50, "vol": 0.011},
        "AAPL": {"base": 198.50, "vol": 0.018},
        "MSFT": {"base": 415.20, "vol": 0.016},
        "NVDA": {"base": 875.30, "vol": 0.025},
        "JNJ": {"base": 155.80, "vol": 0.008},
        "V": {"base": 282.40, "vol": 0.012},
    }

    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        if symbol in self.PRICE_DB:
            info = self.PRICE_DB[symbol]
            change = random.gauss(0, info["vol"])
            return round(info["base"] * (1 + change), 2)
        return None

    def get_historical_prices(self, symbol: str, days: int = 30) -> list[dict]:
        """Get simulated historical prices."""
        if symbol not in self.PRICE_DB:
            return []

        info = self.PRICE_DB[symbol]
        prices = []
        price = info["base"] * 0.95  # Start slightly lower

        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
            change = random.gauss(0.001, info["vol"])  # Slight upward bias
            price = price * (1 + change)
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
        """Get simulated market overview."""
        return {
            "sp500": {"value": 5234.18, "change": round(random.uniform(-1.5, 1.5), 2)},
            "nasdaq": {"value": 16428.82, "change": round(random.uniform(-2.0, 2.0), 2)},
            "dow": {"value": 39512.84, "change": round(random.uniform(-1.0, 1.0), 2)},
            "vix": {"value": round(random.uniform(12, 25), 2), "label": "Fear Index"},
            "ten_year_yield": {"value": round(random.uniform(4.0, 5.0), 2)},
            "timestamp": datetime.now().isoformat(),
        }

    def get_fund_info(self, symbol: str) -> dict:
        """Get fund details (expense ratio, category, etc.)."""
        fund_data = {
            "FXAIX": {"expense_ratio": 0.015, "category": "Large Blend", "aum": "503.4B", "inception": "1988-02-17"},
            "FTEC": {"expense_ratio": 0.084, "category": "Technology", "aum": "11.2B", "inception": "2013-10-21"},
            "FHLC": {"expense_ratio": 0.084, "category": "Healthcare", "aum": "2.8B", "inception": "2013-10-21"},
            "FMAG": {"expense_ratio": 0.520, "category": "Large Growth", "aum": "18.7B", "inception": "1963-05-02"},
            "FBND": {"expense_ratio": 0.036, "category": "Intermediate Bond", "aum": "5.1B", "inception": "2021-10-06"},
        }
        return fund_data.get(symbol, {"expense_ratio": None, "category": "Unknown"})
