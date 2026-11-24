# Backtest engine, evaluation and E4: viva note (M1)

## 1. Position P&L
One unit of spread is $1 long A and $beta short B, so the gross capital is 1 + |beta|. The daily return is
**r_t = held_{t-1} (r^A_t - beta r^B_t) / (1 + |beta|) - cost |held_t - held_{t-1}|**.
Since r^A ~ d ln A and r^B ~ d ln B, r^A - beta r^B ~ d(ln A - beta ln B) = dX: holding the spread earns its
change. (Exactly, by Ito, dA/A = d ln A + sigma_A^2/2 dt, which adds a small drift that changes sign between
long and short trades.) One transaction of a unit trades $(1 + beta), so the cost is c on gross capital and a round trip is 2c
(20 bp US, 30 bp India). In spread units, for Bertram's bands, the round trip is 2c(1 + beta).

## 2. Walk-forward protocol and look-ahead
- Formation 252 days, trade 126 days with every parameter frozen, then roll by 126. Trading windows tile time, so each day is traded once.
- Selection: Engle-Granger p < 0.05 in both directions, beta > 0, half-life 2-63 days, at least 12 crossings a year, ranked by the EG statistic, top K = 20.
- **Signal at the close of t, executed at the close of t+1, first return on day t+2** (`held[1:] = desired[:-1]`). Open positions are closed at the window's last close.
- Lag 0 trades at the same noisy close that created the signal. That noise reverts the next day, so the profit is fake: the S2 Sharpe rises from 0.055 to 0.088. Re-estimating on the trading window ("peeking") gives a Sharpe of 3.6 (NW t = 13.3).
- `test_future_prices_cannot_change_past_returns` scrambles all prices after a date and checks that no earlier return changes.
- Thresholds were never tuned. Design choices were frozen on 2010-21, and 2022-26 is an untouched test block.

## 3. Evaluation
- Returns are on committed capital: K = 20 equal slots, and idle slots earn 0. This is why the annual returns are small. The Sharpe ratio is scale-free. There is no risk-free rate, because the position is self-financing.
- **Lo (2002) Sharpe SE.** By the delta method, Var(SR_d) = (1 + SR_d^2/2)/n; annualise by multiplying by sqrt(252). With SR_d ~ 0 the SE is about 1/sqrt(years): 0.25 for US 15.7 years, 0.27 for India 13.4 years, 0.46 for the 4.7-year test block. Significance needs a Sharpe of about 0.49 in the US. The best is 0.19.
- **Newey-West t.** Positions last about 47 days, so returns are autocorrelated. Bartlett weights, lag = floor(4 (n/100)^(2/9)) = 9. The HAC Sharpe SE (Sharpe / t) is 0.22-0.23, close to Lo's.
- **Sharpe difference vs S0.** Circular block bootstrap with 21-day blocks and 5000 draws, on the same days for both series (this keeps their correlation). p = share of |d* - d| >= |d|. Holm over the 3 comparisons (sort, multiply by 3/2/1, running max). The test block gives 0.344 / 0.917 / 0.917.
- **Trades.** Before costs, S1 earns 44 bp per trade against a 20 bp round trip. Rule exits win about 97% of the time. The 28-45% force-closed at the window's end lose about 3% each, which cancels the gains.

## 4. E4: what would a perfect pair earn?
Synthetic pair: ln A = mu + beta ln B + X, with X an exact OU (kappa = 25, half-life 7.0 days, sigma_eq = 0.03, beta = 1.2,
5 bp per stock per trade). 200 runs of 12 years each, through the real pipeline, with the flip version of Bertram's bands (S3).

**Theory L0.** sigma = sigma_eq sqrt(2 kappa) = 0.212; c = 2 x 5 bp x 2.2 = 0.0022; m* = 0.487 sigma_eq = 0.0146;
m sqrt(kappa)/sigma = 0.344; E[T] = (2 pi/kappa) erfi(0.344) = 0.1016 years (25.6 days). The flip rule earns 2(2m - c) = 0.054 per
cycle, which is 0.532 a year per $1 of A. Divided by 2.2 that is **24.2%**. A 50-checks-a-day simulation gives 24.3%.

| Step | Ann. return % | Cost (points) | Why |
|---|---|---|---|
| L0 theory | 24.2 | | continuous monitoring, true parameters |
| L1 daily checks | 23.1 | 1.1 | overshoot between looks makes cycles longer |
| L2 one-day lag | 20.9 | 2.2 | the gap closes 1 - e^{-kappa/252} = 9.4% a day |
| L3 6-month windows | 20.4 | 0.5 | starts flat, forced close |
| L4a estimate kappa, theta, sigma | 19.5 | 1.0 | kappa_hat/kappa = 1.24, but m in sigma_eq units barely moves (0.50 vs 0.49) |
| L4 estimate beta | 17.2 | 2.3 | median abs(beta_hat - beta) = 0.064 leaves a random-walk piece in the spread |
| L5 EG selection | 12.7 | 4.5 | the pair passes in 74% of windows; 0.74 x 17.2 = 12.7 |

The pipeline earns 53% of theory, and the biggest loss is selection. That matches the real-stock results
(about 8 of 196 US pairs pass, close to the ~10 expected by chance, and only 9% of 259 selected pairs still mean-revert).

## 5. Likely viva questions
- *Why divide by 1 + beta?* It is the gross capital at risk, which makes pairs with different beta comparable.
- *Why lag one day?* A close you use to compute the signal is not a price you can still trade at.
- *Why is the Sharpe SE about 1/sqrt(years)?* Lo's formula with a small daily Sharpe: sqrt(252/n).
- *Why a block bootstrap?* The two series are correlated and autocorrelated, and the blocks keep both.
- *Why Holm?* It controls the family-wise error, is at least as powerful as Bonferroni, and assumes no independence.
- *Why a synthetic pair?* The truth is known, so every point of loss can be attributed.
- *Hit rate 2/3 but no profit?* Losses come from trades that never close, mostly pairs that were never real.

References: Gatev et al. (2006); Bertram (2010); Lo (2002); Newey & West (1987, 1994); Politis & Romano (1992); Ledoit & Wolf (2008); Holm (1979).
