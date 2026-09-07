from .base import Strategy  # noqa: F401
from .momentum import CrossSectionalMomentum  # noqa: F401
from .trend import TrendFollowing  # noqa: F401
from .mean_reversion import RSIMeanReversion  # noqa: F401
from .buy_and_hold import BuyAndHold  # noqa: F401
from .sector_tilt import SectorTilt  # noqa: F401
from .fvg import FVGStrategy  # noqa: F401
from .ensemble import Ensemble, SectorEnsemble  # noqa: F401
from .pairs import PairsTrading  # noqa: F401
from .hrp import TrendHRP  # noqa: F401  (needs skfolio at run time)

REGISTRY = {
    "momentum": CrossSectionalMomentum,
    "trend": TrendFollowing,
    "meanrev": RSIMeanReversion,
    "buyhold": BuyAndHold,
    "trend_hrp": TrendHRP,
    "pairs": PairsTrading,
    "ensemble": Ensemble,
    "sector_ensemble": SectorEnsemble,
    "fvg": FVGStrategy,
    "sector_tilt": SectorTilt,
}
