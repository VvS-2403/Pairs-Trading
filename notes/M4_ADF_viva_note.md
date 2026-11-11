# The augmented Dickey-Fuller test: viva note (M4, task T42)

## 1. What a unit root is, and why it matters for pairs
A spread is tradable only if it comes back to its mean. Write the daily spread as an AR(1),
X_t = a + b X_{t-1} + e_t. If |b| < 1 shocks die out (stationary, mean-reverting); if b = 1
every shock is permanent (random walk, "unit root": the root of 1 - b z = 0 is z = 1).
For the OU spread, the exact discretisation gives **b = e^{-kappa Delta}**, so
**b = 1 is the same as kappa = 0**: no mean reversion. Testing for a unit root is testing kappa = 0.

## 2. The Dickey-Fuller regression
Subtract X_{t-1} from both sides: Delta X_t = alpha + gamma X_{t-1} + e_t, gamma = b - 1.
- H0: gamma = 0 (unit root, kappa = 0)   vs   H1: gamma < 0 (stationary, kappa > 0). One-sided.
- Test statistic: the usual t-ratio tau = gamma_hat / SE(gamma_hat).
- We use the "constant, no trend" version (`regression="c"`): a spread can have a non-zero mean
  but should not trend.

## 3. Why the t-ratio is not t-distributed (the Dickey-Fuller distribution)
Under H0 the regressor X_{t-1} is itself a random walk, so its sample variance grows like T^2,
not T. The standard central limit theorem does not apply. The limit is a functional of Brownian motion
(Dickey & Fuller 1979). Without a constant, tau -> (W(1)^2 - 1) / (2 sqrt(int_0^1 W(r)^2 dr));
with a constant, W is replaced by demeaned Brownian motion: tau -> int W~ dW / sqrt(int W~^2 dr).
This distribution is shifted left and skewed. Consequence: **critical values are more negative than
the normal ones**. With a constant: 1% -3.43, 5% -2.86, 10% -2.57 (vs -1.65 for a one-sided normal 5%).
Using -1.65 would reject a true random walk far too often. statsmodels gives MacKinnon (2010)
response-surface p-values, which also correct for finite T.

## 4. Augmentation
If e_t is autocorrelated, the t-ratio's distribution changes. Said & Dickey (1984): add lagged
differences, Delta X_t = alpha + gamma X_{t-1} + sum_{i=1..p} delta_i Delta X_{t-i} + e_t, so the residual is
white noise; the limit distribution of tau is then the same DF distribution. Lag order p chosen by
AIC (`autolag="AIC"`); in E2a we cap p at 5. Too few lags: size distortion; too many: lower power.

## 5. Power: what our experiment E2a shows
Power = P(reject H0 | spread truly mean-reverts). It depends on how far b is from 1 *in the sample*,
i.e. on kappa * T = (ln 2 / half-life) * window. Rejection rate at 5% (300 simulated OU paths per cell):

| half-life \ window | 63 | 126 | **252** | 504 |
|---|---|---|---|---|
| 5 days  | 0.30 | 0.72 | **0.99** | 1.00 |
| 10 days | 0.16 | 0.25 | **0.74** | 1.00 |
| 20 days | 0.13 | 0.13 | **0.30** | 0.73 |
| 40 days | 0.09 | 0.08 | **0.13** | 0.26 |
| 80 days | 0.10 | 0.06 | **0.09** | 0.10 |

Reading: a 12-month window reliably finds half-lives up to about 10 days. A 40-80 day half-life is
almost invisible (rejection close to the 5% size). Power rises with T for fixed half-life because
the test sees more "half-lives" of reversion. Longer windows help power but risk the
relationship breaking within the window, which is the trade-off behind the 252-day formation.

## 6. Size and the Engle-Granger twist (link to M2)
Size = P(reject | H0 true) should be 5%. Our 80-day row (6-10%) is close to it. When the spread is
an OLS residual a - beta b, beta is chosen to make it look stationary, so plain ADF critical values
over-reject. Engle-Granger uses more negative critical values (about -3.34 at 5% for two variables).
That is E2b.

## 7. Likely viva questions
- *Why is ADF a test of kappa = 0?* gamma = e^{-kappa Delta} - 1 = 0 iff kappa = 0.
- *Why not use normal critical values?* Under H0 the regressor is non-stationary; the DF limit is a
  Brownian functional, skewed left.
- *Why augment?* To whiten serially correlated errors so the DF distribution still applies.
- *What does "fail to reject" mean?* Not proof of a random walk: with 252 days and a 20-day half-life
  we fail 70% of the time even though the spread mean-reverts (low power).
- *Alternatives?* KPSS (null = stationary), Phillips-Perron (non-parametric correction), Johansen
  (system cointegration).

References: Dickey & Fuller (1979); Said & Dickey (1984); MacKinnon (2010); Engle & Granger (1987).
