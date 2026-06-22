"""Shared data models for research candidates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockSnapshot:
    """Latest market snapshot used by the scoring engine."""

    ticker: str
    price: float
    volume: int
    bid: float | None = None
    ask: float | None = None
    name: str = ""
    sector: str = ""
    industry: str = ""
    business_summary: str = ""
    avg_volume: float | None = None
    previous_close: float | None = None
    latest_close: float | None = None
    volume_change_pct: float = 0.0
    price_change_pct: float = 0.0
    volatility: float = 0.0

    @property
    def spread_pct(self) -> float | None:
        """Return bid/ask spread as a fraction of mid price, if available."""

        if self.bid is None or self.ask is None or self.bid <= 0 or self.ask <= 0:
            return None
        mid = (self.bid + self.ask) / 2
        if mid <= 0:
            return None
        return (self.ask - self.bid) / mid
