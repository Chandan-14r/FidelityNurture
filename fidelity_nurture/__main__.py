"""
NurtureFolio CLI — Command-line interface for portfolio analysis.

Usage:
    python -m fidelity_nurture              # Run demo with sample portfolio
    python -m fidelity_nurture analyze      # Analyze sample Fidelity portfolio
    python -m fidelity_nurture optimize     # Run optimization
    python -m fidelity_nurture risk         # Risk assessment only
    python -m fidelity_nurture demo         # Full dashboard demo
"""

import sys
import json
from pathlib import Path

from fidelity_nurture.core.portfolio import Portfolio
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor
from fidelity_nurture.ai.optimizer import PortfolioOptimizer
from fidelity_nurture.ui.dashboard import Dashboard


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    command = args[0] if args else "demo"

    # Load sample portfolio
    portfolio = Portfolio.sample_fidelity_portfolio()

    if command == "analyze":
        analyzer = PortfolioAnalyzer(portfolio)
        score = analyzer.analyze()
        print(json.dumps({
            "health_score": {
                "overall": score.overall,
                "grade": score.grade,
                "diversification": score.diversification,
                "risk": score.risk,
                "performance": score.performance,
                "concentration": score.concentration,
            },
            "warnings": score.warnings,
            "recommendations": score.recommendations,
            "rebalance": analyzer.get_rebalance_suggestions(),
        }, indent=2))

    elif command == "risk":
        predictor = RiskPredictor(portfolio)
        risk = predictor.assess_risk()
        anomalies = predictor.detect_anomalies()
        print(json.dumps({
            "risk_assessment": {
                "level": risk.risk_level,
                "score": risk.risk_score,
                "volatility": risk.volatility_estimate,
                "max_drawdown": risk.max_drawdown_estimate,
                "sharpe": risk.sharpe_estimate,
                "beta": risk.beta_estimate,
                "factors": risk.risk_factors,
                "mitigations": risk.mitigation_strategies,
            },
            "anomalies": [
                {"severity": a.severity, "category": a.category,
                 "description": a.description, "recommendation": a.recommendation}
                for a in anomalies
            ],
        }, indent=2))

    elif command == "optimize":
        optimizer = PortfolioOptimizer(portfolio)
        for strategy in ["maximize_sharpe", "equal_weight", "defensive", "momentum"]:
            result = optimizer.optimize(strategy=strategy)
            print(f"\n{'='*50}")
            print(f"Strategy: {result.strategy}")
            print(f"Expected Return: {result.expected_return}%")
            print(f"Expected Risk: {result.expected_risk}%")
            print(f"Sharpe: {result.sharpe_ratio}")
            if result.changes:
                print("Changes:")
                for c in result.changes[:5]:
                    print(f"  {c['action']} {c['symbol']}: {c['current_weight']}% → {c['target_weight']}%")

    elif command == "json":
        # Export portfolio analysis as JSON
        analyzer = PortfolioAnalyzer(portfolio)
        predictor = RiskPredictor(portfolio)
        print(json.dumps({
            "portfolio": portfolio.summary(),
            "health": {
                "score": analyzer.analyze().overall,
                "grade": analyzer.analyze().grade,
            },
            "risk": {
                "level": predictor.assess_risk().risk_level,
                "score": predictor.assess_risk().risk_score,
            },
            "diversification": analyzer.get_diversification_report(),
        }, indent=2))

    else:  # demo or default
        dashboard = Dashboard(portfolio)
        print(dashboard.render())


if __name__ == "__main__":
    main()
