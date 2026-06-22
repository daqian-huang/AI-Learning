"""Command line entry point for the V3.5 trading research system."""

from __future__ import annotations

import argparse

from .config import MacroInput, ScannerConfig
from .system import TradingResearchSystem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank low-priced US stock trade candidates.")
    parser.add_argument("--tickers", nargs="*", help="Optional tickers to analyze instead of scanner output.")
    parser.add_argument("--no-ibkr", action="store_true", help="Use fallback/yfinance universe instead of IBKR scanner.")
    parser.add_argument("--btc", type=float, help="BTC daily percent change.")
    parser.add_argument("--nasdaq", type=float, help="Nasdaq daily percent change.")
    parser.add_argument("--sp500", type=float, help="S&P 500 daily percent change.")
    parser.add_argument("--csv", help="Optional path to write ranked candidates as CSV.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    macro = None
    if args.btc is not None and args.nasdaq is not None and args.sp500 is not None:
        macro = MacroInput(args.btc, args.nasdaq, args.sp500)
    system = TradingResearchSystem(ScannerConfig())
    dataframe = system.run(macro=macro, tickers=args.tickers, use_ibkr_scanner=not args.no_ibkr)
    if args.csv:
        dataframe.to_csv(args.csv, index=False)
    print(dataframe.to_string(index=False))


if __name__ == "__main__":
    main()
