# Cointegration and the Engle-Granger test: viva note (M2, task T27)

## 1. I(1) and cointegration
- A series is **I(1)** if its level wanders like a random walk but its daily changes are
  stationary. Log stock prices are I(1).
- Two I(1) prices are **cointegrated** if some combination a_t − β b_t is stationary: they can
  move apart for a while but are pulled back together. That combination is our spread X_t,
  and the OU model describes how it is pulled back.
- Correlation is not cointegration: two prices can be highly correlated in returns and still
  drift apart for good.

## 2. The Engle-Granger two-step test
1. **Estimate the spread.** OLS on the formation year: a_t = μ + β b_t + u_t. The residuals
   û_t are the estimated spread; β̂ is the hedge ratio.
2. **Test it.** Run the ADF test on û_t. Rejecting a unit root means the spread mean-reverts,
   so the pair is cointegrated.

## 3. Why the critical values change (spurious regression)
- OLS chooses β̂ to make û_t as small as possible, so it cancels as much of the shared
  wandering as it can. The residuals look more stationary than the true spread.
- Even two **unrelated** random walks then often give residuals that seem to mean-revert,
  and a regression of one on the other can show a high R²: a **spurious regression**.
- So the test statistic is pushed towards rejection, and the critical value must be more
  negative: about **−3.34** at 5% for two series, instead of **−2.86** for plain ADF.
- Using −2.86 would find far more "pairs" than really exist.
- **Our experiment (E2b):** on 1,000 pairs of independent random walks, plain ADF critical values wrongly flag **16.9%** as pairs, Engle-Granger **6.2%** (nominal 5%).

## 4. Both directions
Regressing a on b minimises errors in a; regressing b on a minimises errors in b. The two β̂
are not exact reciprocals and the tests can disagree. A pair's labels are arbitrary, so we
keep it only if **both** directions reject at 5%.

## 5. Testing 196 pairs at once
- At 5%, a test flags 5% of pairs even when none is real: about 10 of 196 per window.
- We find about 8.4 per window (3 on the latest window), so many selected pairs are likely
  false positives.
- Benjamini-Hochberg controls the share of false discoveries among the pairs we accept; at
  q = 10% it keeps only about 0.6 pairs per window. We report it, but do not use it to select
  (too few pairs would be left to trade).

## 6. What our results show (E9)
- If the selected pairs had kept their fitted half-lives (median about 7 days), ADF on the next
  six months would flag about **52%** of them. It flags only **9%**.
- Most pairs lose their mean reversion soon after selection, which explains why trades that
  never revert cancel the profit (E5).
- Caveats: ADF on 126 days has limited power (E2a), which is why we compare with 52% rather
  than 100%; and a stronger test result at selection does not predict a higher profit.

## 6b. Other checks (work by Nitin Sureshkumar)
- **Latest window (T13):** only 3 of 196 pairs pass Engle-Granger (JPM/BAC, TXN/INTC, PEP/HSY), fewer than the
  10 expected by chance; none survives Benjamini-Hochberg.
- **Distance baseline S0 (T29):** ranking by log prices instead of price indices keeps 89% of the top 20 pairs.
  Centring the gap on the first formation day (as in the original rule) gives Sharpe -0.18 instead of -0.05, both
  within one standard error of zero, so the ranking of the rules does not change.
- **India selection (T31):** 3.2 of 55 pairs pass per window against 2.75 by chance; 83 pairs in total, 42 of them banks.
- **Data (T08):** one-day moves above 25% were checked and match real events, so no price was edited.
- **Tests:** tests/test_data.py, test_cointegration.py and test_selection.py (40 checks).

## 7. Likely viva questions
- *What is cointegration in one sentence?* Two wandering prices with a combination that does
  not wander.
- *Why not use correlation?* Correlated returns do not stop the prices drifting apart.
- *Why are the critical values different from ADF?* β̂ is estimated to make the residuals look
  stationary (spurious regression), so we need a stricter threshold.
- *Why test both directions?* The regression is not symmetric, and the pair labels are arbitrary.
- *How many false pairs do you expect?* About 5% of 196, roughly 10 per window, which is about
  what we find.
- *Alternative tests?* Johansen (tests both directions at once, more than two series).
