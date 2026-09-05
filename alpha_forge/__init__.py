"""Alpha Forge - research, backtesting and paper-trading engine for India (NSE) + US markets.

Design rule #1: nothing in this package places a real-money order unless
ALPHA_FORGE_LIVE=1 is set in the environment AND the broker is constructed
with live=True. Everything defaults to paper / dry-run.
"""
__version__ = "0.1.0"
