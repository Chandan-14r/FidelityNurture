"""
NurtureFolio — AI-Powered Portfolio Intelligence Platform
Built for smart investors who want data-driven insights.

An intelligent investment analysis toolkit that uses machine learning
to assess portfolio health, detect anomalies, optimize allocation,
and predict risks — with a beautiful terminal dashboard.
"""

__version__ = "1.0.0"
__author__ = "Chandan"
__license__ = "MIT"

from fidelity_nurture.core.portfolio import Portfolio
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor
from fidelity_nurture.ai.optimizer import PortfolioOptimizer

__all__ = [
    "Portfolio",
    "PortfolioAnalyzer",
    "RiskPredictor",
    "PortfolioOptimizer",
]
