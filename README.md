# 💰 NurtureFolio

**AI-Powered Portfolio Intelligence Platform** — Analyze, optimize, and stress-test your investments with constraint-based machine learning.

Built for investors who want **data-driven insights** without the complexity of Bloomberg terminals.

---

## ✨ What Makes This Different

### 🧠 Constraint-Based Rebalancing (Not Stupid Optimization)
Other tools say: "SELL 37% → 2.9%" ❌  
NurtureFolio says: "Gradually trim 37% → 26.6%" ✅

Real portfolio managers use **constraints**:
- Max single asset: 20%
- Max reduction per rebalance: 30%
- Core funds preserved (never eliminated)
- Only act if weight differs by >5%

### 📊 Mean-Variance Optimization (Modern Portfolio Theory)
```
max_w (w^T * μ - λ * w^T * Σ * w)
```
Where λ = risk aversion, with added penalties for concentration and sector imbalance.

### 🎭 Scenario Simulation
Stress-test your portfolio against:
- 2008 Financial Crisis
- COVID-19 Crash
- Tech Bubble Burst
- Interest Rate Hikes
- Black Swan Events
- **Monte Carlo** (1000 random simulations)

---

## 🚀 Quick Start

```bash
git clone https://github.com/Chandan-14r/FidelityNurture.git
cd FidelityNurture
python3 -m fidelity_nurture
```

### Commands

```bash
# Full terminal dashboard
python3 -m fidelity_nurture

# Health analysis
python3 -m fidelity_nurture analyze

# Risk assessment + anomalies
python3 -m fidelity_nurture risk

# Smart rebalance (constraint-based, recommended)
python3 -m fidelity_nurture optimize

# Mean-Variance Optimization
python3 -m fidelity_nurture optimize --strategy maximize_sharpe

# Different risk tolerances
python3 -m fidelity_nurture optimize --risk conservative
python3 -m fidelity_nurture optimize --risk aggressive

# Scenario simulations
python3 -m fidelity_nurture simulate                           # List all scenarios
python3 -m fidelity_nurture simulate --scenario crash_2008     # 2008 crash
python3 -m fidelity_nurture simulate --monte-carlo             # 1000 random sims

# Export as JSON
python3 -m fidelity_nurture json
```

---

## 📸 Sample Output

### Smart Rebalance (No Extreme Moves)
```
🎯 Smart Rebalance (moderate)
========================================
  Expected Return: 8.5%
  Expected Risk: 6.5%
  Sharpe Ratio: 0.535

  Suggested Changes:
    🔴 SELL FXAIX  37.1% → 26.6% ($5,465)
       └─ Overweight at 37.1% — trimming to 26.6% (max: 20%)
```

### Monte Carlo Simulation
```
🎲 Running Monte Carlo (1000 iterations)...
  Mean Return: 6.15%
  Worst Case: -28.82%
  Best Case: +44.22%
  Probability of Gain: 71.0%
  Probability of 20%+ Loss: 1.0%
```

### 2008 Crisis Scenario
```
🎭 2008 Financial Crisis
  Portfolio Impact: -$17,828 (-34.4%)
  Worst: V (-46.9%)
  Best:  FBND (+8.0%)  ← Bonds protect you
```

---

## 🏗️ Architecture

```
fidelity_nurture/
├── core/
│   ├── portfolio.py      # Portfolio & Holding models
│   └── analyzer.py       # Health scoring & diversification
├── ai/
│   ├── predictor.py      # Risk prediction & anomaly detection
│   ├── optimizer.py      # Constraint-based optimization (5 strategies)
│   └── simulator.py      # Scenario & Monte Carlo simulation
├── data/
│   └── market.py         # Market data (simulated + yfinance ready)
├── ui/
│   └── dashboard.py      # Terminal visualization
├── __main__.py           # CLI with argparse
tests/
└── test_core.py          # 13 tests
```

---

## 🧪 Tests

```bash
python3 tests/test_core.py
# 🧪 Running 13 tests...
# 🎉 All tests passed!
```

---

## 🔧 Use Your Own Portfolio

### Python API
```python
from fidelity_nurture import Portfolio, Holding, PortfolioOptimizer, Constraints

portfolio = Portfolio(name="My Portfolio")
portfolio.add_holding(Holding(
    symbol="VOO", name="Vanguard S&P 500 ETF",
    shares=25.0, avg_cost=420.00, current_price=475.30,
    sector="Large Cap", asset_type="etf",
))

# With constraints
constraints = Constraints(
    max_single_asset=0.20,
    max_single_asset_sell_pct=0.30,
    min_bonds=0.15,
)

optimizer = PortfolioOptimizer(portfolio, constraints)
result = optimizer.optimize(strategy="smart_rebalance")
```

### From CSV
```bash
python3 -m fidelity_nurture --portfolio my_holdings.csv --name "My Portfolio"
```

CSV format:
```csv
symbol,name,shares,avg_cost,current_price,sector,asset_type
AAPL,Apple Inc.,10,150.00,198.50,Technology,stock
FBND,Fidelity Total Bond ETF,80,45.00,44.20,Fixed Income,bond
```

---

## 📋 Roadmap

- [x] Portfolio management & health scoring
- [x] Constraint-based rebalancing (realistic)
- [x] Mean-Variance Optimization
- [x] Risk penalties & multi-objective scoring
- [x] Scenario simulation (8 predefined + custom)
- [x] Monte Carlo simulation (1000 iterations)
- [x] Terminal dashboard
- [ ] Real market data (yfinance integration)
- [ ] Historical backtesting engine
- [ ] Efficient frontier visualization
- [ ] Tax-loss harvesting
- [ ] Dividend tracking
- [ ] Web dashboard (Streamlit)
- [ ] Telegram/Discord alerts

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 👨‍💻 Author

**Chandan** — AI Engineer & Full-Stack Developer
- GitHub: [@Chandan-14r](https://github.com/Chandan-14r)

---

*Built with 🍬 by Sweety — because your portfolio deserves intelligence.*
