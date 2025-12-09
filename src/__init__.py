"""
Wheel of Fortune Gender Analysis Package
"""

from .scraper import WoFScraper, classify_gender_from_name
from .utils import DataNormalizer, ReliabilityAnalyzer, StatisticalAnalyzer

__all__ = [
    'WoFScraper',
    'classify_gender_from_name',
    'DataNormalizer',
    'ReliabilityAnalyzer',
    'StatisticalAnalyzer'
]
