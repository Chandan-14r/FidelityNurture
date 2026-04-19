"""
Core Portfolio Management
Handles portfolio creation, holdings tracking, and performance calculation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import json
import csv
from pathlib import Path


@dataclass
class Holding:
    """Represents a single holding in the portfolio."""
    symbol: str
    name: str
    shares: float
    avg_cost: float
    current_price: float
    sector: str = "Unknown"
    asset_type: str = "stock"  # stock, etf, mutual_fund, bond, crypto
    purchase_date: Optional[str] = None

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    @property
    def weight(self) -> float:
        """Weight will be calculated by Portfolio."""
        return 0.0

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "shares": self.shares,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "sector": self.sector,
            "asset_type": self.asset_type,
            "market_value": round(self.market_value, 2),
            "cost_basis": round(self.cost_basis, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "unrealized_pnl_pct": round(self.unrealized_pnl_pct, 2),
        }


@dataclass
class Portfolio:
    """
    Investment portfolio with holdings, performance tracking, and analysis.
    
    Example:
        portfolio = Portfolio(name="My Investments")
        portfolio.add_holding(Holding(
            symbol="FXAIX", name="Fidelity 500 Index Fund",
            shares=50.0, avg_cost=175.00, current_price=192.50,
            sector="Large Cap", asset_type="mutual_fund"
        ))
    """
    name: str = "Portfolio"
    holdings: list[Holding] = field(default_factory=list)
    cash_balance: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_holding(self, holding: Holding) -> None:
        """Add a holding to the portfolio."""
        # Merge if same symbol exists
        for h in self.holdings:
            if h.symbol == holding.symbol:
                total_shares = h.shares + holding.shares
                h.avg_cost = ((h.avg_cost * h.shares) + (holding.avg_cost * holding.shares)) / total_shares
                h.shares = total_shares
                h.current_price = holding.current_price
                return
        self.holdings.append(holding)

    def remove_holding(self, symbol: str, shares: Optional[float] = None) -> bool:
        """Remove a holding entirely or reduce shares."""
        for i, h in enumerate(self.holdings):
            if h.symbol == symbol:
                if shares is None or shares >= h.shares:
                    self.holdings.pop(i)
                else:
                    h.shares -= shares
                return True
        return False

    @property
    def total_value(self) -> float:
        """Total portfolio market value including cash."""
        return sum(h.market_value for h in self.holdings) + self.cash_balance

    @property
    def total_cost(self) -> float:
        """Total cost basis of all holdings."""
        return sum(h.cost_basis for h in self.holdings)

    @property
    def total_pnl(self) -> float:
        """Total unrealized profit/loss."""
        return self.total_value - self.total_cost - self.cash_balance

    @property
    def total_pnl_pct(self) -> float:
        """Total P&L as percentage."""
        if self.total_cost == 0:
            return 0.0
        return (self.total_pnl / self.total_cost) * 100

    def get_weights(self) -> dict[str, float]:
        """Get allocation weights for each holding."""
        total = self.total_value
        if total == 0:
            return {}
        return {h.symbol: round((h.market_value / total) * 100, 2) for h in self.holdings}

    def get_sector_allocation(self) -> dict[str, float]:
        """Get allocation by sector."""
        total = self.total_value
        if total == 0:
            return {}
        sectors: dict[str, float] = {}
        for h in self.holdings:
            sectors[h.sector] = sectors.get(h.sector, 0) + h.market_value
        return {k: round((v / total) * 100, 2) for k, v in sectors.items()}

    def get_asset_type_allocation(self) -> dict[str, float]:
        """Get allocation by asset type."""
        total = self.total_value
        if total == 0:
            return {}
        types: dict[str, float] = {}
        for h in self.holdings:
            types[h.asset_type] = types.get(h.asset_type, 0) + h.market_value
        return {k: round((v / total) * 100, 2) for k, v in types.items()}

    def get_top_holdings(self, n: int = 5) -> list[Holding]:
        """Get top N holdings by market value."""
        return sorted(self.holdings, key=lambda h: h.market_value, reverse=True)[:n]

    def get_winners(self) -> list[Holding]:
        """Get holdings with positive P&L."""
        return sorted([h for h in self.holdings if h.unrealized_pnl > 0],
                      key=lambda h: h.unrealized_pnl_pct, reverse=True)

    def get_losers(self) -> list[Holding]:
        """Get holdings with negative P&L."""
        return sorted([h for h in self.holdings if h.unrealized_pnl < 0],
                      key=lambda h: h.unrealized_pnl_pct)

    def summary(self) -> dict:
        """Get portfolio summary."""
        return {
            "name": self.name,
            "total_value": round(self.total_value, 2),
            "total_cost": round(self.total_cost, 2),
            "cash_balance": round(self.cash_balance, 2),
            "total_pnl": round(self.total_pnl, 2),
            "total_pnl_pct": round(self.total_pnl_pct, 2),
            "num_holdings": len(self.holdings),
            "sectors": self.get_sector_allocation(),
            "asset_types": self.get_asset_type_allocation(),
        }

    def export_json(self, path: str) -> None:
        """Export portfolio to JSON."""
        data = {
            "name": self.name,
            "created_at": self.created_at,
            "cash_balance": self.cash_balance,
            "holdings": [h.to_dict() for h in self.holdings],
            "summary": self.summary(),
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def from_csv(cls, path: str, name: str = "Portfolio") -> "Portfolio":
        """Load portfolio from CSV file."""
        portfolio = cls(name=name)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                holding = Holding(
                    symbol=row["symbol"],
                    name=row.get("name", row["symbol"]),
                    shares=float(row["shares"]),
                    avg_cost=float(row["avg_cost"]),
                    current_price=float(row.get("current_price", row["avg_cost"])),
                    sector=row.get("sector", "Unknown"),
                    asset_type=row.get("asset_type", "stock"),
                )
                portfolio.add_holding(holding)
        return portfolio

    @classmethod
    def sample_fidelity_portfolio(cls) -> "Portfolio":
        """Create a sample portfolio with popular Fidelity funds."""
        portfolio = cls(name="Fidelity Growth Portfolio")
        holdings = [
            Holding("FXAIX", "Fidelity 500 Index Fund", 100, 170.00, 192.50, "Large Cap", "mutual_fund"),
            Holding("FTEC", "Fidelity MSCI Info Tech ETF", 45, 120.00, 145.30, "Technology", "etf"),
            Holding("FHLC", "Fidelity Health Care ETF", 30, 68.00, 72.80, "Healthcare", "etf"),
            Holding("FMAG", "Fidelity Magellan Fund", 25, 15.50, 17.20, "Large Cap Growth", "mutual_fund"),
            Holding("FBND", "Fidelity Total Bond ETF", 80, 45.00, 44.20, "Fixed Income", "bond"),
            Holding("FIDU", "Fidelity MSCI Industrials ETF", 20, 55.00, 62.10, "Industrials", "etf"),
            Holding("FCOM", "Fidelity Communication Services ETF", 15, 28.00, 31.50, "Communication", "etf"),
            Holding("AAPL", "Apple Inc.", 10, 150.00, 198.50, "Technology", "stock"),
            Holding("MSFT", "Microsoft Corp.", 8, 280.00, 415.20, "Technology", "stock"),
            Holding("NVDA", "NVIDIA Corp.", 5, 450.00, 875.30, "Technology", "stock"),
            Holding("JNJ", "Johnson & Johnson", 12, 160.00, 155.80, "Healthcare", "stock"),
            Holding("V", "Visa Inc.", 6, 230.00, 282.40, "Financials", "stock"),
        ]
        for h in holdings:
            portfolio.add_holding(h)
        portfolio.cash_balance = 5000.00
        return portfolio
