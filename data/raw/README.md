# Raw price data

Daily adjusted closes from Yahoo Finance via `yfinance`, retrieved 2026-10-26.
Adjusted for splits and dividends (`auto_adjust=True`). Regenerate with `python -m src.data`.

| File | Tickers | First date | Last date | Rows |
| --- | --- | --- | --- | --- |
| us_prices.csv | 59 | 2010-01-04 | 2026-09-29 | 4210 |
| india_prices.csv | 27 | 2012-01-02 | 2026-09-29 | 3637 |

One-day moves above 25%, listed for inspection. Those checked match real events
(for example the 9 March 2020 oil-price crash), not split or spin-off errors:

- us: EOG on 2020-03-09: -32.0%
- us: HAL on 2020-03-09: -37.6%
- us: OXY on 2020-03-09: -52.0%
- us: SLB on 2020-03-09: -27.4%
- us: COP on 2020-03-24: +25.2%
- us: HAL on 2020-03-24: +26.5%
- us: OXY on 2020-06-05: +33.7%
- us: VLO on 2020-11-09: +31.2%
- us: INTC on 2024-08-02: -26.1%
- us: DG on 2024-08-29: -32.1%
- us: ORCL on 2025-09-10: +35.9%
- us: IBM on 2026-07-14: -25.2%
- india: SBIN.NS on 2017-10-25: +27.7%
- india: AXISBANK.NS on 2020-03-23: -27.9%
- india: INDUSINDBK.NS on 2020-03-26: +44.7%
- india: INDUSINDBK.NS on 2025-03-11: -27.2%
