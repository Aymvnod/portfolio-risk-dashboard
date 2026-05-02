# Portfolio Risk Dashboard

A clean Streamlit web app for analyzing the risk and performance of a stock or ETF portfolio. The dashboard lets a user enter tickers, choose dates, set portfolio weights, download historical adjusted price data with `yfinance`, and view key portfolio risk metrics with Plotly charts.

This project is designed for a student portfolio, GitHub profile, or personal website showcase.

## Features

- Enter 3 to 10 stock or ETF tickers, such as `AAPL, MSFT, NVDA, JPM, SPY`
- Choose a historical start date and end date
- Assign custom portfolio weights to each ticker
- Automatically normalize weights when they do not add to 100%
- Download historical adjusted price data using `yfinance`
- Calculate daily asset returns and portfolio daily returns
- Display annualized return, annualized volatility, Sharpe ratio, and maximum drawdown
- Configure the risk-free rate used in Sharpe ratio calculations
- Choose an initial investment amount and view cumulative portfolio value over time
- Show a Plotly correlation heatmap between selected assets
- Show a table of individual asset statistics
- Simulate long-only portfolios and highlight the maximum Sharpe ratio and minimum volatility portfolios
- Handle invalid tickers and missing data with clear user-friendly messages

## Finance Concepts Used

**Daily returns** measure the percentage change in an asset's adjusted closing price from one trading day to the next.

**Portfolio return** is calculated as the weighted sum of each asset's daily return. For example, if a portfolio is 40% Apple and 60% Microsoft, each daily portfolio return combines those two daily returns using those weights.

**Annualized return** estimates the yearly compound return based on the historical daily return series.

**Annualized volatility** measures the standard deviation of daily returns scaled by the square root of 252, the approximate number of trading days in a year.

**Sharpe ratio** compares excess return to volatility:

```text
Sharpe Ratio = (Annualized Return - Risk-Free Rate) / Annualized Volatility
```

**Maximum drawdown** measures the largest percentage decline from a previous portfolio peak to a later trough.

**Correlation** measures how similarly assets move relative to each other. Highly correlated assets may offer less diversification benefit.

**Optimal portfolio simulation** generates many random long-only portfolios, calculates each portfolio's expected annual return, volatility, and Sharpe ratio, then highlights:

- The portfolio with the highest Sharpe ratio
- The portfolio with the lowest annualized volatility

This is a simple educational approximation of portfolio optimization. It uses historical return and covariance estimates, so it should not be treated as a prediction or recommendation.

## Project Structure

```text
portfolio-risk-dashboard/
  app.py
  requirements.txt
  README.md
```

## Getting Started

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd portfolio-risk-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal.

## Example Inputs

Try these example portfolios:

- `AAPL, MSFT, NVDA, JPM, SPY`
- `SPY, QQQ, IWM, GLD, TLT`
- `JPM, BAC, GS, MS, C`
- `XOM, CVX, COP, SLB, SPY`

## Notes

- The app uses adjusted prices from Yahoo Finance through `yfinance`, so results depend on data availability.
- Some tickers may require exchange suffixes, such as `.L` for certain London-listed securities.
- Very short date ranges may not provide enough observations for meaningful risk metrics.

## Disclaimer

This project is for educational purposes only and is not financial advice. Do not use it as the sole basis for investment decisions.
