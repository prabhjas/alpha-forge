from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd


class Strategy(ABC):
    """A strategy maps price history -> target portfolio weights.

    Rules:
      * Only use information available at or before each row's timestamp.
      * Weights are fractions of total equity. Sum of |weights| <= 1 (no leverage in v1).
      * Positive = long. Shorts are allowed in the engine but every v1 strategy is long-only
        because shorting single stocks in India requires F&O and that's Phase 3+.
    """

    name: str = "strategy"

    def __init__(self, **params: Any):
        self.params: Dict[str, Any] = {**self.default_params(), **params}

    @classmethod
    def default_params(cls) -> Dict[str, Any]:
        return {}

    @abstractmethod
    def generate_weights(self, prices: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        ...

    def describe(self) -> str:
        return f"{self.name}({', '.join(f'{k}={v}' for k, v in self.params.items())})"
