"""
Scenario Simulator — Stress test your portfolio against market events.
Simulate crashes, bull runs, sector rotations, and more.
"""

import random
from dataclasses import dataclass
from typing import Optional

from fidelity_nurture.core.portfolio import Portfolio, Holding


@dataclass
class ScenarioResult:
    """Result of a scenario simulation."""
    scenario_name: str
    description: str
    portfolio_impact: float       # Dollar change
    portfolio_impact_pct: float   # Percentage change
    worst_holding: dict           # Most affected holding
    best_holding: dict            # Least affected / benefiting holding
    new_total_value: float
    holdings_impact: list[dict]   # Per-holding breakdown


# Predefined market scenarios
SCENARIOS = {
    "crash_2008": {
        "name": "2008 Financial Crisis",
        "description": "Severe market crash similar to 2008. Stocks drop 40-50%, bonds hold steady.",
        "multipliers": {
            "stock": -0.45,
            "etf": -0.40,
            "mutual_fund": -0.38,
            "bond": 0.05,
            "crypto": -0.60,
        },
    },
    "covid_crash": {
        "name": "COVID-19 Crash (Mar 2020)",
        "description": "Sharp 30% drop followed by recovery. Tech recovers fastest.",
        "multipliers": {
            "stock": -0.30,
            "etf": -0.28,
            "mutual_fund": -0.25,
            "bond": 0.08,
            "crypto": -0.40,
        },
        "sector_bonus": {"Technology": 0.10, "Healthcare": 0.05},
    },
    "tech_bubble": {
        "name": "Tech Bubble Burst",
        "description": "Tech stocks crash 60%, other sectors drop 15%.",
        "multipliers": {
            "stock": -0.15,
            "etf": -0.20,
            "mutual_fund": -0.15,
            "bond": 0.03,
            "crypto": -0.30,
        },
        "sector_override": {"Technology": -0.60},
    },
    "bull_run": {
        "name": "Bull Market (+30%)",
        "description": "Strong bull market. Stocks gain 30-40%, bonds flat.",
        "multipliers": {
            "stock": 0.35,
            "etf": 0.30,
            "mutual_fund": 0.28,
            "bond": 0.02,
            "crypto": 0.50,
        },
    },
    "rate_hike": {
        "name": "Interest Rate Hike",
        "description": "Fed raises rates aggressively. Bonds drop, growth stocks hurt.",
        "multipliers": {
            "stock": -0.10,
            "etf": -0.08,
            "mutual_fund": -0.06,
            "bond": -0.12,
            "crypto": -0.20,
        },
        "sector_override": {"Technology": -0.20, "Financials": 0.05},
    },
    "inflation_spike": {
        "name": "High Inflation (7%+)",
        "description": "Inflation surges. Real assets outperform, bonds suffer.",
        "multipliers": {
            "stock": -0.05,
            "etf": -0.03,
            "mutual_fund": -0.02,
            "bond": -0.15,
            "crypto": 0.10,
        },
        "sector_override": {"Energy": 0.15, "Real Estate": 0.10},
    },
    "gradual_growth": {
        "name": "Gradual Growth (+15%)",
        "description": "Steady economic growth. All sectors positive.",
        "multipliers": {
            "stock": 0.15,
            "etf": 0.13,
            "mutual_fund": 0.12,
            "bond": 0.03,
            "crypto": 0.20,
        },
    },
    "black_swan": {
        "name": "Black Swan Event (-50%)",
        "description": "Extreme tail risk event. Everything crashes except treasury bonds.",
        "multipliers": {
            "stock": -0.50,
            "etf": -0.48,
            "mutual_fund": -0.45,
            "bond": 0.10,
            "crypto": -0.70,
        },
    },
}


class ScenarioSimulator:
    """
    Portfolio scenario simulator.
    
    Simulates how your portfolio would perform under different market conditions.
    Useful for stress testing and understanding downside risk.
    """

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def simulate(self, scenario_key: str) -> ScenarioResult:
        """Simulate a predefined scenario."""
        if scenario_key not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_key}. Available: {list(SCENARIOS.keys())}")

        scenario = SCENARIOS[scenario_key]
        return self._run_simulation(
            name=scenario["name"],
            description=scenario["description"],
            multipliers=scenario["multipliers"],
            sector_override=scenario.get("sector_override", {}),
            sector_bonus=scenario.get("sector_bonus", {}),
        )

    def simulate_custom(self, name: str, description: str,
                        stock_change: float = 0, bond_change: float = 0,
                        etf_change: float = 0, crypto_change: float = 0) -> ScenarioResult:
        """
        Simulate a custom scenario.
        
        Args:
            stock_change: % change for stocks (e.g., -0.20 = -20%)
            bond_change: % change for bonds
            etf_change: % change for ETFs
            crypto_change: % change for crypto
        """
        multipliers = {
            "stock": stock_change,
            "etf": etf_change,
            "mutual_fund": stock_change * 0.9,  # Slightly less volatile
            "bond": bond_change,
            "crypto": crypto_change,
        }
        return self._run_simulation(name, description, multipliers)

    def simulate_random(self, num_scenarios: int = 1000) -> dict:
        """
        Monte Carlo simulation — run random scenarios and aggregate results.
        
        Returns distribution of outcomes.
        """
        results = []
        for _ in range(num_scenarios):
            # Random multipliers
            market_move = random.gauss(0.08, 0.15)  # Mean 8%, std 15%
            multipliers = {
                "stock": market_move + random.gauss(0, 0.05),
                "etf": market_move * 0.9 + random.gauss(0, 0.04),
                "mutual_fund": market_move * 0.85 + random.gauss(0, 0.03),
                "bond": random.gauss(0.04, 0.03),
                "crypto": market_move * 1.5 + random.gauss(0, 0.20),
            }
            result = self._run_simulation("Monte Carlo", "", multipliers)
            results.append(result.portfolio_impact_pct)

        results.sort()
        return {
            "num_simulations": num_scenarios,
            "mean_return": round(sum(results) / len(results), 2),
            "median_return": round(results[len(results) // 2], 2),
            "best_case": round(results[-1], 2),
            "worst_case": round(results[0], 2),
            "percentile_5": round(results[int(len(results) * 0.05)], 2),
            "percentile_25": round(results[int(len(results) * 0.25)], 2),
            "percentile_75": round(results[int(len(results) * 0.75)], 2),
            "percentile_95": round(results[int(len(results) * 0.95)], 2),
            "prob_positive": round(sum(1 for r in results if r > 0) / len(results) * 100, 1),
            "prob_loss_20plus": round(sum(1 for r in results if r < -20) / len(results) * 100, 1),
        }

    def list_scenarios(self) -> list[dict]:
        """List all available scenarios."""
        return [
            {"key": k, "name": v["name"], "description": v["description"]}
            for k, v in SCENARIOS.items()
        ]

    def _run_simulation(self, name: str, description: str,
                        multipliers: dict, sector_override: dict = {},
                        sector_bonus: dict = {}) -> ScenarioResult:
        """Run a simulation with given multipliers."""
        total = self.portfolio.total_value
        holdings_impact = []
        total_change = 0.0

        for h in self.portfolio.holdings:
            # Get base multiplier
            base_mult = multipliers.get(h.asset_type, 0)

            # Apply sector override
            if h.sector in sector_override:
                base_mult = sector_override[h.sector]

            # Apply sector bonus
            if h.sector in sector_bonus:
                base_mult += sector_bonus[h.sector]

            # Add some randomness
            noise = random.gauss(0, 0.02)
            impact_pct = base_mult + noise
            impact_dollar = h.market_value * impact_pct

            holdings_impact.append({
                "symbol": h.symbol,
                "name": h.name,
                "current_value": round(h.market_value, 2),
                "change_pct": round(impact_pct * 100, 2),
                "change_dollar": round(impact_dollar, 2),
                "new_value": round(h.market_value + impact_dollar, 2),
            })
            total_change += impact_dollar

        new_total = total + total_change
        impact_pct = (total_change / total * 100) if total > 0 else 0

        # Find worst and best
        sorted_impacts = sorted(holdings_impact, key=lambda x: x["change_pct"])
        worst = sorted_impacts[0] if sorted_impacts else {}
        best = sorted_impacts[-1] if sorted_impacts else {}

        return ScenarioResult(
            scenario_name=name,
            description=description,
            portfolio_impact=round(total_change, 2),
            portfolio_impact_pct=round(impact_pct, 2),
            worst_holding=worst,
            best_holding=best,
            new_total_value=round(new_total, 2),
            holdings_impact=holdings_impact,
        )
