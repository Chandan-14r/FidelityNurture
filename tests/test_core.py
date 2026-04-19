"""
Tests for NurtureFolio v2 — constraint-based optimizer + simulator.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fidelity_nurture.core.portfolio import Portfolio, Holding
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor
from fidelity_nurture.ai.optimizer import PortfolioOptimizer, Constraints
from fidelity_nurture.ai.simulator import ScenarioSimulator


def test_portfolio_creation():
    p = Portfolio(name="Test")
    h = Holding("AAPL", "Apple", 10, 150.0, 200.0, "Technology", "stock")
    p.add_holding(h)
    assert p.total_value == 2000.0
    assert p.total_cost == 1500.0
    assert p.total_pnl == 500.0
    print("✅ test_portfolio_creation passed")


def test_holding_merge():
    p = Portfolio()
    p.add_holding(Holding("AAPL", "Apple", 10, 150.0, 200.0))
    p.add_holding(Holding("AAPL", "Apple", 5, 180.0, 200.0))
    assert len(p.holdings) == 1
    assert p.holdings[0].shares == 15
    assert p.holdings[0].avg_cost == 160.0
    print("✅ test_holding_merge passed")


def test_weights():
    p = Portfolio()
    p.add_holding(Holding("AAPL", "Apple", 10, 100.0, 200.0))
    p.add_holding(Holding("MSFT", "Microsoft", 5, 300.0, 400.0))
    weights = p.get_weights()
    assert weights["AAPL"] == 50.0
    assert weights["MSFT"] == 50.0
    print("✅ test_weights passed")


def test_analyzer():
    p = Portfolio.sample_fidelity_portfolio()
    analyzer = PortfolioAnalyzer(p)
    score = analyzer.analyze()
    assert 0 <= score.overall <= 100
    assert score.grade in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F")
    print(f"✅ test_analyzer passed (score: {score.overall}, grade: {score.grade})")


def test_risk_predictor():
    p = Portfolio.sample_fidelity_portfolio()
    predictor = RiskPredictor(p)
    risk = predictor.assess_risk()
    assert risk.risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert 0 <= risk.risk_score <= 100
    print(f"✅ test_risk_predictor passed (risk: {risk.risk_level})")


def test_anomaly_detection():
    p = Portfolio.sample_fidelity_portfolio()
    predictor = RiskPredictor(p)
    anomalies = predictor.detect_anomalies()
    assert isinstance(anomalies, list)
    for a in anomalies:
        assert a.severity in ("INFO", "WARNING", "CRITICAL")
    print(f"✅ test_anomaly_detection passed ({len(anomalies)} anomalies)")


def test_constraints():
    """Test that constraints are enforced."""
    c = Constraints(
        max_single_asset=0.20,
        max_single_asset_sell_pct=0.30,
        min_bonds=0.10,
    )
    issues = c.validate()
    assert len(issues) == 0, f"Constraint validation failed: {issues}"
    print("✅ test_constraints passed")


def test_smart_rebalance_no_extreme_moves():
    """Test that smart rebalance doesn't make extreme moves (e.g., 37% → 2.9%)."""
    p = Portfolio.sample_fidelity_portfolio()
    c = Constraints(max_single_asset=0.20, max_single_asset_sell_pct=0.30)
    optimizer = PortfolioOptimizer(p, c)
    result = optimizer.optimize(strategy="smart_rebalance")

    # Check that no change reduces by more than 30%
    for change in result.changes:
        if change["action"] == "SELL":
            reduction = change["current_weight"] - change["target_weight"]
            max_allowed = change["current_weight"] * 0.30
            assert reduction <= max_allowed + 1, \
                f"{change['symbol']}: reduced by {reduction:.1f}% (max allowed: {max_allowed:.1f}%)"

    print(f"✅ test_smart_rebalance_no_extreme_moves passed ({len(result.changes)} changes)")


def test_mvo_optimization():
    """Test Mean-Variance Optimization."""
    p = Portfolio.sample_fidelity_portfolio()
    optimizer = PortfolioOptimizer(p)
    result = optimizer.optimize(strategy="maximize_sharpe", risk_tolerance="moderate")
    assert result.strategy is not None
    assert result.sharpe_ratio != 0
    print(f"✅ test_mvo_optimization passed (Sharpe: {result.sharpe_ratio})")


def test_all_strategies():
    """Test all optimization strategies run without error."""
    p = Portfolio.sample_fidelity_portfolio()
    optimizer = PortfolioOptimizer(p)
    for strategy in ["smart_rebalance", "maximize_sharpe", "equal_weight", "defensive", "momentum"]:
        result = optimizer.optimize(strategy=strategy)
        assert result.strategy is not None
        assert isinstance(result.changes, list)
    print("✅ test_all_strategies passed")


def test_simulator():
    """Test scenario simulator."""
    p = Portfolio.sample_fidelity_portfolio()
    simulator = ScenarioSimulator(p)

    for key in ["crash_2008", "bull_run", "tech_bubble", "black_swan"]:
        result = simulator.simulate(key)
        assert result.scenario_name is not None
        assert result.new_total_value > 0
        assert len(result.holdings_impact) == len(p.holdings)

    print("✅ test_simulator passed (4 scenarios)")


def test_monte_carlo():
    """Test Monte Carlo simulation."""
    p = Portfolio.sample_fidelity_portfolio()
    simulator = ScenarioSimulator(p)
    mc = simulator.simulate_random(100)

    assert mc["num_simulations"] == 100
    assert "mean_return" in mc
    assert "worst_case" in mc
    assert "best_case" in mc
    assert mc["worst_case"] <= mc["best_case"]

    print(f"✅ test_monte_carlo passed (mean: {mc['mean_return']}%, worst: {mc['worst_case']}%)")


def test_export_json():
    import tempfile
    p = Portfolio.sample_fidelity_portfolio()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = f.name
    p.export_json(path)

    import json
    data = json.loads(open(path).read())
    assert data["name"] == "Fidelity Growth Portfolio"
    assert len(data["holdings"]) == len(p.holdings)
    os.unlink(path)
    print("✅ test_export_json passed")


if __name__ == "__main__":
    tests = [
        test_portfolio_creation,
        test_holding_merge,
        test_weights,
        test_analyzer,
        test_risk_predictor,
        test_anomaly_detection,
        test_constraints,
        test_smart_rebalance_no_extreme_moves,
        test_mvo_optimization,
        test_all_strategies,
        test_simulator,
        test_monte_carlo,
        test_export_json,
    ]

    print(f"\n🧪 Running {len(tests)} tests...\n")
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("🎉 All tests passed!")
