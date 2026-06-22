"""Configuration for the IBKR trading research system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScannerConfig:
    """Runtime settings for the IBKR scanner and market-data filters."""

    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 35
    exchanges: tuple[str, ...] = ("NYSE", "NASDAQ")
    max_results_per_scan: int = 50
    price_limit: float = 15.0
    min_volume: int = 500_000
    max_spread_pct: float = 0.02
    history_period: str = "3mo"
    history_interval: str = "1d"
    sector_keywords: tuple[str, ...] = (
        "AI",
        "artificial intelligence",
        "semiconductor",
        "chip",
        "memory",
        "storage",
        "data center",
        "cloud",
    )
    fallback_universe: tuple[str, ...] = (
        "SOUN",
        "BBAI",
        "AI",
        "WOLF",
        "ARRY",
        "OUST",
        "STEM",
        "IONQ",
    )


@dataclass(frozen=True)
class MacroInput:
    """Daily percentage changes for risk-sentiment inputs."""

    btc_daily_change: float
    nasdaq_daily_change: float
    sp500_daily_change: float


@dataclass(frozen=True)
class ScoringWeights:
    """Weights used by the final ranking formula."""

    ai: float = 2.0
    liquidity: float = 2.0
    macro: float = 1.5
    oi: float = 2.0
    liquidation: float = 1.5
