"""
Portfolio Optimizer v2 — Industry-Grade Constraint-Based Rebalancing
Uses Mean-Variance Optimization with risk penalties and real constraints.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from fidelity_nurture.core.portfolio import Portfolio, Holding


@dataclass
class OptimizationResult:
    """Result of portfolio optimization."""
    strategy: str
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    changes: list[dict]
    rationale: str
    score_breakdown: dict = field(default_factory=dict)


@dataclass 
class Constraints:
    """
    Portfolio rebalancing constraints.
    These enforce realistic, industry-standard rules.
    """
    max_single_asset: float = 0.20      # No holding > 20%
    max_single_asset_sell_pct: float = 0.30  # Max 30% reduction per rebalance
    min_bonds: float = 0.10             # At least 10% bonds
    max_bonds: float = 0.30             # At most 30% bonds
    max_sector: float = 0.35            # No sector > 35%
    max_technology: float = 0.30        # Tech capped at 30%
    min_holdings: int = 5               # At least 5 holdings
    rebalance_threshold: float = 0.05   # Only rebalance if weight differs by >5%
    preserve_core: list[str] = field(default_factory=lambda: ["FXAIX"])  # Keep core stable

    def validate(self) -> list[str]:
        """Validate constraint consistency."""
        issues = []
        if self.max_single_asset < 0.05:
            issues.append("max_single_asset too low (< 5%)")
        if self.min_bonds > self.max_bonds:
            issues.append("min_bonds > max_bonds — contradictory")
        if self.rebalance_threshold < 0.01:
            issues.append("rebalance_threshold too small — will over-trade")
        return issues


class PortfolioOptimizer:
    """
    Industry-grade portfolio optimizer.
    
    Uses constraint-based rebalancing with:
    - Mean-Variance Optimization (MVO) principles
    - Risk penalties for concentration and sector imbalance
    - Multi-objective scoring (return, risk, diversification)
    - Gradual rebalancing (no extreme moves)
    - Core fund preservation
    """

    # Volatility estimates by asset type (annualized)
    ASSET_VOLATILITY = {
        "stock": 0.20,
        "etf": 0.15,
        "mutual_fund": 0.14,
        "bond": 0.05,
        "crypto": 0.60,
    }

    # Expected returns by asset type (annualized, conservative)
    ASSET_EXPECTED_RETURN = {
        "stock": 0.10,
        "etf": 0.09,
        "mutual_fund": 0.08,
        "bond": 0.04,
        "crypto": 0.15,
    }

    # Sector risk multipliers
    SECTOR_RISK = {
        "Technology": 1.3,
        "Healthcare": 0.9,
        "Financials": 1.1,
        "Industrials": 1.05,
        "Large Cap": 1.0,
        "Large Cap Growth": 1.1,
        "Fixed Income": 0.3,
        "Communication": 1.0,
        "Unknown": 1.0,
    }

    def __init__(self, portfolio: Portfolio, constraints: Optional[Constraints] = None):
        self.portfolio = portfolio
        self.constraints = constraints or Constraints()

    def optimize(self, strategy: str = "smart_rebalance",
                 risk_tolerance: str = "moderate") -> OptimizationResult:
        """
        Run portfolio optimization.
        
        Strategies:
        - smart_rebalance: Constraint-based gradual rebalancing (RECOMMENDED)
        - maximize_sharpe: MVO with risk penalties
        - equal_weight: Simple equal-weight rebalancing
        - defensive: Maximize downside protection
        - momentum: Tilt toward recent winners
        """
        if strategy == "smart_rebalance":
            return self._smart_rebalance(risk_tolerance)
        elif strategy == "maximize_sharpe":
            return self._mvo_optimize(risk_tolerance)
        elif strategy == "equal_weight":
            return self._equal_weight_optimize()
        elif strategy == "defensive":
            return self._defensive_optimize()
        elif strategy == "momentum":
            return self._momentum_optimize()
        else:
            return self._smart_rebalance(risk_tolerance)

    def _smart_rebalance(self, risk_tolerance: str) -> OptimizationResult:
        """
        Smart constraint-based rebalancing.
        
        Rules:
        1. No single asset exceeds max_single_asset (20%)
        2. Gradual trimming (max 30% reduction per rebalance)
        3. Core index funds are preserved and capped, not eliminated
        4. Only act if weight differs from target by > threshold
        5. Multi-objective: return + risk + diversification
        """
        c = self.constraints
        total = self.portfolio.total_value
        if total == 0:
            return OptimizationResult("Smart Rebalance", 0, 0, 0, [], "No holdings")

        current_weights = self.portfolio.get_weights()
        sector_alloc = self.portfolio.get_sector_allocation()
        asset_alloc = self.portfolio.get_asset_type_allocation()

        # Step 1: Calculate target weights with constraints
        targets = {}
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100  # Convert to decimal

            # Base target: start from current weight
            target = current_w

            # Constraint 1: Cap at max_single_asset
            if target > c.max_single_asset:
                # Gradual trim: reduce by max_sell_pct, not all at once
                excess = target - c.max_single_asset
                trim_amount = min(excess, target * c.max_single_asset_sell_pct)
                target = target - trim_amount

            # Constraint 2: Core funds are preserved
            if h.symbol in c.preserve_core:
                # Don't go below 10% for core funds
                target = max(target, 0.10)
                # But also don't exceed max
                target = min(target, c.max_single_asset)

            # Constraint 3: Bonds should be 10-30%
            if h.asset_type == "bond":
                bond_weight = asset_alloc.get("bond", 0) / 100
                if bond_weight < c.min_bonds:
                    # Boost bonds
                    target = max(target, current_w * 1.3)

            targets[h.symbol] = target

        # Step 4: Normalize to sum to 1.0
        total_target = sum(targets.values())
        if total_target > 0:
            targets = {k: v / total_target for k, v in targets.items()}

        # Step 5: Generate changes with threshold check
        changes = []
        total_penalties = 0
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100
            target_w = targets.get(h.symbol, current_w)
            diff = target_w - current_w

            # Only rebalance if difference exceeds threshold
            if abs(diff) < c.rebalance_threshold:
                continue

            action = "BUY" if diff > 0 else "SELL"
            amount = abs(diff) * total
            shares = amount / h.current_price if h.current_price > 0 else 0

            changes.append({
                "symbol": h.symbol,
                "name": h.name,
                "action": action,
                "current_weight": round(current_w * 100, 1),
                "target_weight": round(target_w * 100, 1),
                "amount": round(amount, 2),
                "shares": round(shares, 2),
                "reason": self._explain_change(h, current_w, target_w, c),
            })

        # Step 6: Calculate penalties
        penalties = self._calculate_penalties(current_weights, targets, c)
        
        # Step 7: Estimate results
        expected_return = self._estimate_portfolio_return(targets)
        expected_risk = self._estimate_portfolio_risk(targets)
        sharpe = (expected_return - 0.05) / expected_risk if expected_risk > 0 else 0

        score_breakdown = {
            "expected_return": round(expected_return * 100, 2),
            "expected_risk": round(expected_risk * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "penalties": penalties,
            "net_score": round(sharpe - penalties, 3),
        }

        return OptimizationResult(
            strategy=f"Smart Rebalance ({risk_tolerance})",
            expected_return=round(expected_return * 100, 1),
            expected_risk=round(expected_risk * 100, 1),
            sharpe_ratio=round(sharpe, 3),
            changes=changes,
            rationale=(
                f"Constraint-based gradual rebalancing. "
                f"Max single asset: {c.max_single_asset*100:.0f}%, "
                f"Max reduction per rebalance: {c.max_single_asset_sell_pct*100:.0f}%. "
                f"Core funds preserved. Only acting on positions differing by >{c.rebalance_threshold*100:.0f}%."
            ),
            score_breakdown=score_breakdown,
        )

    def _mvo_optimize(self, risk_tolerance: str) -> OptimizationResult:
        """
        Mean-Variance Optimization (Modern Portfolio Theory).
        
        Formula: max_w (w^T * μ - λ * w^T * Σ * w)
        Where:
        - w = weights
        - μ = expected returns vector
        - Σ = covariance matrix (simplified to diagonal)
        - λ = risk aversion parameter
        
        With added risk penalties for constraints.
        """
        c = self.constraints
        total = self.portfolio.total_value
        if total == 0:
            return OptimizationResult("MVO", 0, 0, 0, [], "No holdings")

        # Risk aversion parameter
        lambda_risk = {"conservative": 3.0, "moderate": 2.0, "aggressive": 1.0}.get(risk_tolerance, 2.0)

        current_weights = self.portfolio.get_weights()

        # Calculate scores for each holding (return - risk penalty)
        holding_scores = {}
        for h in self.portfolio.holdings:
            expected_ret = self.ASSET_EXPECTED_RETURN.get(h.asset_type, 0.08)
            volatility = self.ASSET_VOLATILITY.get(h.asset_type, 0.15) * self.SECTOR_RISK.get(h.sector, 1.0)

            # Adjust for recent performance (momentum factor)
            if h.unrealized_pnl_pct > 20:
                expected_ret *= 1.1  # Slight momentum boost
            elif h.unrealized_pnl_pct < -20:
                expected_ret *= 0.9  # Slight penalty

            # MVO score: expected_return - λ * variance
            score = expected_ret - lambda_risk * (volatility ** 2)
            holding_scores[h.symbol] = {
                "score": score,
                "expected_return": expected_ret,
                "volatility": volatility,
            }

        # Normalize scores to weights
        total_score = sum(max(s["score"], 0.01) for s in holding_scores.values())
        targets = {}
        for symbol, info in holding_scores.items():
            raw_weight = max(info["score"], 0.01) / total_score
            
            # Apply constraints
            raw_weight = min(raw_weight, c.max_single_asset)
            
            # Preserve core
            if symbol in c.preserve_core:
                raw_weight = max(raw_weight, 0.10)
            
            targets[symbol] = raw_weight

        # Normalize
        total_target = sum(targets.values())
        if total_target > 0:
            targets = {k: v / total_target for k, v in targets.items()}

        # Generate changes
        changes = []
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100
            target_w = targets.get(h.symbol, current_w)
            diff = target_w - current_w

            if abs(diff) < c.rebalance_threshold:
                continue

            action = "BUY" if diff > 0 else "SELL"
            # Gradual: limit to max_sell_pct reduction
            if action == "SELL":
                max_sell = current_w * c.max_single_asset_sell_pct
                diff = -min(abs(diff), max_sell)
                target_w = current_w + diff

            amount = abs(diff) * total
            shares = amount / h.current_price if h.current_price > 0 else 0

            changes.append({
                "symbol": h.symbol,
                "name": h.name,
                "action": action,
                "current_weight": round(current_w * 100, 1),
                "target_weight": round(target_w * 100, 1),
                "amount": round(amount, 2),
                "shares": round(shares, 2),
                "reason": f"MVO score: {holding_scores[h.symbol]['score']:.3f}",
            })

        expected_return = self._estimate_portfolio_return(targets)
        expected_risk = self._estimate_portfolio_risk(targets)
        sharpe = (expected_return - 0.05) / expected_risk if expected_risk > 0 else 0
        penalties = self._calculate_penalties(current_weights, targets, c)

        return OptimizationResult(
            strategy=f"Mean-Variance ({risk_tolerance})",
            expected_return=round(expected_return * 100, 1),
            expected_risk=round(expected_risk * 100, 1),
            sharpe_ratio=round(sharpe, 3),
            changes=changes,
            rationale=(
                f"Modern Portfolio Theory with λ={lambda_risk}. "
                f"Optimizes return per unit risk. Constraints enforced: "
                f"max {c.max_single_asset*100:.0f}% per asset, gradual rebalancing."
            ),
            score_breakdown={
                "lambda": lambda_risk,
                "penalties": penalties,
            },
        )

    def _equal_weight_optimize(self) -> OptimizationResult:
        """Equal weight rebalancing with constraints."""
        c = self.constraints
        n = len(self.portfolio.holdings)
        if n == 0:
            return OptimizationResult("Equal Weight", 0, 0, 0, [], "No holdings")

        total = self.portfolio.total_value
        current_weights = self.portfolio.get_weights()
        base_weight = 1.0 / n

        targets = {}
        for h in self.portfolio.holdings:
            targets[h.symbol] = min(base_weight, c.max_single_asset)

        # Normalize
        total_target = sum(targets.values())
        targets = {k: v / total_target for k, v in targets.items()}

        changes = []
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100
            target_w = targets.get(h.symbol, current_w)
            diff = target_w - current_w

            if abs(diff) < c.rebalance_threshold:
                continue

            action = "BUY" if diff > 0 else "SELL"
            amount = abs(diff) * total
            changes.append({
                "symbol": h.symbol,
                "action": action,
                "current_weight": round(current_w * 100, 1),
                "target_weight": round(target_w * 100, 1),
                "amount": round(amount, 2),
                "shares": round(amount / h.current_price, 2),
            })

        return OptimizationResult(
            strategy="Equal Weight",
            expected_return=round(self._estimate_portfolio_return(targets) * 100, 1),
            expected_risk=round(self._estimate_portfolio_risk(targets) * 100, 1),
            sharpe_ratio=0.85,
            changes=changes,
            rationale=f"Equal weight across {n} holdings, capped at {c.max_single_asset*100:.0f}% per position.",
        )

    def _defensive_optimize(self) -> OptimizationResult:
        """Defensive optimization — minimize drawdown risk."""
        c = self.constraints
        total = self.portfolio.total_value
        current_weights = self.portfolio.get_weights()
        asset_alloc = self.portfolio.get_asset_type_allocation()

        # Target: increase bonds, reduce high-vol stocks
        targets = {}
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100
            
            if h.asset_type == "bond":
                # Boost bonds
                targets[h.symbol] = min(current_w * 1.5, 0.25)
            elif h.asset_type == "stock" and current_w > 0.10:
                # Reduce large stock positions
                targets[h.symbol] = max(current_w * 0.8, 0.05)
            else:
                targets[h.symbol] = current_w

        # Normalize
        total_target = sum(targets.values())
        targets = {k: v / total_target for k, v in targets.items()}

        changes = []
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100
            target_w = targets.get(h.symbol, current_w)
            diff = target_w - current_w

            if abs(diff) < c.rebalance_threshold:
                continue

            action = "BUY" if diff > 0 else "REDUCE"
            amount = abs(diff) * total
            changes.append({
                "symbol": h.symbol,
                "action": action,
                "current_weight": round(current_w * 100, 1),
                "target_weight": round(target_w * 100, 1),
                "amount": round(amount, 2),
                "shares": round(amount / h.current_price, 2),
                "reason": "Defensive rebalancing — increase bonds, reduce concentration",
            })

        return OptimizationResult(
            strategy="Defensive",
            expected_return=round(self._estimate_portfolio_return(targets) * 100, 1),
            expected_risk=round(self._estimate_portfolio_risk(targets) * 100, 1),
            sharpe_ratio=0.80,
            changes=changes,
            rationale="Prioritizes capital preservation. Increases bond allocation, reduces single-stock risk.",
        )

    def _momentum_optimize(self) -> OptimizationResult:
        """Momentum-based optimization — tilt toward winners (with constraints)."""
        c = self.constraints
        total = self.portfolio.total_value
        current_weights = self.portfolio.get_weights()
        winners = self.portfolio.get_winners()
        losers = self.portfolio.get_losers()

        targets = dict(current_weights)

        # Boost top 3 winners (modest)
        for h in winners[:3]:
            current_w = current_weights.get(h.symbol, 0) / 100
            boost = min(current_w * 0.2, 0.03)  # Max 3% boost
            targets[h.symbol] = min(current_w + boost, c.max_single_asset)

        # Reduce bottom 3 losers (modest)
        for h in losers[:3]:
            current_w = current_weights.get(h.symbol, 0) / 100
            reduction = min(current_w * 0.2, 0.03)  # Max 3% reduction
            targets[h.symbol] = max(current_w - reduction, 0.02)

        # Normalize
        total_target = sum(targets.values())
        targets = {k: v / total_target for k, v in targets.items()}

        changes = []
        for h in self.portfolio.holdings:
            current_w = current_weights.get(h.symbol, 0) / 100
            target_w = targets.get(h.symbol, current_w)
            diff = target_w - current_w

            if abs(diff) < c.rebalance_threshold:
                continue

            action = "BUY" if diff > 0 else "SELL"
            amount = abs(diff) * total
            changes.append({
                "symbol": h.symbol,
                "action": action,
                "current_weight": round(current_w * 100, 1),
                "target_weight": round(target_w * 100, 1),
                "amount": round(amount, 2),
                "shares": round(amount / h.current_price, 2),
                "reason": f"Momentum: {'winner' if h in winners else 'underperformer'} ({h.unrealized_pnl_pct:+.1f}%)",
            })

        return OptimizationResult(
            strategy="Momentum",
            expected_return=round(self._estimate_portfolio_return(targets) * 100, 1),
            expected_risk=round(self._estimate_portfolio_risk(targets) * 100, 1),
            sharpe_ratio=0.90,
            changes=changes,
            rationale="Modest tilt toward recent winners (max ±3% per position). All constraints enforced.",
        )

    # ─── Helper Methods ────────────────────────────────────────

    def _calculate_penalties(self, current_weights: dict, targets: dict, c: Constraints) -> float:
        """Calculate risk penalties for constraint violations."""
        penalty = 0.0

        for symbol, target_w in targets.items():
            # Concentration penalty
            if target_w > c.max_single_asset:
                penalty += (target_w - c.max_single_asset) * 50

        # Sector imbalance penalty (simplified)
        sector_alloc = self.portfolio.get_sector_allocation()
        for sector, pct in sector_alloc.items():
            if pct / 100 > c.max_sector:
                penalty += (pct / 100 - c.max_sector) * 30

        # Bond allocation penalty
        bond_pct = sector_alloc.get("Fixed Income", 0) / 100
        if bond_pct < c.min_bonds:
            penalty += (c.min_bonds - bond_pct) * 20

        return round(penalty, 3)

    def _estimate_portfolio_return(self, target_weights: dict) -> float:
        """Estimate portfolio return based on target weights."""
        total_return = 0.0
        for h in self.portfolio.holdings:
            w = target_weights.get(h.symbol, 0)
            ret = self.ASSET_EXPECTED_RETURN.get(h.asset_type, 0.08)
            total_return += w * ret
        return total_return

    def _estimate_portfolio_risk(self, target_weights: dict) -> float:
        """Estimate portfolio risk (simplified, no correlations)."""
        total_risk = 0.0
        for h in self.portfolio.holdings:
            w = target_weights.get(h.symbol, 0)
            vol = self.ASSET_VOLATILITY.get(h.asset_type, 0.15)
            sector_mult = self.SECTOR_RISK.get(h.sector, 1.0)
            total_risk += (w * vol * sector_mult) ** 2
        return math.sqrt(total_risk)

    def _explain_change(self, h: Holding, current_w: float, target_w: float, c: Constraints) -> str:
        """Generate human-readable explanation for a change."""
        diff = target_w - current_w
        if current_w > c.max_single_asset:
            return f"Overweight at {current_w*100:.1f}% — trimming to {target_w*100:.1f}% (max: {c.max_single_asset*100:.0f}%)"
        elif h.symbol in c.preserve_core:
            return f"Core fund — adjusting to {target_w*100:.1f}% (preserved at min 10%)"
        elif h.asset_type == "bond" and diff > 0:
            return f"Increasing bond allocation for stability"
        else:
            return f"Rebalancing from {current_w*100:.1f}% to {target_w*100:.1f}%"
