"""IBKR and yfinance data-source adapters."""

from __future__ import annotations

import importlib.util
from collections.abc import Iterable


from .config import ScannerConfig
from .models import StockSnapshot


def _require_package(package: str, install_hint: str) -> None:
    if importlib.util.find_spec(package) is None:
        raise RuntimeError(f"Missing optional dependency '{package}'. Install with: {install_hint}")


class IBKRScanner:
    """US stock scanner backed by ib_insync market scanners and snapshots."""

    def __init__(self, config: ScannerConfig):
        self.config = config

    def scan(self) -> list[str]:
        """Return US stock symbols from NYSE and NASDAQ scanner subscriptions."""

        _require_package("ib_insync", "pip install ib_insync")
        from ib_insync import IB, ScannerSubscription

        ib = IB()
        ib.connect(self.config.host, self.config.port, clientId=self.config.client_id)
        tickers: set[str] = set()
        try:
            for exchange in self.config.exchanges:
                subscription = ScannerSubscription(
                    instrument="STK",
                    locationCode=f"STK.{exchange}",
                    scanCode="MOST_ACTIVE",
                    abovePrice=0,
                    belowPrice=self.config.price_limit,
                )
                rows = ib.reqScannerData(subscription, [], [])[: self.config.max_results_per_scan]
                tickers.update(row.contractDetails.contract.symbol for row in rows)
        finally:
            ib.disconnect()
        return sorted(tickers)


class YFinanceMarketData:
    """Market-data fallback and enrichment using yfinance."""

    def __init__(self, config: ScannerConfig):
        self.config = config

    def snapshots(self, tickers: Iterable[str]) -> list[StockSnapshot]:
        """Build stock snapshots with price, volume, metadata, and history-derived features."""

        _require_package("yfinance", "pip install yfinance")
        import yfinance as yf

        snapshots: list[StockSnapshot] = []
        for ticker in sorted(set(tickers)):
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.get_info()
            history = yf_ticker.history(
                period=self.config.history_period,
                interval=self.config.history_interval,
                auto_adjust=False,
            )
            if history.empty:
                continue
            latest = history.iloc[-1]
            previous = history.iloc[-2] if len(history) > 1 else latest
            avg_volume = float(history["Volume"].tail(20).mean()) if "Volume" in history else 0.0
            latest_close = float(latest["Close"])
            previous_close = float(previous["Close"])
            volume = int(latest.get("Volume", 0))
            volume_change_pct = ((volume - avg_volume) / avg_volume * 100) if avg_volume else 0.0
            price_change_pct = (
                ((latest_close - previous_close) / previous_close * 100) if previous_close else 0.0
            )
            volatility = float(history["Close"].pct_change().tail(20).std() or 0.0)
            snapshots.append(
                StockSnapshot(
                    ticker=ticker,
                    price=float(info.get("regularMarketPrice") or latest_close),
                    volume=volume,
                    bid=_safe_float(info.get("bid")),
                    ask=_safe_float(info.get("ask")),
                    name=str(info.get("longName") or info.get("shortName") or ""),
                    sector=str(info.get("sector") or ""),
                    industry=str(info.get("industry") or ""),
                    business_summary=str(info.get("longBusinessSummary") or ""),
                    avg_volume=avg_volume,
                    previous_close=previous_close,
                    latest_close=latest_close,
                    volume_change_pct=volume_change_pct,
                    price_change_pct=price_change_pct,
                    volatility=volatility,
                )
            )
        return snapshots


def _safe_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    number = float(value)
    return number if number > 0 else None


def macro_from_yfinance() -> tuple[float, float, float]:
    """Fetch BTC, Nasdaq, and S&P 500 daily percentage changes from yfinance."""

    _require_package("yfinance", "pip install yfinance")
    import yfinance as yf

    symbols = ["BTC-USD", "^IXIC", "^GSPC"]
    changes: list[float] = []
    for symbol in symbols:
        history = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
        if len(history) < 2:
            changes.append(0.0)
            continue
        previous = float(history.iloc[-2]["Close"])
        latest = float(history.iloc[-1]["Close"])
        changes.append(((latest - previous) / previous * 100) if previous else 0.0)
    return tuple(changes)  # type: ignore[return-value]
