"""
NurtureFolio CLI v2 — Full-featured portfolio intelligence.

Usage:
    python -m fidelity_nurture                          # Full dashboard
    python -m fidelity_nurture analyze                  # Health score
    python -m fidelity_nurture risk                     # Risk assessment
    python -m fidelity_nurture optimize                 # Smart rebalance (default)
    python -m fidelity_nurture optimize --strategy mvo  # Mean-Variance Optimization
    python -m fidelity_nurture optimize --risk aggressive
    python -m fidelity_nurture simulate                 # List scenarios
    python -m fidelity_nurture simulate crash_2008      # Simulate specific scenario
    python -m fidelity_nurture simulate --monte-carlo   # Monte Carlo simulation
    python -m fidelity_nurture json                     # Export as JSON
    python -m fidelity_nurture --portfolio my_data.csv  # Load from CSV
"""

import sys
import json
import argparse
from pathlib import Path

from fidelity_nurture.core.portfolio import Portfolio
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor
from fidelity_nurture.ai.optimizer import PortfolioOptimizer, Constraints
from fidelity_nurture.ai.simulator import ScenarioSimulator
from fidelity_nurture.ui.dashboard import Dashboard


def parse_args():
    parser = argparse.ArgumentParser(
        prog="nurturefolio",
        description="💰 NurtureFolio — AI-Powered Portfolio Intelligence",
    )
    parser.add_argument("command", nargs="?", default="dashboard",
                        choices=["dashboard", "analyze", "risk", "optimize", "simulate", "json"],
                        help="Command to run")
    parser.add_argument("--portfolio", "-p", type=str, default=None,
                        help="Path to portfolio CSV file")
    parser.add_argument("--name", "-n", type=str, default="Portfolio",
                        help="Portfolio name")
    parser.add_argument("--strategy", "-s", type=str, default="smart_rebalance",
                        choices=["smart_rebalance", "maximize_sharpe", "equal_weight", "defensive", "momentum"],
                        help="Optimization strategy")
    parser.add_argument("--risk", "-r", type=str, default="moderate",
                        choices=["conservative", "moderate", "aggressive"],
                        help="Risk tolerance level")
    parser.add_argument("--max-asset", type=float, default=0.20,
                        help="Max single asset weight (default: 0.20 = 20%%)")
    parser.add_argument("--monte-carlo", action="store_true",
                        help="Run Monte Carlo simulation (1000 iterations)")
    parser.add_argument("--scenario", type=str, default=None,
                        help="Scenario key to simulate")
    parser.add_argument("--live", action="store_true",
                        help="Use live market data (requires yfinance)")
    parser.add_argument("--json-out", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    # Map command aliases
    if args.scenario:
        args.command = "simulate"

    return args


def load_portfolio(args) -> Portfolio:
    """Load portfolio from args."""
    if args.portfolio:
        return Portfolio.from_csv(args.portfolio, name=args.name)
    return Portfolio.sample_fidelity_portfolio()


def cmd_dashboard(portfolio, args):
    """Full terminal dashboard."""
    dashboard = Dashboard(portfolio)
    print(dashboard.render())


def cmd_analyze(portfolio, args):
    """Portfolio health analysis."""
    analyzer = PortfolioAnalyzer(portfolio)
    score = analyzer.analyze()

    if args.json_out:
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
            "diversification": analyzer.get_diversification_report(),
        }, indent=2))
    else:
        print(f"\n🏥 Portfolio Health Analysis")
        print(f"{'='*40}")
        print(f"  Overall Grade: {score.grade} ({score.overall:.0f}/100)")
        print(f"  Diversification: {score.diversification:.0f}/100")
        print(f"  Risk Management: {score.risk:.0f}/100")
        print(f"  Performance: {score.performance:.0f}/100")
        print(f"  Concentration: {score.concentration:.0f}/100")

        if score.warnings:
            print(f"\n⚠️  Warnings:")
            for w in score.warnings:
                print(f"  • {w}")

        if score.recommendations:
            print(f"\n💡 Recommendations:")
            for r in score.recommendations:
                print(f"  • {r}")


def cmd_risk(portfolio, args):
    """Risk assessment."""
    predictor = RiskPredictor(portfolio)
    risk = predictor.assess_risk()
    anomalies = predictor.detect_anomalies()

    if args.json_out:
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
    else:
        print(f"\n⚠️  Risk Assessment")
        print(f"{'='*40}")
        print(f"  Risk Level: {risk.risk_level} ({risk.risk_score:.0f}/100)")
        print(f"  Volatility: {risk.volatility_estimate:.1f}%")
        print(f"  Max Drawdown: {risk.max_drawdown_estimate:.1f}%")
        print(f"  Sharpe Ratio: {risk.sharpe_estimate:.2f}")
        print(f"  Beta: {risk.beta_estimate:.2f}")

        if risk.risk_factors:
            print(f"\n  Risk Factors:")
            for f in risk.risk_factors:
                print(f"    • {f}")

        if risk.mitigation_strategies:
            print(f"\n  Mitigations:")
            for m in risk.mitigation_strategies:
                print(f"    • {m}")

        if anomalies:
            print(f"\n🔍 Anomalies:")
            for a in anomalies:
                icon = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(a.severity, "•")
                print(f"  {icon} [{a.severity}] {a.description}")
                print(f"    → {a.recommendation}")


def cmd_optimize(portfolio, args):
    """Portfolio optimization."""
    constraints = Constraints(max_single_asset=args.max_asset)
    optimizer = PortfolioOptimizer(portfolio, constraints)

    if args.strategy == "all":
        strategies = ["smart_rebalance", "maximize_sharpe", "equal_weight", "defensive", "momentum"]
    else:
        strategies = [args.strategy]

    for strategy in strategies:
        result = optimizer.optimize(strategy=strategy, risk_tolerance=args.risk)

        if args.json_out:
            print(json.dumps({
                "strategy": result.strategy,
                "expected_return": result.expected_return,
                "expected_risk": result.expected_risk,
                "sharpe_ratio": result.sharpe_ratio,
                "changes": result.changes,
                "rationale": result.rationale,
                "score_breakdown": result.score_breakdown,
            }, indent=2))
        else:
            print(f"\n🎯 {result.strategy}")
            print(f"{'='*40}")
            print(f"  Expected Return: {result.expected_return}%")
            print(f"  Expected Risk: {result.expected_risk}%")
            print(f"  Sharpe Ratio: {result.sharpe_ratio}")
            print(f"\n  {result.rationale}")

            if result.changes:
                print(f"\n  Suggested Changes:")
                for c in result.changes:
                    action_icon = "🟢" if c["action"] == "BUY" else "🔴"
                    print(f"    {action_icon} {c['action']:>5} {c['symbol']:<8} "
                          f"{c['current_weight']}% → {c['target_weight']}% "
                          f"(${c['amount']:,.0f})")
                    if "reason" in c:
                        print(f"       └─ {c['reason']}")

            if result.score_breakdown:
                print(f"\n  Score Breakdown: {result.score_breakdown}")


def cmd_simulate(portfolio, args):
    """Scenario simulation."""
    simulator = ScenarioSimulator(portfolio)

    if args.monte_carlo:
        print(f"\n🎲 Running Monte Carlo Simulation (1000 iterations)...")
        mc = simulator.simulate_random(1000)
        if args.json_out:
            print(json.dumps(mc, indent=2))
        else:
            print(f"\n  Mean Return: {mc['mean_return']}%")
            print(f"  Median Return: {mc['median_return']}%")
            print(f"  Best Case: +{mc['best_case']}%")
            print(f"  Worst Case: {mc['worst_case']}%")
            print(f"  5th Percentile: {mc['percentile_5']}%")
            print(f"  95th Percentile: {mc['percentile_95']}%")
            print(f"  Probability of Gain: {mc['prob_positive']}%")
            print(f"  Probability of 20%+ Loss: {mc['prob_loss_20plus']}%")
        return

    if args.scenario:
        try:
            result = simulator.simulate(args.scenario)
        except ValueError as e:
            print(f"❌ {e}")
            print(f"\nAvailable scenarios:")
            for s in simulator.list_scenarios():
                print(f"  • {s['key']}: {s['name']}")
            return

        if args.json_out:
            print(json.dumps({
                "scenario": result.scenario_name,
                "description": result.description,
                "portfolio_impact": result.portfolio_impact,
                "portfolio_impact_pct": result.portfolio_impact_pct,
                "new_total_value": result.new_total_value,
                "worst": result.worst_holding,
                "best": result.best_holding,
                "holdings": result.holdings_impact,
            }, indent=2))
        else:
            print(f"\n🎭 Scenario: {result.scenario_name}")
            print(f"{'='*40}")
            print(f"  {result.description}")
            print(f"\n  Portfolio Impact: ${result.portfolio_impact:,.0f} ({result.portfolio_impact_pct:+.1f}%)")
            print(f"  New Total Value: ${result.new_total_value:,.0f}")
            print(f"\n  Worst: {result.worst_holding.get('symbol', 'N/A')} ({result.worst_holding.get('change_pct', 0):+.1f}%)")
            print(f"  Best:  {result.best_holding.get('symbol', 'N/A')} ({result.best_holding.get('change_pct', 0):+.1f}%)")
            print(f"\n  Holdings Impact:")
            for h in sorted(result.holdings_impact, key=lambda x: x["change_pct"]):
                color = "🟢" if h["change_pct"] >= 0 else "🔴"
                print(f"    {color} {h['symbol']:<8} {h['change_pct']:+.1f}% (${h['change_dollar']:+,.0f})")
        return

    # List scenarios
    print(f"\n🎭 Available Scenarios:")
    print(f"{'='*40}")
    for s in simulator.list_scenarios():
        print(f"  • {s['key']}: {s['name']}")
        print(f"    {s['description']}")
    print(f"\n  Usage: python -m fidelity_nurture simulate --scenario crash_2008")
    print(f"  Monte Carlo: python -m fidelity_nurture simulate --monte-carlo")


def cmd_json(portfolio, args):
    """Export full analysis as JSON."""
    analyzer = PortfolioAnalyzer(portfolio)
    predictor = RiskPredictor(portfolio)
    optimizer = PortfolioOptimizer(portfolio)
    simulator = ScenarioSimulator(portfolio)

    output = {
        "portfolio": portfolio.summary(),
        "health": {
            "score": analyzer.analyze().overall,
            "grade": analyzer.analyze().grade,
            "details": {
                "diversification": analyzer.analyze().diversification,
                "risk": analyzer.analyze().risk,
                "performance": analyzer.analyze().performance,
                "concentration": analyzer.analyze().concentration,
            },
        },
        "risk": {
            "level": predictor.assess_risk().risk_level,
            "score": predictor.assess_risk().risk_score,
            "volatility": predictor.assess_risk().volatility_estimate,
            "max_drawdown": predictor.assess_risk().max_drawdown_estimate,
        },
        "optimization": {
            "smart_rebalance": {
                "changes": optimizer.optimize("smart_rebalance").changes,
            },
        },
        "scenarios": {
            "crash_2008": simulator.simulate("crash_2008").portfolio_impact_pct,
            "bull_run": simulator.simulate("bull_run").portfolio_impact_pct,
            "monte_carlo": simulator.simulate_random(500),
        },
        "diversification": analyzer.get_diversification_report(),
    }
    print(json.dumps(output, indent=2))


def main():
    args = parse_args()
    portfolio = load_portfolio(args)

    commands = {
        "dashboard": cmd_dashboard,
        "analyze": cmd_analyze,
        "risk": cmd_risk,
        "optimize": cmd_optimize,
        "simulate": cmd_simulate,
        "json": cmd_json,
    }

    cmd = commands.get(args.command, cmd_dashboard)
    cmd(portfolio, args)


if __name__ == "__main__":
    main()
