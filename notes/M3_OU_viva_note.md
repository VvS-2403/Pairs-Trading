# The Ornstein-Uhlenbeck process: viva note (M3, task T35)

## 1. The model
dX_t = κ(θ − X_t) dt + σ dW_t, κ > 0.
- θ: long-run level of the spread. κ: speed of pull back towards θ. σ: size of the noise.
- If X is above θ the drift is negative, if below it is positive: the spread is pulled back.

## 2. Solving it with Itô's lemma
Apply Itô to Y_t = e^{κt} X_t:
dY = e^{κt}(κX dt + dX) = e^{κt}(κθ dt + σ dW). The X terms cancel, so integrate:

X_t = θ + (X_0 − θ) e^{−κt} + σ ∫_0^t e^{−κ(t−s)} dW_s.

- The stochastic integral of a deterministic function is Gaussian with mean 0 and variance
  σ² ∫ e^{−2κ(t−s)} ds = σ²(1 − e^{−2κt}) / (2κ) (Itô isometry).
- So X_t is **Gaussian**: mean θ + (X_0 − θ)e^{−κt}, variance σ²(1 − e^{−2κt})/(2κ).
- As t → ∞: stationary law **N(θ, σ²/2κ)**; σ_eq = σ/√(2κ) is the spread's typical size.
- **Half-life** ln 2 / κ: the expected gap X − θ halves in that time. With κ in years,
  in trading days it is 252 ln 2 / κ.

## 3. Exact discretisation and estimation
- Over one day Δ = 1/252 the solution gives exactly
  X_{t+Δ} = a + b X_t + ε_t, b = e^{−κΔ}, a = θ(1 − b), Var(ε) = σ²(1 − e^{−2κΔ})/(2κ).
- This is an **AR(1)** with Gaussian errors, so OLS of X_{t+Δ} on X_t is the conditional
  maximum-likelihood estimator.
- Invert: κ̂ = −ln b̂ / Δ, θ̂ = â/(1 − b̂), σ_eq = s_ε/√(1 − b̂²). Valid only if 0 < b̂ < 1.
- A simple step-by-step (Euler) approximation gives only b ≈ 1 − κΔ; the formula above is
  exact. (For OU the Milstein scheme equals Euler, because the noise does not depend on X.)

## 4. What our results show (E1)
- With one year of data κ̂ is **too high**: about 18% for a fast pair (κ = 25, half-life
  7 days), about 96% for a slow pair (κ = 5). The error roughly halves when the window doubles.
- Why: OLS underestimates b in short samples, and b̂ smaller means κ̂ = −ln b̂/Δ larger.
- Consequence: fitted half-lives look shorter than they are, so pairs look faster and more
  attractive than they really are.
- On long 40-year simulated paths the estimator recovers κ, θ and σ closely (check in
  notebook section 3).

## 5. Likely viva questions
- *Solve the OU SDE.* Itô on e^{κt}X_t removes the drift; integrate.
- *Why is X_t Gaussian?* It is a deterministic function plus an Itô integral of a
  deterministic integrand.
- *What is the half-life?* ln 2/κ: time for the expected gap to halve.
- *Why is OLS the MLE?* The exact discretisation is an AR(1) with Gaussian errors.
- *Why is κ̂ biased?* Short samples bias b̂ down, which pushes κ̂ up.
- *When is the estimate invalid?* If b̂ ≥ 1 (no mean reversion) or b̂ ≤ 0.
- *How does ADF connect?* γ = b − 1 = e^{−κΔ} − 1, so testing γ = 0 tests κ = 0 (M4).
