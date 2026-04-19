# 💰 NurtureFolio

**AI-Powered Portfolio Intelligence Platform** — Analyze, optimize, and monitor your investments with machine learning.

Built for investors who want **data-driven insights** without the complexity of Bloomberg terminals.

---

## ✨ Features

### 📊 Portfolio Analysis
- **Health Scoring** — A+ to F grade based on diversification, risk, performance & concentration
- **Sector Breakdown** — Visual allocation across sectors, asset types, and holdings
- **Concentration Detection** — Herfindahl-Hirschman Index for portfolio concentration

### 🤖 AI Risk Engine
- **Volatility Estimation** — Annualized portfolio volatility using asset-weighted models
- **Max Drawdown Prediction** — Estimate worst-case scenarios
- **Beta & Sharpe Calculation** — Risk-adjusted return metrics
- **Anomaly Detection** — Auto-detect overweight sectors, single-stock risk, performance outliers

### 🎯 Portfolio Optimization
- **Max Sharpe** — Optimize for best risk-adjusted returns
- **Equal Weight** — Simple equal-weight rebalancing
- **Defensive** — Minimize drawdown risk with bond allocation
- **Momentum** — Tilt toward recent winners

### 🖥️ Terminal Dashboard
- Beautiful colored terminal output with bar charts
- Holdings table with P&L and weights
- Health score gauges
- Actionable recommendations

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/Chandan-14r/FidelityNurture.git
cd FidelityNurture

# Run the demo (no dependencies needed!)
python -m fidelity_nurture
```

### Other Commands

```bash
python -m fidelity_nurture analyze    # Health score & recommendations
python -m fidelity_nurture risk       # Risk assessment & anomalies
python -m fidelity_nurture optimize   # All optimization strategies
python -m fidelity_nurture json       # Export analysis as JSON
```

---

## 📸 Sample Output

```
══════════════════════════════════════════════════════════════════════
  💰 NurtureFolio — AI Portfolio Intelligence
  Portfolio: Fidelity Growth Portfolio
══════════════════════════════════════════════════════════════════════

📊 PORTFOLIO OVERVIEW
  ┌─────────────────────────────────────────┐
  │  Total Value:         $32,847.60        │
  │  Cost Basis:          $25,530.00        │
  │  Unrealized P&L:      +$7,317.60        │
  │  Return:               +28.66%          │
  │  Holdings:                    12        │
  │  Cash:                $5,000.00         │
  └─────────────────────────────────────────┘

🏥 PORTFOLIO HEALTH
  Overall:        B+ (72/100)
  Diversification:████████░░ 78
  Risk Mgmt:      ███████░░░ 68
  Performance:    █████████░ 95
  Concentration:  ███████░░░ 65

⚠️  RISK ASSESSMENT
  Risk Level:     MODERATE (48/100)
  Volatility:     14.2% annualized
  Sharpe Ratio:   1.67
  Portfolio Beta:  1.08

🔍 ANOMALIES
  ⚠️ [WARNING] Technology sector is 42.1% — overweight
    → Reduce tech exposure below 30%
```

---

## 🏗️ Architecture

```
fidelity_nurture/
├── core/
│   ├── portfolio.py      # Portfolio & Holding data models
│   └── analyzer.py       # Health scoring & diversification analysis
├── ai/
│   ├── predictor.py      # Risk prediction & anomaly detection
│   └── optimizer.py      # Portfolio optimization strategies
├── data/
│   └── market.py         # Market data provider (extensible)
├── ui/
│   └── dashboard.py      # Terminal visualization
├── __init__.py
├── __main__.py           # CLI entry point
tests/
└── test_core.py          # Test suite
```

---

## 🧪 Running Tests

```bash
python tests/test_core.py
```

---

## 🔧 Extending

### Add Your Own Portfolio

```python
from fidelity_nurture.core.portfolio import Portfolio, Holding

portfolio = Portfolio(name="My Portfolio")
portfolio.add_holding(Holding(
    symbol="VOO",
    name="Vanguard S&P 500 ETF",
    shares=25.0,
    avg_cost=420.00,
    current_price=475.30,
    sector="Large Cap",
    asset_type="etf",
))

from fidelity_nurture.ui.dashboard import Dashboard
print(Dashboard(portfolio).render())
```

### Load from CSV

```python
portfolio = Portfolio.from_csv("my_holdings.csv", name="My Portfolio")
```

CSV format:
```csv
symbol,name,shares,avg_cost,current_price,sector,asset_type
AAPL,Apple Inc.,10,150.00,198.50,Technology,stock
FBND,Fidelity Total Bond ETF,80,45.00,44.20,Fixed Income,bond
```

### Integrate Real Market Data

Extend `MarketDataProvider` to use:
- **yfinance** — `pip install yfinance`
- **Alpha Vantage** — Free API key
- **IEX Cloud** — Real-time quotes

---

## 📋 Roadmap

- [x] Portfolio management & health scoring
- [x] AI risk prediction & anomaly detection
- [x] Multiple optimization strategies
- [x] Terminal dashboard with visualizations
- [ ] Real market data integration (yfinance)
- [ ] Historical backtesting engine
- [ ] Web dashboard (Streamlit/Gradio)
- [ ] Tax-loss harvesting suggestions
- [ ] Dividend tracking & yield analysis
- [ ] Monte Carlo simulation for retirement planning
- [ ] Telegram/Discord alerts for portfolio changes

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Chandan** — AI Engineer & Full-Stack Developer
- GitHub: [@Chandan-14r](https://github.com/Chandan-14r)
- LinkedIn: [Chandan R.S](https://linkedin.com/in/chandan-rs)

---

*Built with 🍬 by Sweety — because your portfolio deserves intelligence.*
