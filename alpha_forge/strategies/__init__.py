from .base import Strategy  # noqa: F401
from .momentum import CrossSectionalMomentum  # noqa: F401
from .trend import TrendFollowing  # noqa: F401
from .mean_reversion import RSIMeanReversion  # noqa: F401
from .buy_and_hold import BuyAndHold  # noqa: F401
from .hrp import TrendHRP  # noqa: F401  (needs skfolio at run time)

REGISTRY = {
    "momentum": CrossSectionalMomentum,
    "trend": TrendFollowing,
    "meanrev": RSIMeanReversion,
    "buyhold": BuyAndHold,
    "trend_hrp": TrendHRP,
}
