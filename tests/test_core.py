"""
Tests for NurtureFolio core modules.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fidelity_nurture.core.portfolio import Portfolio, Holding
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor
from fidelity_nurture.ai.optimizer import PortfolioOptimizer


def test_portfolio_creation():
    """Test portfolio creation and basic operations."""
    p = Portfolio(name="Test")
    h = Holding("AAPL", "Apple", 10, 150.0, 200.0, "Technology", "stock")
    p.add_holding(h)

    assert p.total_value == 2000.0
    assert p.total_cost == 1500.0
    assert p.total_pnl == 500.0
    assert len(p.holdings) == 1
    print("✅ test_portfolio_creation passed")


def test_holding_merge():
    """Test adding same symbol merges holdings."""
    p = Portfolio()
    p.add_holding(Holding("AAPL", "Apple", 10, 150.0, 200.0))
    p.add_holding(Holding("AAPL", "Apple", 5, 180.0, 200.0))

    assert len(p.holdings) == 1
    assert p.holdings[0].shares == 15
    # Avg cost: (150*10 + 180*5) / 15 = (1500+900)/15 = 160
    assert p.holdings[0].avg_cost == 160.0
    print("✅ test_holding_merge passed")


def test_weights():
    """Test portfolio weight calculation."""
    p = Portfolio()
    p.add_holding(Holding("AAPL", "Apple", 10, 100.0, 200.0))  # 2000
    p.add_holding(Holding("MSFT", "Microsoft", 5, 300.0, 400.0))  # 2000

    weights = p.get_weights()
    assert weights["AAPL"] == 50.0
    assert weights["MSFT"] == 50.0
    print("✅ test_weights passed")


def test_sector_allocation():
    """Test sector allocation."""
    p = Portfolio()
    p.add_holding(Holding("AAPL", "Apple", 10, 100.0, 200.0, "Tech"))
    p.add_holding(Holding("JNJ", "J&J", 10, 100.0, 200.0, "Health"))

    alloc = p.get_sector_allocation()
    assert alloc["Tech"] == 50.0
    assert alloc["Health"] == 50.0
    print("✅ test_sector_allocation passed")


def test_analyzer():
    """Test portfolio analyzer."""
    p = Portfolio.sample_fidelity_portfolio()
    analyzer = PortfolioAnalyzer(p)
    score = analyzer.analyze()

    assert 0 <= score.overall <= 100
    assert score.grade in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F")
    assert isinstance(score.warnings, list)
    assert isinstance(score.recommendations, list)
    print(f"✅ test_analyzer passed (score: {score.overall}, grade: {score.grade})")


def test_risk_predictor():
    """Test risk prediction."""
    p = Portfolio.sample_fidelity_portfolio()
    predictor = RiskPredictor(p)
    risk = predictor.assess_risk()

    assert risk.risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert 0 <= risk.risk_score <= 100
    assert risk.volatility_estimate > 0
    assert isinstance(risk.risk_factors, list)
    print(f"✅ test_risk_predictor passed (risk: {risk.risk_level}, score: {risk.risk_score})")


def test_anomaly_detection():
    """Test anomaly detection."""
    p = Portfolio.sample_fidelity_portfolio()
    predictor = RiskPredictor(p)
    anomalies = predictor.detect_anomalies()

    assert isinstance(anomalies, list)
    for a in anomalies:
        assert a.severity in ("INFO", "WARNING", "CRITICAL")
        assert a.category in ("allocation", "performance", "volatility", "correlation")
    print(f"✅ test_anomaly_detection passed ({len(anomalies)} anomalies found)")


def test_optimizer():
    """Test portfolio optimizer."""
    p = Portfolio.sample_fidelity_portfolio()
    optimizer = PortfolioOptimizer(p)

    for strategy in ["maximize_sharpe", "equal_weight", "defensive", "momentum"]:
        result = optimizer.optimize(strategy=strategy)
        assert result.strategy is not None
        assert isinstance(result.changes, list)
    print("✅ test_optimizer passed (all 4 strategies)")


def test_export_json():
    """Test JSON export."""
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
        test_sector_allocation,
        test_analyzer,
        test_risk_predictor,
        test_anomaly_detection,
        test_optimizer,
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
