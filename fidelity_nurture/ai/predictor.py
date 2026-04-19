"""
AI Risk Predictor — ML-powered risk assessment and anomaly detection.
Uses statistical models and pattern recognition to identify portfolio risks.
"""

import math
import random
from dataclasses import dataclass
from typing import Optional

from fidelity_nurture.core.portfolio import Portfolio, Holding


@dataclass
class RiskAssessment:
    """Complete risk assessment for a portfolio or holding."""
    risk_level: str          # LOW, MODERATE, HIGH, CRITICAL
    risk_score: float        # 0-100
    volatility_estimate: float  # Annualized volatility estimate
    max_drawdown_estimate: float  # Estimated max drawdown
    sharpe_estimate: float   # Estimated Sharpe ratio
    beta_estimate: float     # Portfolio beta estimate
    risk_factors: list[str]
    mitigation_strategies: list[str]


@dataclass
class Anomaly:
    """Detected anomaly in portfolio or holding."""
    severity: str            # INFO, WARNING, CRITICAL
    category: str            # allocation, performance, volatility, correlation
    description: str
    affected_symbols: list[str]
    recommendation: str


class RiskPredictor:
    """
    AI-powered risk prediction engine.
    
    Uses statistical analysis and heuristic models to:
    - Estimate portfolio volatility and drawdown risk
    - Detect anomalies in allocation and performance
    - Predict potential risk scenarios
    - Suggest risk mitigation strategies
    """

    # Volatility estimates by asset type (annualized)
    ASSET_VOLATILITY = {
        "stock": 0.20,
        "etf": 0.15,
        "mutual_fund": 0.14,
        "bond": 0.05,
        "crypto": 0.60,
    }

    # Sector beta estimates
    SECTOR_BETA = {
        "Technology": 1.3,
        "Healthcare": 0.9,
        "Financials": 1.1,
        "Industrials": 1.05,
        "Consumer": 0.85,
        "Energy": 1.2,
        "Utilities": 0.6,
        "Real Estate": 0.7,
        "Communication": 1.0,
        "Fixed Income": 0.1,
        "Large Cap": 1.0,
        "Large Cap Growth": 1.1,
        "Unknown": 1.0,
    }

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def assess_risk(self) -> RiskAssessment:
        """Run comprehensive risk assessment."""
        volatility = self._estimate_volatility()
        max_dd = self._estimate_max_drawdown(volatility)
        sharpe = self._estimate_sharpe(volatility)
        beta = self._estimate_beta()

        risk_score = self._calculate_risk_score(volatility, max_dd, beta)
        risk_level = self._classify_risk(risk_score)
        factors = self._identify_risk_factors(volatility, beta)
        mitigations = self._suggest_mitigations(risk_level, factors)

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=round(risk_score, 1),
            volatility_estimate=round(volatility * 100, 1),
            max_drawdown_estimate=round(max_dd * 100, 1),
            sharpe_estimate=round(sharpe, 2),
            beta_estimate=round(beta, 2),
            risk_factors=factors,
            mitigation_strategies=mitigations,
        )

    def detect_anomalies(self) -> list[Anomaly]:
        """Detect anomalies in the portfolio."""
        anomalies = []
        weights = self.portfolio.get_weights()
        sector_alloc = self.portfolio.get_sector_allocation()

        # 1. Single holding concentration anomaly
        for symbol, weight in weights.items():
            if weight > 25:
                holding = next(h for h in self.portfolio.holdings if h.symbol == symbol)
                anomalies.append(Anomaly(
                    severity="CRITICAL",
                    category="allocation",
                    description=f"{symbol} ({holding.name}) is {weight:.1f}% of portfolio — dangerously concentrated",
                    affected_symbols=[symbol],
                    recommendation=f"Reduce {symbol} to below 15% of total portfolio value",
                ))
            elif weight > 15:
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="allocation",
                    description=f"{symbol} is {weight:.1f}% of portfolio — moderately concentrated",
                    affected_symbols=[symbol],
                    recommendation=f"Consider trimming {symbol} to improve diversification",
                ))

        # 2. Sector over-concentration
        for sector, pct in sector_alloc.items():
            if pct > 50:
                anomalies.append(Anomaly(
                    severity="CRITICAL",
                    category="allocation",
                    description=f"{sector} sector is {pct:.1f}% of portfolio — severely overweight",
                    affected_symbols=[h.symbol for h in self.portfolio.holdings if h.sector == sector],
                    recommendation=f"Reduce {sector} to below 30% by adding other sectors",
                ))
            elif pct > 35:
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="allocation",
                    description=f"{sector} sector is {pct:.1f}% of portfolio — overweight",
                    affected_symbols=[h.symbol for h in self.portfolio.holdings if h.sector == sector],
                    recommendation=f"Consider reducing {sector} exposure below 30%",
                ))

        # 3. Performance outliers
        for h in self.portfolio.holdings:
            if h.unrealized_pnl_pct < -30:
                anomalies.append(Anomaly(
                    severity="CRITICAL",
                    category="performance",
                    description=f"{h.symbol} is down {abs(h.unrealized_pnl_pct):.1f}% — significant loss",
                    affected_symbols=[h.symbol],
                    recommendation=f"Review {h.symbol} fundamentals — consider stop-loss or exit strategy",
                ))
            elif h.unrealized_pnl_pct > 100:
                anomalies.append(Anomaly(
                    severity="INFO",
                    category="performance",
                    description=f"{h.symbol} is up {h.unrealized_pnl_pct:.1f}% — consider taking profits",
                    affected_symbols=[h.symbol],
                    recommendation=f"Lock in some gains on {h.symbol} to reduce concentration risk",
                ))

        # 4. Missing defensive allocation
        asset_alloc = self.portfolio.get_asset_type_allocation()
        if asset_alloc.get("bond", 0) < 5:
            anomalies.append(Anomaly(
                severity="WARNING",
                category="allocation",
                description="Portfolio has minimal bond allocation (< 5%) — low defensive positioning",
                affected_symbols=[],
                recommendation="Add 10-20% bonds or fixed income for downside protection",
            ))

        # 5. Cash drag
        if self.portfolio.cash_balance > 0:
            cash_pct = (self.portfolio.cash_balance / self.portfolio.total_value) * 100
            if cash_pct > 20:
                anomalies.append(Anomaly(
                    severity="INFO",
                    category="allocation",
                    description=f"Cash is {cash_pct:.1f}% of portfolio — potential cash drag on returns",
                    affected_symbols=[],
                    recommendation="Deploy excess cash into diversified investments or money market fund",
                ))

        return anomalies

    def _estimate_volatility(self) -> float:
        """Estimate annualized portfolio volatility using asset weights."""
        if not self.portfolio.holdings:
            return 0.0

        total = self.portfolio.total_value
        if total == 0:
            return 0.0

        # Weighted average volatility (simplified)
        weighted_vol = 0.0
        for h in self.portfolio.holdings:
            weight = h.market_value / total
            base_vol = self.ASSET_VOLATILITY.get(h.asset_type, 0.15)
            # Adjust for sector
            sector_adj = self.SECTOR_BETA.get(h.sector, 1.0)
            weighted_vol += weight * base_vol * sector_adj

        return weighted_vol

    def _estimate_max_drawdown(self, volatility: float) -> float:
        """Estimate maximum drawdown based on volatility."""
        # Rule of thumb: max drawdown ≈ 2-3x annual volatility
        return min(volatility * 2.5, 0.80)  # Cap at 80%

    def _estimate_sharpe(self, volatility: float) -> float:
        """Estimate Sharpe ratio."""
        if volatility == 0:
            return 0.0
        excess_return = self.portfolio.total_pnl_pct / 100
        risk_free = 0.05  # ~5% risk-free rate
        return (excess_return - risk_free) / volatility

    def _estimate_beta(self) -> float:
        """Estimate portfolio beta."""
        if not self.portfolio.holdings:
            return 1.0

        total = self.portfolio.total_value
        if total == 0:
            return 1.0

        weighted_beta = 0.0
        for h in self.portfolio.holdings:
            weight = h.market_value / total
            beta = self.SECTOR_BETA.get(h.sector, 1.0)
            weighted_beta += weight * beta

        return weighted_beta

    def _calculate_risk_score(self, volatility: float, max_dd: float, beta: float) -> float:
        """Calculate overall risk score (0-100)."""
        # Higher score = higher risk
        vol_score = min(volatility / 0.40 * 100, 100)  # 40% vol = 100
        dd_score = min(max_dd / 0.50 * 100, 100)       # 50% max dd = 100
        beta_score = min(beta / 1.5 * 100, 100)         # 1.5 beta = 100

        return (vol_score * 0.4 + dd_score * 0.3 + beta_score * 0.3)

    def _classify_risk(self, score: float) -> str:
        """Classify risk level."""
        if score < 25:
            return "LOW"
        elif score < 50:
            return "MODERATE"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"

    def _identify_risk_factors(self, volatility: float, beta: float) -> list[str]:
        """Identify key risk factors."""
        factors = []
        weights = self.portfolio.get_weights()
        sector_alloc = self.portfolio.get_sector_allocation()
        asset_alloc = self.portfolio.get_asset_type_allocation()

        if beta > 1.2:
            factors.append(f"High portfolio beta ({beta:.2f}) — more volatile than market")

        if volatility > 0.25:
            factors.append(f"High estimated volatility ({volatility*100:.1f}%)")

        tech_pct = sector_alloc.get("Technology", 0)
        if tech_pct > 35:
            factors.append(f"Technology concentration at {tech_pct:.1f}%")

        single_stock_max = max(weights.values()) if weights else 0
        if single_stock_max > 15:
            max_sym = max(weights, key=weights.get)
            factors.append(f"Single stock concentration: {max_sym} at {single_stock_max:.1f}%")

        if asset_alloc.get("crypto", 0) > 5:
            factors.append("Crypto exposure adds significant volatility")

        if asset_alloc.get("bond", 0) < 10:
            factors.append("Low bond allocation — limited downside protection")

        if len(self.portfolio.holdings) < 8:
            factors.append(f"Only {len(self.portfolio.holdings)} holdings — insufficient diversification")

        return factors

    def _suggest_mitigations(self, risk_level: str, factors: list[str]) -> list[str]:
        """Suggest risk mitigation strategies."""
        mitigations = []

        if risk_level in ("HIGH", "CRITICAL"):
            mitigations.append("🎯 Set stop-loss orders on individual positions (10-15% below cost)")
            mitigations.append("📊 Rebalance portfolio to reduce concentration")

        if any("Technology" in f for f in factors):
            mitigations.append("🔀 Diversify tech exposure across healthcare, utilities, and consumer staples")

        if any("Single stock" in f for f in factors):
            mitigations.append("✂️ Trim largest positions to under 10% each")

        if any("bond" in f.lower() for f in factors):
            mitigations.append("🛡️ Add 15-20% bonds or treasury ETFs for stability")

        if any("diversification" in f.lower() for f in factors):
            mitigations.append("🌐 Add 3-5 more holdings across different sectors")

        if not mitigations:
            mitigations.append("✅ Portfolio risk is well-managed — continue monitoring")

        return mitigations
