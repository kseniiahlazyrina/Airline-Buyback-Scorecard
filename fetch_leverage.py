"""
STEP 6 — Pull FY2019 leverage for each airline.

Net debt / EBITDA at 31 Dec 2019, the last normal year before the shock.

    EBITDA   = operating income + depreciation & amortization
    Net debt = long-term debt + operating lease liabilities
               - cash - short-term investments

Source: SEC XBRL companyfacts API.
Output: leverage_2019.csv

The script PRINTS which XBRL tag it used for every figure. Read those.
Tag choice is where this kind of pull goes quietly wrong, so verify at
least two companies against the actual 10-K before trusting the table.

BEFORE RUNNING: put your real email in USER_AGENT.
"""

import time

import pandas as pd
import requests

# ---------------------------------------------------------------- settings

USER_AGENT = "Karim - UW student project - kseniia@uw.edu"   

CIKS = {
    "DAL":  "0000027904",
    "UAL":  "0000100517",
    "AAL":  "0000006201",
    "LUV":  "0000092380",
    "ALK":  "0000766421",
    "JBLU": "0001158463",
}

FY_END = "2019-12-31"
FY_START = "2019-01-01"

# Candidate tags, tried in order. Companies tag the same concept differently.
INCOME_TAGS = {
    "operating_income": ["OperatingIncomeLoss"],
    "d_and_a": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
    ],
}

BALANCE_TAGS = {
    "lt_debt_noncurrent": ["LongTermDebtNoncurrent"],
    "lt_debt_current": ["LongTermDebtCurrent"],
    "lease_noncurrent": ["OperatingLeaseLiabilityNoncurrent"],
    "lease_current": ["OperatingLeaseLiabilityCurrent"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "short_term_investments": [
        "ShortTermInvestments",
        "MarketableSecuritiesCurrent",
        "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
    ],
}

# ---------------------------------------------------------------- fetching


def fetch_company_facts(cik):
    """One call returns every number this company ever filed."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    return response.json()


def pick_value(facts, tags, is_instant):
    """
    Find the FY2019 value for the first tag that has one.

    is_instant=True  -> balance sheet item (a point in time, no start date)
    is_instant=False -> income statement item (a period, needs start + end)
    """
    for tag in tags:
        entries = (facts.get("facts", {})
                        .get("us-gaap", {})
                        .get(tag, {})
                        .get("units", {})
                        .get("USD", []))

        matches = []
        for entry in entries:
            if entry.get("end") != FY_END:
                continue
            if is_instant and "start" in entry:
                continue
            if not is_instant and entry.get("start") != FY_START:
                continue
            matches.append(entry)

        if not matches:
            continue

        # Prefer the annual report, then the most recently filed version.
        matches.sort(key=lambda e: (e.get("form") == "10-K", e.get("filed", "")))
        return matches[-1]["val"], tag

    return None, None


# ---------------------------------------------------------------- assembly


def build_row(ticker, facts):
    row = {"ticker": ticker}
    used = {}

    for field, tags in INCOME_TAGS.items():
        value, tag = pick_value(facts, tags, is_instant=False)
        row[field] = value
        used[field] = tag

    for field, tags in BALANCE_TAGS.items():
        value, tag = pick_value(facts, tags, is_instant=True)
        row[field] = value
        used[field] = tag

    print(f"\n{ticker} — tags used:")
    for field, tag in used.items():
        status = tag if tag else "NOT FOUND"
        print(f"    {field:<24} {status}")

    return row


def compute_metrics(df):
    """Everything in millions, so the numbers are readable."""
    for column in df.columns:
        if column != "ticker":
            df[column] = pd.to_numeric(df[column], errors="coerce") / 1e6

    df["ebitda"] = df["operating_income"].fillna(0) + df["d_and_a"].fillna(0)

    df["total_debt"] = (df["lt_debt_noncurrent"].fillna(0)
                        + df["lt_debt_current"].fillna(0)
                        + df["lease_noncurrent"].fillna(0)
                        + df["lease_current"].fillna(0))

    df["liquid_assets"] = (df["cash"].fillna(0)
                           + df["short_term_investments"].fillna(0))

    df["net_debt"] = df["total_debt"] - df["liquid_assets"]
    df["net_debt_ebitda"] = (df["net_debt"] / df["ebitda"]).round(2)

    return df


# ---------------------------------------------------------------- main


def main():
    rows = []
    for ticker, cik in CIKS.items():
        facts = fetch_company_facts(cik)
        rows.append(build_row(ticker, facts))
        time.sleep(0.3)

    df = compute_metrics(pd.DataFrame(rows))
    df.to_csv("leverage_2019.csv", index=False)

    print("\n\nFY2019 LEVERAGE ($ millions)\n")
    display_columns = ["ticker", "ebitda", "total_debt", "liquid_assets",
                       "net_debt", "net_debt_ebitda"]
    print(df[display_columns].round(0).to_string(index=False))

    print("\nWrote leverage_2019.csv")
    print("\nVERIFY at least two of these against the FY2019 10-K "
          "before using them.")


if __name__ == "__main__":
    main()
