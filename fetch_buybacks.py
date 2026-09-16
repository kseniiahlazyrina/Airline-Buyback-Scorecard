"""
STEP 1 — Pull quarterly share-repurchase dollars for six US airlines.

Source: SEC XBRL company-concept API (free, no key needed).
Output: raw_buybacks.csv — one row per company-quarter.

BEFORE RUNNING: put your real email in USER_AGENT below.
The SEC returns a 403 error if you don't identify yourself.

Run with:  python fetch_buybacks.py
"""

import time

import pandas as pd
import requests

# ---------------------------------------------------------------- settings

USER_AGENT = "Karim - UW student project - kseniia@uw.edu"   # <-- EDIT THIS

CIKS = {
    "DAL":  "0000027904",   # Delta Air Lines
    "UAL":  "0000100517",   # United Airlines Holdings
    "AAL":  "0000006201",   # American Airlines Group
    "LUV":  "0000092380",   # Southwest Airlines
    "ALK":  "0000766421",   # Alaska Air Group
    "JBLU": "0001158463",   # JetBlue Airways
}

# Not every company uses the same XBRL tag for buybacks. Try these in order.
TAGS = [
    "PaymentsForRepurchaseOfCommonStock",
    "PaymentsForRepurchaseOfEquity",
]

START_YEAR = 2015

# ---------------------------------------------------------------- fetching


def fetch_concept(cik, tag):
    """Ask the SEC for every value this company ever reported under one tag."""
    url = (
        f"https://data.sec.gov/api/xbrl/companyconcept/"
        f"CIK{cik}/us-gaap/{tag}.json"
    )
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    if response.status_code == 404:
        return None          # this company never used this tag
    response.raise_for_status()
    return response.json()


def get_facts(ticker, cik):
    """Return every reported fact for one company as a tidy DataFrame."""
    for tag in TAGS:
        data = fetch_concept(cik, tag)
        time.sleep(0.2)                  # stay under the SEC's 10 requests/sec
        if data and data.get("units", {}).get("USD"):
            rows = pd.DataFrame(data["units"]["USD"])
            rows["tag"] = tag
            # Confirms the CIK mapped to the company you actually wanted.
            print(f"  {ticker}: matched '{data['entityName']}'  (tag: {tag})")
            return rows
    print(f"  {ticker}: NO DATA — check the CIK, or add another tag to TAGS")
    return pd.DataFrame()


# ---------------------------------------------------------------- reshaping


def to_quarterly(facts):
    """
    Turn year-to-date cash-flow figures into single quarters.

    A Q3 10-Q reports nine months cumulative, not three. So Q3 alone is
    (nine-month figure) minus (six-month figure). This does that subtraction.
    """
    df = facts.copy()
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    df["filed"] = pd.to_datetime(df["filed"])

    df = df[df["form"].isin(["10-K", "10-Q"])]
    df = df[df["end"].dt.year >= START_YEAR]

    # The same period gets restated in later filings. Keep the newest version.
    df = (
        df.sort_values("filed")
          .drop_duplicates(subset=["start", "end"], keep="last")
    )
    df["days"] = (df["end"] - df["start"]).dt.days

    out = []
    for year, group in df.groupby(df["end"].dt.year):
        # Year-to-date facts are the ones starting on 1 January.
        ytd_rows = group[(group["start"].dt.month == 1)
                         & (group["start"].dt.day <= 3)]
        ytd = dict(zip(ytd_rows["end"].dt.quarter, ytd_rows["val"]))

        # Some companies also tag a standalone three-month figure (~90 days).
        q_rows = group[group["days"].between(80, 100)]
        three_month = dict(zip(q_rows["end"].dt.quarter, q_rows["val"]))

        running_total = 0.0
        for q in (1, 2, 3, 4):
            if q in ytd:
                value = ytd[q] - running_total
                running_total = ytd[q]
                method = "ytd_difference"
            elif q in three_month:
                value = three_month[q]
                running_total += value
                method = "reported_3m"
            else:
                value, method = None, "missing"

            period_end = (pd.Timestamp(year=year, month=q * 3, day=1)
                          + pd.offsets.MonthEnd(0))

            out.append({
                "fiscal_year": year,
                "quarter": f"Q{q}",
                "period_end": period_end.date(),
                "buyback_musd": None if value is None else round(value / 1e6, 1),
                "method": method,
            })

    return pd.DataFrame(out)


# ---------------------------------------------------------------- main


def main():
    print("Fetching from SEC EDGAR...\n")

    frames = []
    for ticker, cik in CIKS.items():
        facts = get_facts(ticker, cik)
        if facts.empty:
            continue
        quarterly = to_quarterly(facts)
        quarterly.insert(0, "ticker", ticker)
        frames.append(quarterly)

    result = (pd.concat(frames, ignore_index=True)
                .sort_values(["ticker", "period_end"]))
    result.to_csv("raw_buybacks.csv", index=False)

    print("\nWrote raw_buybacks.csv\n")
    print("ANNUAL TOTALS ($ millions) — check these against the 10-Ks:\n")
    summary = (result.groupby(["ticker", "fiscal_year"])["buyback_musd"]
                     .sum()
                     .unstack()
                     .round(0))
    print(summary.to_string())


if __name__ == "__main__":
    main()

