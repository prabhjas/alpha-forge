from .base import Broker, Order, Position, Fill  # noqa: F401
from .paper import PaperBroker  # noqa: F401


def get_broker(name: str, **kwargs):
    if name == "paper":
        return PaperBroker(**kwargs)
    if name == "alpaca":
        from .alpaca_broker import AlpacaBroker
        return AlpacaBroker(**kwargs)
    if name == "kite":
        from .kite_broker import KiteBroker
        return KiteBroker(**kwargs)
    if name == "angelone":
        from .angelone_broker import AngelOneBroker
        return AngelOneBroker(**kwargs)
    raise ValueError(f"unknown broker {name}")
