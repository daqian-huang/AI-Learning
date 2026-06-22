# IBKR-Compatible Trading Research System V3.5

This package ranks low-priced US stock candidates for daily research. It is designed for Interactive Brokers users and can fall back to `yfinance` when IBKR historical data is not available.


## Windows Quick Start

> **Research-only warning:** This tool is for screening and research only. It does not place trades, and nothing in its output is financial advice. Always do your own risk review before trading.

1. **Install Python dependencies** from PowerShell in the repository root:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

2. **Start IBKR TWS or IB Gateway** and keep it running while the scan executes:
   - For TWS paper trading, log into paper mode; the default API port is usually `7497`.
   - For TWS live trading, the default API port is usually `7496`.
   - For IB Gateway paper trading, the default API port is usually `4002`.
   - For IB Gateway live trading, the default API port is usually `4001`.

3. **Enable the required TWS API settings** in **File > Global Configuration > API > Settings**:
   - Enable **Enable ActiveX and Socket Clients**.
   - Confirm the socket port matches the port used by `ScannerConfig`.
   - Add `127.0.0.1` as a trusted IP if prompted.
   - Keep **Read-Only API** enabled if you want research-only access; this system does not submit orders.

4. **Run one scanner command** with daily macro inputs and CSV export:

   ```powershell
   python -m tools.ibkr_research.cli --btc 1.2 --nasdaq 0.5 --sp500 0.3 --csv candidates.csv
   ```

5. **Review a ranked output table** shaped like this sample:

   | ticker | price | AI score | liquidity score | macro score | OI score | liquidation score | final score |
   | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
   | SOUN | 7.82 | 8.00 | 9.35 | 6.50 | 8.40 | 2.10 | 61.35 |
   | BBAI | 4.16 | 6.50 | 8.70 | 6.50 | 7.20 | 3.30 | 55.95 |
   | WOLF | 2.94 | 5.00 | 7.80 | 6.50 | 6.10 | 1.80 | 47.85 |

## What it does

- Scans NYSE and NASDAQ stocks through `ib_insync` scanner subscriptions.
- Keeps stocks priced at or below 15 USD.
- Scores AI, semiconductor, memory, storage, data-center, and cloud exposure from company metadata.
- Rejects candidates with volume below 500,000 shares or with spreads wider than the configured threshold.
- Converts BTC, Nasdaq, and S&P 500 daily changes into a macro risk-on/risk-off score.
- Uses price and volume behavior as an open-interest proxy because IBKR does not provide stock OI directly.
- Raises a liquidation proxy score when volatility, volume spikes, and a falling OI proxy align.
- Returns a sorted dataframe with ticker, price, component scores, and final score.

## Formula

```text
Final Score =
AI Score * 2 +
Liquidity Score * 2 +
Macro Score * 1.5 +
OI Score * 2 +
Liquidation Score * 1.5
```

## Daily usage

Install optional runtime dependencies:

```bash
pip install pandas yfinance ib_insync
```

Run with IBKR scanner data:

```bash
python -m tools.ibkr_research.cli --btc 1.2 --nasdaq 0.5 --sp500 0.3 --csv candidates.csv
```

Run without IBKR, using a small fallback universe and yfinance market data:

```bash
python -m tools.ibkr_research.cli --no-ibkr --btc 1.2 --nasdaq 0.5 --sp500 0.3
```

Analyze explicit tickers:

```bash
python -m tools.ibkr_research.cli --tickers SOUN BBAI AI WOLF --btc 1.2 --nasdaq 0.5 --sp500 0.3
```

## Windows step-by-step setup

These steps assume you are running the project from PowerShell on Windows 10 or Windows 11.

### 1. Install Python

1. Install Python 3.11 or newer from the Microsoft Store or from <https://www.python.org/downloads/windows/>.
2. During installation, enable **Add python.exe to PATH**.
3. Confirm Python is available:

```powershell
python --version
```

### 2. Open PowerShell in the repository

Move into the repository root, replacing the path with the location where you cloned or downloaded this project:

```powershell
cd C:\Users\YOUR_NAME\AI-Learning
```

### 3. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, run this once for the current user and then activate again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The main runtime packages are:

- `ib_insync` for Interactive Brokers scanner connectivity.
- `yfinance` for historical market data fallback and metadata enrichment.
- `pandas` for the final sorted dataframe and CSV export.

### 5. Connect IBKR TWS or IB Gateway

You can use either Trader Workstation (TWS) or IB Gateway. Keep the application open while running the scan.

#### TWS paper trading defaults

1. Open **Trader Workstation** and log into paper trading.
2. Go to **File > Global Configuration > API > Settings**.
3. Enable **Enable ActiveX and Socket Clients**.
4. Confirm **Socket port** is `7497` for paper trading.
5. Add `127.0.0.1` to trusted IPs if TWS asks for trusted API clients.
6. Keep **Read-Only API** enabled if you only want research access. This system does not place orders.

#### TWS live trading defaults

- Live TWS commonly uses port `7496`.
- If you use live TWS, update `ScannerConfig(port=7496)` in code or add a small wrapper script that passes a custom config.

#### IB Gateway defaults

1. Open **IB Gateway** and log in.
2. Open the gateway settings and enable API socket clients.
3. Paper IB Gateway commonly uses port `4002`; live IB Gateway commonly uses port `4001`.
4. If you use one of these ports, update `ScannerConfig(port=4002)` for paper or `ScannerConfig(port=4001)` for live.

### 6. Run a daily IBKR scan

From the repository root with the virtual environment activated:

```powershell
python -m tools.ibkr_research.cli --btc 1.2 --nasdaq 0.5 --sp500 0.3 --csv candidates.csv
```

This command:

1. Connects to IBKR on the configured host and port.
2. Scans NYSE and NASDAQ stocks.
3. Keeps candidates priced at or below 15 USD.
4. Enriches candidates with yfinance metadata and daily history.
5. Applies liquidity, AI/sector, macro, OI proxy, and liquidation proxy scoring.
6. Prints the ranked dataframe and saves it to `candidates.csv`.

### 7. Run without IBKR for testing

Use this mode when TWS or IB Gateway is closed, or when you only want to test the pipeline with the fallback watchlist:

```powershell
python -m tools.ibkr_research.cli --no-ibkr --btc 1.2 --nasdaq 0.5 --sp500 0.3
```

### 8. Run with explicit tickers

Use this mode when you want to research a fixed list instead of scanner output:

```powershell
python -m tools.ibkr_research.cli --tickers SOUN BBAI AI WOLF --btc 1.2 --nasdaq 0.5 --sp500 0.3 --csv candidates.csv
```

### Sample output table

Actual values will change daily because prices, volume, spreads, and market sentiment change. The table shape is:

| ticker | price | AI score | liquidity score | macro score | OI score | liquidation score | final score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SOUN | 7.82 | 8.00 | 9.35 | 6.50 | 8.40 | 2.10 | 61.35 |
| BBAI | 4.16 | 6.50 | 8.70 | 6.50 | 7.20 | 3.30 | 55.95 |
| WOLF | 2.94 | 5.00 | 7.80 | 6.50 | 6.10 | 1.80 | 47.85 |

### Daily operating checklist

1. Start TWS or IB Gateway and verify the correct API port.
2. Activate the Python virtual environment.
3. Enter current BTC, Nasdaq, and S&P 500 daily percentage changes.
4. Run the scan and save a CSV.
5. Review only the ranked candidates; this tool is for research and does not submit orders.

## Extension points

- Replace `YFinanceMarketData.snapshots()` with an IBKR historical-data implementation.
- Tune `ScannerConfig` for stricter spread, volume, scanner, or keyword requirements.
- Add persistence for daily snapshots and score history.
- Add risk controls before using any candidate as an actual trade idea.

This tool is for research only and does not place orders.
