"""Daily research orchestration for IBKR-compatible stock candidates."""

from __future__ import annotations


from .config import MacroInput, ScannerConfig, ScoringWeights
from .data_sources import IBKRScanner, YFinanceMarketData, macro_from_yfinance
from .models import StockSnapshot
from .scoring import (
    ai_sector_score,
    final_score,
    liquidity_score,
    liquidation_score,
    macro_sentiment_score,
    oi_proxy_score,
    price_passes,
)


class TradingResearchSystem:
    """End-to-end V3.5 candidate generator for daily research."""

    def __init__(self, config: ScannerConfig | None = None, weights: ScoringWeights | None = None):
        self.config = config or ScannerConfig()
        self.weights = weights or ScoringWeights()
        self.ibkr_scanner = IBKRScanner(self.config)
        self.market_data = YFinanceMarketData(self.config)

    def run(
        self,
        macro: MacroInput | None = None,
        tickers: list[str] | None = None,
        use_ibkr_scanner: bool = True,
    ):
        """Return ranked candidates sorted by final score descending."""

        universe = tickers or self._stock_universe(use_ibkr_scanner=use_ibkr_scanner)
        macro_input = macro or MacroInput(*macro_from_yfinance())
        snapshots = self.market_data.snapshots(universe)
        return self.rank_snapshots(snapshots, macro_input)

    def rank_rows(self, snapshots: list[StockSnapshot], macro: MacroInput) -> list[dict[str, float | str]]:
        """Rank pre-built snapshots as plain rows; useful for tests and alternate data feeds."""

        macro_score = macro_sentiment_score(macro)
        rows: list[dict[str, float | str]] = []
        for snapshot in snapshots:
            if not price_passes(snapshot, self.config):
                continue
            liquidity = liquidity_score(snapshot, self.config)
            if liquidity <= 0:
                continue
            ai_score = ai_sector_score(snapshot, self.config.sector_keywords)
            oi_score = oi_proxy_score(snapshot)
            liq_score = liquidation_score(snapshot, oi_score)
            rows.append(
                {
                    "ticker": snapshot.ticker,
                    "price": round(snapshot.price, 2),
                    "AI score": round(ai_score, 3),
                    "liquidity score": round(liquidity, 3),
                    "macro score": round(macro_score, 3),
                    "OI score": round(oi_score, 3),
                    "liquidation score": round(liq_score, 3),
                    "final score": final_score(
                        ai_score, liquidity, macro_score, oi_score, liq_score, self.weights
                    ),
                }
            )
        return sorted(rows, key=lambda row: float(row["final score"]), reverse=True)

    def rank_snapshots(self, snapshots: list[StockSnapshot], macro: MacroInput):
        """Rank pre-built snapshots and return a pandas dataframe sorted by final score."""

        import pandas as pd

        return pd.DataFrame(self.rank_rows(snapshots, macro))

    def _stock_universe(self, use_ibkr_scanner: bool) -> list[str]:
        if not use_ibkr_scanner:
            return list(self.config.fallback_universe)
        return self.ibkr_scanner.scan()
