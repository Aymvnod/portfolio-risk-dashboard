# Portfolio Risk Dashboard

A Streamlit app I built to explore portfolio risk and performance using real market data. You pick your tickers, set your weights, and it pulls historical prices via `yfinance` and shows you the numbers that actually matter. Sharpe ratio, drawdown, volatility, correlation between assets, and where your portfolio sits on the efficient frontier.

I built this to get more hands-on with portfolio theory beyond just reading about it.

---

## What it does

- Enter 3–10 tickers (stocks or ETFs)
- Pick a date range and assign weights to each position
- Weights don't have to sum to 100%. it normalises them automatically
- Pulls adjusted closing prices from Yahoo Finance
- Shows annualised return, volatility, Sharpe ratio, and max drawdown
- Plots cumulative portfolio value over time given an initial investment amount
- Correlation heatmap between all selected assets
- Runs a Monte Carlo simulation across thousands of random long-only portfolios and highlights the max Sharpe and min volatility points

---

## Some portfolios worth trying

```
AAPL, MSFT, NVDA, JPM, SPY
SPY, QQQ, IWM, GLD, TLT
JPM, BAC, GS, MS, C
XOM, CVX, COP, SLB, SPY
```

---

## The finance behind it

**Daily returns** — percentage change in adjusted close price from one day to the next.

**Portfolio return** — weighted sum of each asset's daily return. If you're 40% AAPL and 60% MSFT, each day's portfolio return is just those two returns blended by weight.

**Annualised return** — compounds the daily return series out to a yearly figure.

**Annualised volatility** — standard deviation of daily returns scaled by √252 (trading days in a year).

**Sharpe ratio** — how much return you're getting per unit of risk taken:
```
(Annualised Return − Risk-Free Rate) / Annualised Volatility
```
You can set the risk-free rate yourself in the sidebar.

**Max drawdown** — the worst peak-to-trough drop in the portfolio over the selected period.

**Correlation** — how closely assets move together. Lower correlation generally means better diversification.

The optimisation is a Monte Carlo approximation, so treat it as directional, not exact.

---

## Setup

```bash
git clone <your-repo-url>
cd portfolio-risk-dashboard
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Project layout

```
portfolio-risk-dashboard/
  app.py
  requirements.txt
  README.md
```

---

## Notes

- Data comes from Yahoo Finance via `yfinance`. If a ticker returns nothing, double-check the symbol.
- London-listed stocks usually need a `.L` suffix (e.g. `SHEL.L`).
- Short date ranges give noisy estimates, a year or more works better.

---

*For educational purposes only. Not financial advice.*
