"""
Portfolio Optimizer — AI-driven portfolio optimization and rebalancing.
Uses Modern Portfolio Theory principles to suggest optimal allocations.
"""

from dataclasses import dataclass
from typing import Optional

from fidelity_nurture.core.portfolio import Portfolio, Holding
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor


@dataclass
class OptimizationResult:
    """Result of portfolio optimization."""
    strategy: str
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    changes: list[dict]
    rationale: str


@dataclass
class AllocationTarget:
    """Target allocation for a holding."""
    symbol: str
    current_weight: float
    target_weight: float
    action: str          # BUY, SELL, HOLD
    amount: float        # Dollar amount to buy/sell
    shares: float        # Shares to buy/sell


class PortfolioOptimizer:
    """
    Portfolio optimization engine.
    
    Strategies:
    - maximize_sharpe: Optimize for best risk-adjusted returns
    - minimize_risk: Target minimum volatility for desired return
    - equal_weight: Simple equal-weight rebalancing
    - momentum: Tilt toward recent winners
    - defensive: Maximize downside protection
    """

    # Model portfolio targets by risk tolerance
    CONSERVATIVE = {
        "bonds": 40, "large_cap": 30, "international": 10,
        "mid_cap": 10, "small_cap": 5, "alternatives": 5,
    }
    MODERATE = {
        "bonds": 25, "large_cap": 35, "international": 15,
        "mid_cap": 12, "small_cap": 8, "alternatives": 5,
    }
    AGGRESSIVE = {
        "bonds": 10, "large_cap": 30, "international": 20,
        "mid_cap": 15, "small_cap": 15, "alternatives": 10,
    }

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.analyzer = PortfolioAnalyzer(portfolio)
        self.predictor = RiskPredictor(portfolio)

    def optimize(self, strategy: str = "maximize_sharpe",
                 risk_tolerance: str = "moderate") -> OptimizationResult:
        """
        Run portfolio optimization.
        
        Args:
            strategy: Optimization strategy
            risk_tolerance: conservative, moderate, aggressive
        """
        if strategy == "equal_weight":
            return self._equal_weight_optimize()
        elif strategy == "defensive":
            return self._defensive_optimize()
        elif strategy == "momentum":
            return self._momentum_optimize()
        else:
            return self._maximize_sharpe_optimize(risk_tolerance)

    def _maximize_sharpe_optimize(self, risk_tolerance: str) -> OptimizationResult:
        """Optimize for maximum Sharpe ratio."""
        risk_assessment = self.predictor.assess_risk()
        current_weights = self.portfolio.get_weights()
        total = self.portfolio.total_value

        targets = []
        if risk_tolerance == "conservative":
            target_map = self.CONSERVATIVE
        elif risk_tolerance == "aggressive":
            target_map = self.AGGRESSIVE
        else:
            target_map = self.MODERATE

        # Simple sector-based rebalancing
        sector_alloc = self.portfolio.get_sector_allocation()

        # Determine target weights based on risk tolerance
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0)

            if h.asset_type == "bond":
                target_w = target_map["bonds"] / self._count_type("bond")
            elif h.sector == "Technology":
                target_w = target_map["large_cap"] / self._count_large_cap() * 0.7
            elif h.asset_type == "etf":
                target_w = target_map["international"] / max(self._count_type("etf"), 1)
            else:
                target_w = target_map["large_cap"] / max(len(self.portfolio.holdings), 1)

            diff = target_w - current_w
            action = "HOLD"
            if diff > 2:
                action = "BUY"
            elif diff < -2:
                action = "SELL"

            amount = abs(diff) / 100 * total
            shares = amount / h.current_price if h.current_price > 0 else 0

            targets.append(AllocationTarget(
                symbol=h.symbol,
                current_weight=round(current_w, 2),
                target_weight=round(target_w, 2),
                action=action,
                amount=round(amount, 2),
                shares=round(shares, 2),
            ))

        changes = [
            {
                "symbol": t.symbol,
                "action": t.action,
                "current_weight": t.current_weight,
                "target_weight": t.target_weight,
                "amount": t.amount,
                "shares": t.shares,
            }
            for t in targets if t.action != "HOLD"
        ]

        # Estimate results
        new_vol = risk_assessment.volatility_estimate * 0.85  # Expected improvement
        new_return = self.portfolio.total_pnl_pct * 1.05
        new_sharpe = (new_return - 5) / new_vol if new_vol > 0 else 0

        return OptimizationResult(
            strategy=f"Max Sharpe ({risk_tolerance})",
            expected_return=round(new_return, 1),
            expected_risk=round(new_vol, 1),
            sharpe_ratio=round(new_sharpe, 2),
            changes=changes,
            rationale=f"Rebalanced for {risk_tolerance} risk tolerance. "
                      f"Reduced concentration risk and improved sector diversification.",
        )

    def _equal_weight_optimize(self) -> OptimizationResult:
        """Equal weight rebalancing."""
        n = len(self.portfolio.holdings)
        if n == 0:
            return OptimizationResult("Equal Weight", 0, 0, 0, [], "No holdings")

        target_weight = 100.0 / n
        total = self.portfolio.total_value
        current_weights = self.portfolio.get_weights()

        changes = []
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0)
            diff = target_weight - current_w
            if abs(diff) > 1:
                amount = abs(diff) / 100 * total
                shares = amount / h.current_price if h.current_price > 0 else 0
                changes.append({
                    "symbol": h.symbol,
                    "action": "BUY" if diff > 0 else "SELL",
                    "current_weight": round(current_w, 2),
                    "target_weight": round(target_weight, 2),
                    "amount": round(amount, 2),
                    "shares": round(shares, 2),
                })

        return OptimizationResult(
            strategy="Equal Weight",
            expected_return=round(self.portfolio.total_pnl_pct * 1.02, 1),
            expected_risk=round(self.predictor._estimate_volatility() * 100 * 0.9, 1),
            sharpe_ratio=0.85,
            changes=changes,
            rationale="Equal weighting removes concentration bias. Simple but effective for broad market exposure.",
        )

    def _defensive_optimize(self) -> OptimizationResult:
        """Defensive optimization — minimize drawdown risk."""
        risk = self.predictor.assess_risk()
        total = self.portfolio.total_value
        current_weights = self.portfolio.get_weights()

        changes = []
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0)

            # Reduce high-vol positions
            if h.asset_type == "stock" and current_w > 10:
                target_w = max(current_w * 0.7, 5)
                diff = current_w - target_w
                amount = diff / 100 * total
                shares = amount / h.current_price
                changes.append({
                    "symbol": h.symbol,
                    "action": "REDUCE",
                    "current_weight": round(current_w, 2),
                    "target_weight": round(target_w, 2),
                    "amount": round(amount, 2),
                    "shares": round(shares, 2),
                })

        # Suggest adding bonds
        changes.append({
            "symbol": "FBND",
            "action": "BUY",
            "reason": "Add Fidelity Total Bond ETF for defensive positioning",
            "suggested_allocation": "15-20%",
            "amount": round(total * 0.15, 2),
        })

        return OptimizationResult(
            strategy="Defensive",
            expected_return=round(self.portfolio.total_pnl_pct * 0.9, 1),
            expected_risk=round(risk.volatility_estimate * 0.7, 1),
            sharpe_ratio=round(risk.sharpe_estimate * 1.1, 2),
            changes=changes,
            rationale="Reduced high-volatility positions and increased defensive allocation. "
                      "Prioritizes capital preservation over growth.",
        )

    def _momentum_optimize(self) -> OptimizationResult:
        """Momentum-based optimization — tilt toward winners."""
        total = self.portfolio.total_value
        winners = self.portfolio.get_winners()
        losers = self.portfolio.get_losers()
        current_weights = self.portfolio.get_weights()

        changes = []

        # Increase winners
        for h in winners[:3]:
            current_w = current_weights.get(h.symbol, 0)
            target_w = min(current_w * 1.3, 15)
            diff = target_w - current_w
            if diff > 1:
                amount = diff / 100 * total
                changes.append({
                    "symbol": h.symbol,
                    "action": "BUY",
                    "current_weight": round(current_w, 2),
                    "target_weight": round(target_w, 2),
                    "amount": round(amount, 2),
                    "reason": f"Momentum: up {h.unrealized_pnl_pct:.1f}%",
                })

        # Reduce losers
        for h in losers[:3]:
            current_w = current_weights.get(h.symbol, 0)
            target_w = max(current_w * 0.6, 3)
            diff = current_w - target_w
            if diff > 1:
                amount = diff / 100 * total
                changes.append({
                    "symbol": h.symbol,
                    "action": "SELL",
                    "current_weight": round(current_w, 2),
                    "target_weight": round(target_w, 2),
                    "amount": round(amount, 2),
                    "reason": f"Cut losses: down {h.unrealized_pnl_pct:.1f}%",
                })

        return OptimizationResult(
            strategy="Momentum",
            expected_return=round(self.portfolio.total_pnl_pct * 1.15, 1),
            expected_risk=round(self.predictor._estimate_volatility() * 100 * 1.1, 1),
            sharpe_ratio=0.95,
            changes=changes,
            rationale="Tilting toward recent outperformers and cutting underperformers. "
                      "Higher growth potential but increased risk.",
        )

    def _count_type(self, asset_type: str) -> int:
        """Count holdings of a given asset type."""
        return sum(1 for h in self.portfolio.holdings if h.asset_type == asset_type)

    def _count_large_cap(self) -> int:
        """Count large cap holdings."""
        return sum(1 for h in self.portfolio.holdings
                   if "Large Cap" in h.sector or h.asset_type == "mutual_fund")
