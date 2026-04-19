"""
NurtureFolio — AI-Powered Portfolio Intelligence Platform
Built for smart investors who want data-driven insights.
"""

__version__ = "2.0.0"
__author__ = "Chandan"
__license__ = "MIT"

from fidelity_nurture.core.portfolio import Portfolio
from fidelity_nurture.core.analyzer import PortfolioAnalyzer
from fidelity_nurture.ai.predictor import RiskPredictor
from fidelity_nurture.ai.optimizer import PortfolioOptimizer, Constraints
from fidelity_nurture.ai.simulator import ScenarioSimulator

__all__ = [
    "Portfolio",
    "PortfolioAnalyzer",
    "RiskPredictor",
    "PortfolioOptimizer",
    "Constraints",
    "ScenarioSimulator",
]
