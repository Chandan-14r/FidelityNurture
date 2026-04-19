"""
Portfolio Analyzer — Deep analysis of portfolio health, risk, and diversification.
"""

import math
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from fidelity_nurture.core.portfolio import Portfolio, Holding


@dataclass
class HealthScore:
    """Portfolio health assessment."""
    overall: float  # 0-100
    diversification: float
    risk: float
    performance: float
    concentration: float
    grade: str  # A+, A, B+, B, C+, C, D, F
    warnings: list[str]
    recommendations: list[str]


class PortfolioAnalyzer:
    """
    Comprehensive portfolio analysis engine.
    
    Evaluates portfolio health across multiple dimensions:
    - Diversification (sector, asset type, individual holdings)
    - Concentration risk
    - Performance metrics
    - Risk-adjusted returns
    """

    # Ideal ranges for a balanced portfolio
    IDEAL_SECTOR_MAX = 30.0      # No sector > 30%
    IDEAL_HOLDING_MAX = 15.0      # No single holding > 15%
    IDEAL_STOCK_MIN = 40.0        # At least 40% stocks
    IDEAL_BOND_MIN = 10.0         # At least 10% bonds
    IDEAL_MIN_HOLDINGS = 8        # At least 8 holdings

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self._warnings: list[str] = []
        self._recommendations: list[str] = []

    def analyze(self) -> HealthScore:
        """Run full portfolio analysis and return health score."""
        div_score = self._score_diversification()
        risk_score = self._score_risk()
        perf_score = self._score_performance()
        conc_score = self._score_concentration()

        overall = (div_score * 0.30 + risk_score * 0.25 +
                   perf_score * 0.25 + conc_score * 0.20)

        return HealthScore(
            overall=round(overall, 1),
            diversification=round(div_score, 1),
            risk=round(risk_score, 1),
            performance=round(perf_score, 1),
            concentration=round(conc_score, 1),
            grade=self._calculate_grade(overall),
            warnings=self._warnings,
            recommendations=self._recommendations,
        )

    def _score_diversification(self) -> float:
        """Score diversification (0-100)."""
        score = 100.0
        holdings = self.portfolio.holdings

        if not holdings:
            return 0.0

        # Check number of holdings
        if len(holdings) < self.IDEAL_MIN_HOLDINGS:
            penalty = (self.IDEAL_MIN_HOLDINGS - len(holdings)) * 8
            score -= penalty
            self._warnings.append(f"Only {len(holdings)} holdings — consider adding more for diversification")
            self._recommendations.append(f"Aim for at least {self.IDEAL_MIN_HOLDINGS} holdings across different sectors")

        # Check sector diversity
        sectors = self.portfolio.get_sector_allocation()
        num_sectors = len(sectors)
        if num_sectors < 4:
            penalty = (4 - num_sectors) * 10
            score -= penalty
            self._warnings.append(f"Only {num_sectors} sectors represented")
            self._recommendations.append("Diversify across at least 4-5 sectors")

        # Check Herfindahl-Hirschman Index (concentration)
        weights = self.portfolio.get_weights()
        hhi = sum((w / 100) ** 2 for w in weights.values())
        if hhi > 0.25:  # Highly concentrated
            score -= 20
            self._warnings.append("Portfolio is highly concentrated (HHI > 0.25)")
        elif hhi > 0.15:
            score -= 10
            self._warnings.append("Portfolio is moderately concentrated")

        return max(0, score)

    def _score_risk(self) -> float:
        """Score risk profile (0-100, higher = better risk management)."""
        score = 100.0

        if not self.portfolio.holdings:
            return 0.0

        asset_alloc = self.portfolio.get_asset_type_allocation()
        sector_alloc = self.portfolio.get_sector_allocation()

        # Tech overweight check
        tech_pct = sector_alloc.get("Technology", 0)
        if tech_pct > 40:
            score -= 20
            self._warnings.append(f"Technology sector is {tech_pct:.1f}% — overexposed")
            self._recommendations.append("Reduce tech exposure below 35% for better risk balance")

        # Bond allocation check
        bond_pct = asset_alloc.get("bond", 0) + asset_alloc.get("mutual_fund", 0) * 0.1
        if bond_pct < self.IDEAL_BOND_MIN:
            score -= 15
            self._warnings.append(f"Fixed income only {bond_pct:.1f}% — low defensive allocation")
            self._recommendations.append(f"Consider adding bonds for stability (target: {self.IDEAL_BOND_MIN}%+)")

        # Single stock risk
        weights = self.portfolio.get_weights()
        for symbol, weight in weights.items():
            holding = next(h for h in self.portfolio.holdings if h.symbol == symbol)
            if holding.asset_type == "stock" and weight > 20:
                score -= 15
                self._warnings.append(f"{symbol} is {weight}% of portfolio — single stock risk")

        # Crypto risk (if any)
        crypto_pct = asset_alloc.get("crypto", 0)
        if crypto_pct > 10:
            score -= 10
            self._warnings.append(f"Crypto allocation at {crypto_pct:.1f}% — high volatility risk")

        return max(0, score)

    def _score_performance(self) -> float:
        """Score portfolio performance (0-100)."""
        if not self.portfolio.holdings:
            return 50.0

        pnl_pct = self.portfolio.total_pnl_pct

        if pnl_pct > 30:
            return 95.0
        elif pnl_pct > 20:
            return 85.0
        elif pnl_pct > 10:
            return 75.0
        elif pnl_pct > 5:
            return 65.0
        elif pnl_pct > 0:
            return 55.0
        elif pnl_pct > -5:
            return 45.0
        elif pnl_pct > -10:
            return 35.0
        elif pnl_pct > -20:
            return 25.0
        else:
            self._warnings.append(f"Portfolio is down {abs(pnl_pct):.1f}% — significant losses")
            self._recommendations.append("Review underperforming holdings and consider rebalancing")
            return 15.0

    def _score_concentration(self) -> float:
        """Score concentration risk (0-100, higher = better diversified)."""
        score = 100.0

        if not self.portfolio.holdings:
            return 0.0

        weights = self.portfolio.get_weights()
        sector_alloc = self.portfolio.get_sector_allocation()

        # Check individual holding concentration
        max_weight = max(weights.values()) if weights else 0
        if max_weight > self.IDEAL_HOLDING_MAX:
            penalty = (max_weight - self.IDEAL_HOLDING_MAX) * 2
            score -= penalty
            max_sym = max(weights, key=weights.get)
            self._warnings.append(f"{max_sym} makes up {max_weight:.1f}% of portfolio")

        # Check sector concentration
        max_sector = max(sector_alloc.values()) if sector_alloc else 0
        if max_sector > self.IDEAL_SECTOR_MAX:
            penalty = (max_sector - self.IDEAL_SECTOR_MAX) * 1.5
            score -= penalty
            max_sec = max(sector_alloc, key=sector_alloc.get)
            self._warnings.append(f"{max_sec} sector makes up {max_sector:.1f}% — overconcentrated")
            self._recommendations.append(f"Reduce {max_sec} exposure to below {self.IDEAL_SECTOR_MAX}%")

        return max(0, score)

    def _calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def get_rebalance_suggestions(self) -> list[dict]:
        """
        Generate rebalancing suggestions based on target allocation.
        Returns list of buy/sell recommendations.
        """
        suggestions = []
        weights = self.portfolio.get_weights()
        total = self.portfolio.total_value

        if total == 0:
            return suggestions

        sector_alloc = self.portfolio.get_sector_allocation()

        # Suggest trimming overweight positions
        for symbol, weight in weights.items():
            holding = next(h for h in self.portfolio.holdings if h.symbol == symbol)
            if weight > self.IDEAL_HOLDING_MAX:
                target_pct = self.IDEAL_HOLDING_MAX
                excess_value = (weight - target_pct) / 100 * total
                shares_to_sell = excess_value / holding.current_price
                suggestions.append({
                    "action": "REDUCE",
                    "symbol": symbol,
                    "name": holding.name,
                    "current_weight": weight,
                    "target_weight": target_pct,
                    "shares_to_sell": round(shares_to_sell, 2),
                    "value_to_sell": round(excess_value, 2),
                    "reason": f"Overweight at {weight:.1f}% — trim to {target_pct}%",
                })

        # Suggest adding to underweight sectors
        for sector, pct in sector_alloc.items():
            if pct < 10 and sector not in ("Fixed Income",):
                suggestions.append({
                    "action": "CONSIDER",
                    "sector": sector,
                    "current_pct": pct,
                    "target_pct": 15,
                    "reason": f"{sector} is only {pct:.1f}% — consider increasing exposure",
                })

        return suggestions

    def get_diversification_report(self) -> dict:
        """Detailed diversification breakdown."""
        return {
            "by_sector": self.portfolio.get_sector_allocation(),
            "by_asset_type": self.portfolio.get_asset_type_allocation(),
            "by_holding": self.portfolio.get_weights(),
            "top_5_holdings": [
                {
                    "symbol": h.symbol,
                    "name": h.name,
                    "weight": self.portfolio.get_weights().get(h.symbol, 0),
                    "pnl_pct": round(h.unrealized_pnl_pct, 2),
                }
                for h in self.portfolio.get_top_holdings(5)
            ],
            "winners": [
                {"symbol": h.symbol, "pnl_pct": round(h.unrealized_pnl_pct, 2)}
                for h in self.portfolio.get_winners()[:3]
            ],
            "losers": [
                {"symbol": h.symbol, "pnl_pct": round(h.unrealized_pnl_pct, 2)}
                for h in self.portfolio.get_losers()[:3]
            ],
        }
