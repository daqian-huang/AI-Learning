"""Scoring modules for the IBKR-compatible trading research system."""

from __future__ import annotations

import math
from collections.abc import Iterable

from .config import MacroInput, ScannerConfig, ScoringWeights
from .models import StockSnapshot


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 10.0) -> float:
    """Clamp a score to a fixed range."""

    if math.isnan(value) or math.isinf(value):
        return minimum
    return max(minimum, min(maximum, value))


def price_passes(snapshot: StockSnapshot, config: ScannerConfig) -> bool:
    """Return whether a stock is within the maximum research price."""

    return 0 < snapshot.price <= config.price_limit


def ai_sector_score(snapshot: StockSnapshot, keywords: Iterable[str]) -> float:
    """Score AI, semiconductor, storage, data-center, and cloud exposure."""

    haystack = " ".join(
        [snapshot.ticker, snapshot.name, snapshot.sector, snapshot.industry, snapshot.business_summary]
    ).lower()
    matches = {keyword.lower() for keyword in keywords if keyword.lower() in haystack}
    if not matches:
        return 0.0
    return clamp_score(2.0 + len(matches) * 1.5)


def liquidity_score(snapshot: StockSnapshot, config: ScannerConfig) -> float:
    """Score volume and spread quality; reject illiquid names before scoring."""

    if snapshot.volume < config.min_volume:
        return 0.0
    spread = snapshot.spread_pct
    if spread is not None and spread > config.max_spread_pct:
        return 0.0

    volume_component = clamp_score((snapshot.volume / config.min_volume) * 3.0, maximum=7.0)
    if spread is None:
        spread_component = 1.5
    else:
        spread_component = clamp_score((1 - spread / config.max_spread_pct) * 3.0, maximum=3.0)
    return clamp_score(volume_component + spread_component)


def macro_sentiment_score(macro: MacroInput) -> float:
    """Convert BTC, Nasdaq, and S&P 500 daily moves into a risk score."""

    weighted_change = (
        macro.btc_daily_change * 0.25
        + macro.nasdaq_daily_change * 0.45
        + macro.sp500_daily_change * 0.30
    )
    return clamp_score(5.0 + weighted_change * 1.5)


def oi_proxy_score(snapshot: StockSnapshot) -> float:
    """Proxy open-interest behavior using price and volume changes."""

    price_change = snapshot.price_change_pct
    volume_change = snapshot.volume_change_pct
    if price_change > 0 and volume_change > 0:
        return clamp_score(6.0 + min(price_change + volume_change / 2, 4.0))
    if price_change < 0 and volume_change > 0:
        return clamp_score(4.0 - min(abs(price_change), 3.0) + min(volume_change / 4, 2.0))
    if price_change > 0 and volume_change < 0:
        return 4.0
    return 3.0


def liquidation_score(snapshot: StockSnapshot, oi_score: float) -> float:
    """Estimate liquidation risk from volatility, volume spike, and falling OI proxy."""

    volatility_component = clamp_score(snapshot.volatility * 100 / 8.0, maximum=4.0)
    volume_spike_component = clamp_score(snapshot.volume_change_pct / 25.0, maximum=4.0)
    oi_drop_component = clamp_score((5.0 - oi_score) * 1.5, maximum=2.0)
    if volatility_component >= 2.0 and volume_spike_component >= 2.0 and oi_drop_component > 0:
        return clamp_score(volatility_component + volume_spike_component + oi_drop_component)
    return clamp_score((volatility_component + volume_spike_component + oi_drop_component) / 2)


def final_score(
    ai_score: float,
    liquidity: float,
    macro: float,
    oi: float,
    liquidation: float,
    weights: ScoringWeights,
) -> float:
    """Apply the V3.5 ranking formula."""

    return round(
        ai_score * weights.ai
        + liquidity * weights.liquidity
        + macro * weights.macro
        + oi * weights.oi
        + liquidation * weights.liquidation,
        3,
    )
