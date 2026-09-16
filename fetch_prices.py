"""
STEP 2 — Build a quarterly average share price for each airline.

Source: Yahoo Finance via the yfinance package.
Method: average EVERY trading day's closing price within each quarter.
        (Better than averaging three month-end closes, which only samples
        three days out of roughly sixty.)

Output: quarterly_prices.csv  — one row per company-quarter
        current_prices.csv    — today's price for each ticker

In Google Colab, run this first in its own cell:
    !pip install yfinance -q
"""

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------- settings

# SPY is the S&P 500 benchmark, pulled the same way so the comparison
# uses dividend-adjusted prices on both sides.
TICKERS = ["DAL", "UAL", "AAL", "LUV", "ALK", "JBLU", "SPY"]
START = "2015-01-01"

# Prices are already adjusted for dividends and splits (auto_adjust=True),
# so the "Close" column below IS the adjusted close.
AUTO_ADJUST = True

# ---------------------------------------------------------------- download


def download_closes():
    """Get daily adjusted closing prices for all six tickers."""
    raw = yf.download(
        TICKERS,
        start=START,
        interval="1d",
        auto_adjust=AUTO_ADJUST,
        progress=False,
    )

    closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    closes = closes.dropna(how="all")

    print(f"Downloaded {len(closes):,} trading days")
    print(f"Range: {closes.index[0].date()} to {closes.index[-1].date()}\n")
    return closes


# ---------------------------------------------------------------- reshape


def to_quarterly(closes):
    """Average the daily closes within each calendar quarter."""
    long = closes.stack().reset_index()
    long.columns = ["date", "ticker", "close"]

    long["fiscal_year"] = long["date"].dt.year
    long["quarter"] = "Q" + long["date"].dt.quarter.astype(str)

    grouped = (
        long.groupby(["ticker", "fiscal_year", "quarter"])
            .agg(avg_price=("close", "mean"),
                 trading_days=("close", "size"))
            .reset_index()
    )

    # Last calendar day of the quarter, so this lines up with the buyback file.
    quarter_number = grouped["quarter"].str[1].astype(int)
    grouped["period_end"] = (
        pd.to_datetime(dict(year=grouped["fiscal_year"],
                            month=quarter_number * 3,
                            day=1))
        + pd.offsets.MonthEnd(0)
    ).dt.date

    grouped["avg_price"] = grouped["avg_price"].round(2)

    # A quarter with far fewer than ~60 trading days is still in progress.
    grouped["complete_quarter"] = grouped["trading_days"] >= 55

    # Join key for matching against the buyback table in Excel.
    grouped["key"] = (grouped["ticker"] + "-"
                      + grouped["fiscal_year"].astype(str) + "-"
                      + grouped["quarter"])

    columns = ["key", "ticker", "fiscal_year", "quarter", "period_end",
               "avg_price", "trading_days", "complete_quarter"]
    return grouped[columns].sort_values(["ticker", "period_end"])


def current_prices(closes):
    """Most recent closing price for each ticker."""
    latest = closes.ffill().iloc[-1]
    as_of = closes.index[-1].date()

    out = (latest.round(2)
                 .rename("current_price")
                 .reset_index())
    out.columns = ["ticker", "current_price"]
    out["as_of_date"] = as_of
    return out


# ---------------------------------------------------------------- main


def main():
    closes = download_closes()

    quarterly = to_quarterly(closes)
    quarterly.to_csv("quarterly_prices.csv", index=False)

    current = current_prices(closes)
    current.to_csv("current_prices.csv", index=False)

    print("Wrote quarterly_prices.csv and current_prices.csv\n")

    print("CURRENT PRICES")
    print(current.to_string(index=False))

    print("\nSPOT CHECK — Delta quarterly averages, 2018")
    check = quarterly[(quarterly["ticker"] == "DAL")
                      & (quarterly["fiscal_year"] == 2018)]
    print(check[["quarter", "avg_price", "trading_days"]].to_string(index=False))

    incomplete = quarterly[~quarterly["complete_quarter"]]
    if not incomplete.empty:
        print("\nINCOMPLETE QUARTERS (still in progress, treat with care)")
        print(incomplete[["ticker", "fiscal_year", "quarter", "trading_days"]]
              .to_string(index=False))


if __name__ == "__main__":
    main()
