# Airline-Buyback-Scorecard
Did $49bn of US airline share repurchases create value? A capital allocation scorecard.

# US Airline Share Repurchases: A Capital Allocation Scorecard

Six US airlines spent **$49.1 billion** buying back their own stock since 2015.
Those shares are worth **$55.4 billion** today — about **1% a year**.

Four of the six would have done better simply repaying debt.

📊 **[Interactive dashboard](https://public.tableau.com/views/Book1_17895923184030/Dashboard1?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)** · 🎥 **[2-minute walkthrough](ADD_VIDEO_LINK)**

---

## The question

A share repurchase is a purchase of an asset. So it can be graded like any
investment: what price was paid, what is it worth now, and what did the same
money earn elsewhere?

Companies disclose how much they spent. Nobody publishes how that money
performed. This project builds it.

**Carriers:** American (AAL), Alaska (ALK), Delta (DAL), JetBlue (JBLU),
Southwest (LUV), United (UAL)
**Period:** Q1 2015 – Q2 2026

---

## Findings

**1. The aggregate return was roughly 1% a year.**
$49.1bn deployed, $55.4bn today. About 87% of the spending happened before 2021,
so most of this capital has had years to work.

**2. Timing was not the problem.**
Each carrier was benchmarked against a version of itself spending the same total,
divided evenly across the same quarters, with no decisions at all. Five of six
beat it. Aggregate timing alpha was **+1.6%**.

This matters because bad timing is the intuitive explanation — airlines earn most
at the top of the cycle, which is when their stock is priciest. The data rejects it.

**3. Four of six lost to repaying debt.**
Compounding the same dollars at an after-tax cost of debt of 3.95% would have
produced $67.9bn instead of $55.4bn. A **$12.4bn** shortfall.

**4. American is the case study.**
Highest leverage in the group at 5.2x net debt/EBITDA entering 2020, the only
negative timing alpha at −21.3%, and $13.5bn destroyed against debt paydown —
more than the $12.1bn it spent, while carrying $24.3bn of debt.

### Results

| Carrier | Spent ($M) | Worth today ($M) | vs. debt paydown ($M) | Timing alpha | Net debt/EBITDA, YE2019 |
|---|---|---|---|---|---|
| Delta | 10,424 | 19,370 | **+4,470** | +3.2% | 1.45x |
| United | 9,750 | 16,822 | **+3,242** | +7.7% | 2.31x |
| Alaska | 2,198 | 1,742 | −982 | +2.0% | 1.13x |
| JetBlue | 1,570 | 395 | −1,720 | +1.7% | 1.38x |
| Southwest | 13,031 | 12,938 | −3,903 | +1.4% | −0.02x |
| American | 12,107 | 4,180 | **−13,537** | **−21.3%** | **5.21x** |

Prices as of 4 September 2026. All results move with the market.

---

## Conclusion

The failure wasn't timing. It was the alternative these carriers passed up.

A leveraged cyclical business shouldn't repurchase shares until its balance
sheet can survive a downturn. Repurchases are what you do with capital that
has no better use. For four of these six, it had one.

---

## Method

shares purchased = quarterly repurchase $ ÷ that quarter's average price
value today = shares purchased × closing price on the as-of date
timing alpha = actual value ÷ even-spread value − 1
debt alternative = Σ [quarterly $ × (1 + after-tax cost of debt) ^ years elapsed]
S&P alternative = Σ [quarterly $ ÷ SPY quarterly price] × SPY today
net debt/EBITDA = (debt + lease liabilities − cash − ST investments) ÷ (operating income + D&A)


Three benchmarks, each using the same dollars on the same dates:

1. **Even-spread schedule** — isolates timing from stock performance, since the
   imaginary version experiences identical price movements.
2. **Debt paydown** — the alternative actually available to management.
3. **S&P 500** — the shareholder's counterfactual.

---

## Data sources

| Input | Source |
|---|---|
| Quarterly repurchase dollars | SEC XBRL company-concept API, `PaymentsForRepurchaseOfCommonStock`, forms 10-K and 10-Q |
| Share prices | Yahoo Finance daily adjusted closes via `yfinance`, averaged across all trading days per quarter |
| FY2019 leverage | FY2019 10-K balance sheets and income statements |

10-Q cash flow statements report year-to-date figures, so quarterly amounts are
derived by differencing consecutive YTD values, with Q4 backed out of the 10-K.

Prices are dividend- and split-adjusted on both sides of every comparison.

---

## Repository contents

| File | Purpose |
|---|---|
| `fetch_buybacks.py` | Pulls quarterly repurchase dollars, converts YTD to quarterly |
| `fetch_prices.py` | Pulls daily prices for six carriers plus SPY, averages to quarters |
| `fetch_leverage.py` | Pulls FY2019 leverage components, prints the XBRL tag used for each |
| `Airline_Project.xlsx` | The model — quarterly detail, summary, benchmarks, assumptions |
| `tableau_data.csv` | Flat table behind the dashboard, 276 carrier-quarters |

### Reproducing

```bash
pip install requests pandas yfinance

python fetch_buybacks.py    # → raw_buybacks.csv
python fetch_prices.py      # → quarterly_prices.csv, current_prices.csv
python fetch_leverage.py    # → leverage_2019.csv
```

The SEC requires a contact email in the `User-Agent` header and returns 403
without one. Edit the `USER_AGENT` line in `fetch_buybacks.py` and
`fetch_leverage.py` before running.

---

## Limitations

**Quarterly average price is a proxy.** Actual execution prices are disclosed
monthly in Item 5 of each 10-Q and will differ.

**Three carriers' debt figures were entered by hand.** `fetch_leverage.py`
found no match for American, Southwest, and JetBlue because they tag long-term
debt under names outside the script's candidate list. The script prints which
tag it used for every figure, so the gaps were visible rather than silent. Those
values came from the FY2019 10-K debt notes.

**The even-spread benchmark holds start and stop dates constant.** It tests
allocation within each carrier's active window, not the decision to be active
at all. Delta gets no credit for stopping in early 2020.

**The debt benchmark is not meaningful for Southwest**, which held net cash at
the end of 2019 and had no debt to repay.

**Leverage does not cleanly explain outcomes.** Correlation between 2019
leverage and value destroyed is about −0.38 across six carriers, driven almost
entirely by American. It is a case study, not a trend.

**In the workbook:** blue text is a typed input, black is a formula. Blank cells
mean not yet filed; zeros mean no repurchases reported.
