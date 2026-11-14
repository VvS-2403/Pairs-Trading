# Bertram's optimal bands: viva note (M5, task T49)

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

## 5. Likely viva questions
- *Where does the erfi come from?* Integrating the backward equation twice; the Gaussian inner
  integrals combine when up- and down-crossing times are added.
- *Why does m* not depend on κ?* κ only rescales time; in σ_eq units the shape of μ(m) is fixed.
- *Why do real cycles take longer than the formula?* Discrete (daily) monitoring misses crossings.
- *Why is m* → 0 with zero cost optimal?* Return per unit time favours many tiny round trips when
  they are free; costs make each trade need a minimum profit.

Reference: Bertram (2010).
