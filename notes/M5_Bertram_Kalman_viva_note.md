# Bertram's optimal bands and the Kalman filter: viva note (M5, task T49)

## 1. Bertram's question
Take the centred spread dX = −κX dt + σ dW (θ removed). A trade is one cycle: enter at a,
exit at m > a, then wait for X to come back to a. With round-trip cost c the profit per cycle is
m − a − c. **Which bands maximise the expected return per unit time, (m − a − c) / E[T]?**
(Bertram 2010, Physica A.) We use symmetric bands a = −m and, in S3, flip long/short at ±m.

## 2. Expected cycle time from first-passage times
Let u(x) = expected time to first hit level m starting from x < m. Itô's lemma on u(X_t) plus
optional stopping gives the **Kolmogorov backward equation**

    (1/2) σ² u''(x) − κ x u'(x) = −1,   u(m) = 0,   u' bounded as x → −∞.

It is a first-order linear ODE in u'. With the scale density s(y) = exp(κy²/σ²):

    u'(x) = −(2/σ²) s(x) ∫_{−∞}^{x} e^{−κz²/σ²} dz.

So the up-crossing time a → m is T_up = (2/σ²) ∫_a^m s(y) ∫_{−∞}^{y} e^{−κz²/σ²} dz dy, and the
down-crossing m → a has ∫_{y}^{∞} instead. **Adding them, the inner integrals join into one
Gaussian integral** √(πσ²/κ), and with ∫ e^{u²} du = (√π/2) erfi(u):

    E[T] = T_up + T_down = (π/κ) [ erfi(m√κ/σ) − erfi(a√κ/σ) ],   erfi(x) = (2/√π) ∫_0^x e^{t²} dt.

erfi grows like e^{x²}, so E[T] explodes for wide bands: the spread rarely wanders that far.

## 3. The optimal band
μ(−m, m) = (2m − c) / E[T] is maximised numerically over m (`bertram_bands`). Facts to quote:
- **m* depends only on c / σ_eq**, with σ_eq = σ/√(2κ): writing m√κ/σ = m/(√2 σ_eq) shows κ only
  scales E[T] by 1/κ. Faster pairs earn proportionally more at the same band (E3, right panel).
- **m* rises with cost** (0.54, 0.96, 1.26 σ_eq at c = 0.1, 0.5, 1 σ_eq) and **tends to 0 when
  trading is free**: with no cost, trade every tiny oscillation.
- Bertram also derives the variance per trade and a Sharpe-maximising band, which is wider. We
  implement the return-maximising version.

## 4. What our checks showed (T50, E3)
- The erfi formula equals a direct numerical integration of the backward-equation solution
  (to 10⁻⁸), and the optimiser matches a 20,000-point grid.
- Simulated cycles converge to the formula as monitoring gets finer: at a 0.25 σ_eq band the
  cycle is 99% too long when checked daily, 28% at 1/10 day, 5% at 1/200 day.
- **Discrete monitoring bias:** a path can cross a band and come back between two checks. A rule
  that checks once a day completes cycles 35–99% more slowly than the formula assumes, so
  Bertram's return per unit time is optimistic for daily trading (part of M1's E4 gap).
- **Other assumptions that fail in practice:** κ and σ are treated as known (they are estimated,
  and κ̂ is biased upward, E1); the spread is assumed to stay OU forever (many selected pairs
  break, E5b); no stop-loss.

## 5. The Kalman filter hedge ratio (E10)
Let the regression drift: state x_t = (μ_t, β_t) is a random walk, observation is the log price.

    x_t = x_{t−1} + w_t,        w_t ~ N(0, V_w),  V_w = δ/(1−δ) I
    a_t = μ_t + β_t b_t + e_t,  e_t ~ N(0, V_e)

Each day, with h_t = (1, b_t):
- predict: R = P + V_w, forecast â_t = h_t x̂, forecast variance Q_t = h_t R h_tᵀ + V_e;
- forecast error e_t = a_t − â_t (uses data up to t−1 only: **no look-ahead**);
- update: gain K = R h_tᵀ / Q_t, x̂ ← x̂ + K e_t, P ← R − K h_t R.

The trading signal is z_t = e_t / √Q_t, opened at ±1 and closed at 0 (Chan 2013).

**δ and V_e decide everything.** δ sets how fast β_t adapts; V_e how noisy the observation is.
If the model is right, z_t is standard normal.

## 6. What E10 showed
- As specified (δ = 10⁻⁴ on log prices, V_e = formation spread variance) the Sharpe ratio is −0.12,
  with 119 trades held 3.6 days.
- β_t moves about 0.01 a day, so the filter absorbs most of the spread: the forecast error has 31%
  of the static spread's standard deviation. V_e is then far too large, so sd(z) = 0.21, not 1,
  and |z| > 1 on only 0.5% of days. **The filter explains away the mean reversion it should trade.**
- Fix (future work): estimate δ and V_e by maximum likelihood on the formation window (maximise
  Σ log N(e_t; 0, Q_t)). Not done, because choosing δ after seeing the backtest would be tuning.

## 7. Likely viva questions
- *Where does the erfi come from?* Integrating the backward equation twice; the Gaussian inner
  integrals combine when up- and down-crossing times are added.
- *Why does m* not depend on κ?* κ only rescales time; in σ_eq units the shape of μ(m) is fixed.
- *Why do real cycles take longer than the formula?* Discrete (daily) monitoring misses crossings.
- *Why is m* → 0 with zero cost optimal?* Return per unit time favours many tiny round trips when
  they are free; costs make each trade need a minimum profit.
- *Why did the Kalman rule fail?* Mis-set noise parameters let β absorb the spread; z is not
  standard normal. Estimate δ and V_e by maximum likelihood.
- *Does the Kalman filter use future data?* No: every value at day t uses the prior (data to t−1).

References: Bertram (2010); Elliott, van der Hoek & Malcolm (2005); Chan (2013); Kloeden & Platen (1992).
