from tools.ibkr_research.config import MacroInput, ScannerConfig
from tools.ibkr_research.models import StockSnapshot
from tools.ibkr_research.scoring import ai_sector_score, liquidity_score, macro_sentiment_score
from tools.ibkr_research.system import TradingResearchSystem


def test_scores_ai_liquid_stock():
    config = ScannerConfig()
    snapshot = StockSnapshot(
        ticker="TEST",
        price=10.0,
        volume=1_000_000,
        bid=9.99,
        ask=10.01,
        name="Test AI Semiconductor",
        sector="Technology",
        industry="Semiconductor chips",
        business_summary="Builds artificial intelligence data center storage products.",
    )

    assert ai_sector_score(snapshot, config.sector_keywords) > 5
    assert liquidity_score(snapshot, config) > 5


def test_macro_positive_is_risk_on():
    assert macro_sentiment_score(MacroInput(1.0, 1.0, 1.0)) > macro_sentiment_score(
        MacroInput(-1.0, -1.0, -1.0)
    )


def test_system_filters_and_sorts_candidates():
    system = TradingResearchSystem(ScannerConfig())
    snapshots = [
        StockSnapshot(
            ticker="GOOD",
            price=8.0,
            volume=2_000_000,
            bid=7.99,
            ask=8.01,
            name="Good AI Cloud",
            business_summary="Artificial intelligence cloud semiconductor storage company.",
            price_change_pct=4.0,
            volume_change_pct=60.0,
            volatility=0.04,
        ),
        StockSnapshot(ticker="EXPENSIVE", price=16.0, volume=3_000_000),
        StockSnapshot(ticker="ILLIQUID", price=5.0, volume=10_000),
    ]

    ranked = system.rank_rows(snapshots, MacroInput(0.5, 0.5, 0.5))

    assert [row["ticker"] for row in ranked] == ["GOOD"]
    assert ranked[0]["final score"] > 0
