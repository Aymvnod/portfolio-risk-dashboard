from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


TRADING_DAYS = 252
MIN_TICKERS = 3
MAX_TICKERS = 10
DEFAULT_SIMULATIONS = 5000


st.set_page_config(
    page_title="Portfolio Risk Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stMetricLabel"] {
            color: #475569;
        }
        .small-note {
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.45;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def parse_tickers(raw_tickers: str) -> list[str]:
    """Convert comma or space separated ticker text into unique uppercase tickers."""
    cleaned = raw_tickers.replace(",", " ").split()
    tickers: list[str] = []
    for ticker in cleaned:
        normalized = ticker.strip().upper()
        if normalized and normalized not in tickers:
            tickers.append(normalized)
    return tickers


@st.cache_data(ttl=60 * 30, show_spinner=False)
def load_adjusted_prices(tickers: tuple[str, ...], start: date, end: date) -> pd.DataFrame:
    """Download adjusted close prices and return a tidy ticker-column price frame."""
    data = yf.download(
        list(tickers),
        start=start,
        end=end + timedelta(days=1),
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" not in data.columns.get_level_values(0):
            return pd.DataFrame()
        prices = data["Close"].copy()
    else:
        prices = data[["Close"]].copy()
        prices.columns = [tickers[0]]

    prices = prices.dropna(axis=1, how="all")
    prices = prices.ffill().dropna(how="any")
    prices.index = pd.to_datetime(prices.index)
    return prices


def annualized_return(returns: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, float]:
    compounded_growth = (1 + returns).prod()
    periods = returns.count()
    return compounded_growth ** (TRADING_DAYS / periods) - 1


def annualized_volatility(returns: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, float]:
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: Union[pd.Series, pd.DataFrame], risk_free_rate: float) -> Union[pd.Series, float]:
    ann_return = annualized_return(returns)
    ann_volatility = annualized_volatility(returns)
    if isinstance(ann_volatility, pd.Series):
        return (ann_return - risk_free_rate) / ann_volatility.replace(0, np.nan)
    if ann_volatility == 0:
        return np.nan
    return (ann_return - risk_free_rate) / ann_volatility


def max_drawdown(returns: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, float]:
    cumulative = (1 + returns).cumprod()
    running_peak = cumulative.cummax()
    drawdown = cumulative / running_peak - 1
    return drawdown.min()


def format_percent(value: float) -> str:
    if pd.isna(value) or np.isinf(value):
        return "N/A"
    return f"{value:.2%}"


def format_number(value: float) -> str:
    if pd.isna(value) or np.isinf(value):
        return "N/A"
    return f"{value:.2f}"


def build_metric_cards(portfolio_returns: pd.Series, risk_free_rate: float) -> None:
    ann_return = annualized_return(portfolio_returns)
    ann_vol = annualized_volatility(portfolio_returns)
    sharpe = sharpe_ratio(portfolio_returns, risk_free_rate)
    drawdown = max_drawdown(portfolio_returns)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Annualized Return", format_percent(ann_return))
    metric_cols[1].metric("Annualized Volatility", format_percent(ann_vol))
    metric_cols[2].metric("Sharpe Ratio", format_number(sharpe))
    metric_cols[3].metric("Maximum Drawdown", format_percent(drawdown))


def make_portfolio_value_chart(portfolio_value: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=portfolio_value.index,
            y=portfolio_value,
            mode="lines",
            name="Portfolio Value",
            line=dict(color="#0f766e", width=3),
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Cumulative Portfolio Value",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def make_correlation_heatmap(returns: pd.DataFrame) -> go.Figure:
    corr = returns.corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig.update_layout(
        title="Asset Return Correlation",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        coloraxis_colorbar=dict(title="Correlation"),
    )
    return fig


def make_drawdown_chart(portfolio_returns: pd.Series) -> go.Figure:
    cumulative = (1 + portfolio_returns).cumprod()
    drawdown = cumulative / cumulative.cummax() - 1

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown,
            fill="tozeroy",
            mode="lines",
            name="Drawdown",
            line=dict(color="#be123c", width=2),
            hovertemplate="%{x|%b %d, %Y}<br>%{y:.2%}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Portfolio Drawdown",
        xaxis_title="Date",
        yaxis_title="Drawdown",
        yaxis_tickformat=".0%",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def asset_statistics(returns: pd.DataFrame, risk_free_rate: float) -> pd.DataFrame:
    stats = pd.DataFrame(
        {
            "Annual Return": annualized_return(returns),
            "Annual Volatility": annualized_volatility(returns),
            "Sharpe Ratio": sharpe_ratio(returns, risk_free_rate),
            "Max Drawdown": max_drawdown(returns),
        }
    )
    return stats


@st.cache_data(show_spinner=False)
def simulate_portfolios(
    returns: pd.DataFrame,
    risk_free_rate: float,
    number_of_portfolios: int,
) -> pd.DataFrame:
    """Generate random long-only portfolios for simple portfolio optimization."""
    mean_returns = returns.mean() * TRADING_DAYS
    covariance_matrix = returns.cov() * TRADING_DAYS
    tickers = returns.columns.tolist()
    results = []
    rng = np.random.default_rng(42)

    for _ in range(number_of_portfolios):
        weights = rng.random(len(tickers))
        weights = weights / weights.sum()

        portfolio_return = float(np.dot(weights, mean_returns))
        portfolio_volatility = float(np.sqrt(weights.T @ covariance_matrix @ weights))
        portfolio_sharpe = (
            (portfolio_return - risk_free_rate) / portfolio_volatility
            if portfolio_volatility > 0
            else np.nan
        )

        row = {
            "Return": portfolio_return,
            "Volatility": portfolio_volatility,
            "Sharpe Ratio": portfolio_sharpe,
        }
        row.update({f"Weight {ticker}": weight for ticker, weight in zip(tickers, weights)})
        results.append(row)

    return pd.DataFrame(results)


def make_optimization_chart(simulations: pd.DataFrame, max_sharpe: pd.Series, min_volatility: pd.Series) -> go.Figure:
    fig = px.scatter(
        simulations,
        x="Volatility",
        y="Return",
        color="Sharpe Ratio",
        color_continuous_scale="Viridis",
        template="plotly_white",
        hover_data={
            "Volatility": ":.2%",
            "Return": ":.2%",
            "Sharpe Ratio": ":.2f",
        },
    )
    fig.add_trace(
        go.Scatter(
            x=[max_sharpe["Volatility"]],
            y=[max_sharpe["Return"]],
            mode="markers",
            name="Max Sharpe",
            marker=dict(color="#dc2626", size=14, symbol="star"),
            hovertemplate="Max Sharpe<br>Return: %{y:.2%}<br>Volatility: %{x:.2%}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[min_volatility["Volatility"]],
            y=[min_volatility["Return"]],
            mode="markers",
            name="Min Volatility",
            marker=dict(color="#2563eb", size=12, symbol="diamond"),
            hovertemplate="Min Volatility<br>Return: %{y:.2%}<br>Volatility: %{x:.2%}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Simulated Portfolios",
        xaxis_title="Annualized Volatility",
        yaxis_title="Annualized Return",
        xaxis_tickformat=".0%",
        yaxis_tickformat=".0%",
        height=560,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        coloraxis_colorbar=dict(
            title="Sharpe Ratio",
            y=0.45,
            len=0.65,
            thickness=18,
        ),
        margin=dict(l=20, r=90, t=95, b=30),
    )
    return fig


def extract_weight_table(portfolio: pd.Series, tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Ticker": tickers,
            "Weight": [portfolio[f"Weight {ticker}"] for ticker in tickers],
        }
    )


def show_invalid_ticker_message(requested: Iterable[str], returned: Iterable[str]) -> None:
    missing = sorted(set(requested) - set(returned))
    if missing:
        st.warning(
            "No usable adjusted price data was found for: "
            + ", ".join(missing)
            + ". Check spelling, exchange suffixes, or date coverage."
        )


st.title("Portfolio Risk Dashboard")
st.caption("A clean risk analytics dashboard for equity and ETF portfolios.")

with st.sidebar:
    st.header("Portfolio Inputs")

    ticker_text = st.text_input(
        "Stock tickers",
        value="AAPL, MSFT, NVDA, JPM, SPY",
        help="Enter 3 to 10 tickers separated by commas or spaces.",
    )
    tickers = parse_tickers(ticker_text)

    today = date.today()
    default_start = today.replace(year=today.year - 5)
    start_date = st.date_input("Start date", value=default_start, max_value=today)
    end_date = st.date_input("End date", value=today, max_value=today)

    initial_investment = st.number_input(
        "Initial investment ($)",
        min_value=100.0,
        value=10000.0,
        step=500.0,
        format="%.2f",
    )

    risk_free_rate = st.slider(
        "Risk-free rate",
        min_value=0.0,
        max_value=0.10,
        value=0.04,
        step=0.0025,
        format="%.2f",
        help="Annual risk-free rate used in Sharpe ratio calculations.",
    )

    normalize_weights = st.checkbox(
        "Normalize weights automatically",
        value=True,
        help="Scale entered weights to sum to 100%.",
    )

    show_optimization = st.checkbox(
        "Show optimal portfolio",
        value=True,
        help="Simulate long-only portfolios and highlight the max-Sharpe and min-volatility portfolios.",
    )

    number_of_portfolios = st.slider(
        "Optimization simulations",
        min_value=1000,
        max_value=20000,
        value=DEFAULT_SIMULATIONS,
        step=1000,
        help="More simulations can improve the search but may run more slowly.",
        disabled=not show_optimization,
    )

    st.subheader("Weights")
    raw_weights: dict[str, float] = {}
    if MIN_TICKERS <= len(tickers) <= MAX_TICKERS:
        equal_weight = round(100 / len(tickers), 2)
        for ticker in tickers:
            raw_weights[ticker] = st.number_input(
                f"{ticker} weight (%)",
                min_value=0.0,
                max_value=100.0,
                value=equal_weight,
                step=1.0,
                format="%.2f",
            )
    else:
        st.info("Enter 3 to 10 valid ticker symbols to configure weights.")

run_analysis = st.sidebar.button("Run analysis", type="primary", width="stretch")

if not run_analysis:
    st.info("Configure your portfolio in the sidebar, then run the analysis.")
    st.markdown(
        '<p class="small-note">Tip: Try AAPL, MSFT, NVDA, JPM, and SPY for a diversified technology, financials, and broad-market example.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

if len(tickers) < MIN_TICKERS or len(tickers) > MAX_TICKERS:
    st.error(f"Please enter between {MIN_TICKERS} and {MAX_TICKERS} unique tickers.")
    st.stop()

if start_date >= end_date:
    st.error("Start date must be earlier than end date.")
    st.stop()

weight_sum = sum(raw_weights.values())
if weight_sum <= 0:
    st.error("Portfolio weights must add to more than 0%.")
    st.stop()

if not np.isclose(weight_sum, 100.0, atol=0.01):
    if normalize_weights:
        st.warning(f"Weights add to {weight_sum:.2f}%, so they were normalized to 100%.")
    else:
        st.warning(f"Weights add to {weight_sum:.2f}%. Enable normalization or adjust them to 100%.")
        st.stop()

weights = pd.Series(raw_weights, dtype=float) / weight_sum

with st.spinner("Downloading price data and calculating portfolio risk metrics..."):
    prices = load_adjusted_prices(tuple(tickers), start_date, end_date)

if prices.empty:
    st.error("No price data was returned. Check the tickers, dates, and internet connection.")
    st.stop()

show_invalid_ticker_message(tickers, prices.columns)

valid_tickers = [ticker for ticker in tickers if ticker in prices.columns]
if len(valid_tickers) < MIN_TICKERS:
    st.error("Fewer than 3 selected tickers have usable price data. Please update your inputs.")
    st.stop()

prices = prices[valid_tickers]
weights = weights.loc[valid_tickers]
weights = weights / weights.sum()

returns = prices.pct_change().dropna()
if returns.empty or len(returns) < 2:
    st.error("Not enough price history is available to calculate returns for this date range.")
    st.stop()

portfolio_returns = returns.dot(weights)
portfolio_value = initial_investment * (1 + portfolio_returns).cumprod()
stats = asset_statistics(returns, risk_free_rate)

st.subheader("Portfolio Overview")
build_metric_cards(portfolio_returns, risk_free_rate)

st.markdown(
    f'<p class="small-note">Analysis uses {len(returns):,} daily return observations from {returns.index.min().date()} to {returns.index.max().date()}.</p>',
    unsafe_allow_html=True,
)

st.plotly_chart(make_portfolio_value_chart(portfolio_value), width="stretch")

left_col, right_col = st.columns(2)
with left_col:
    st.plotly_chart(make_drawdown_chart(portfolio_returns), width="stretch")
with right_col:
    st.plotly_chart(make_correlation_heatmap(returns), width="stretch")

st.subheader("Asset Statistics")
formatted_stats = stats.copy()
for column in ["Annual Return", "Annual Volatility", "Max Drawdown"]:
    formatted_stats[column] = formatted_stats[column].map(format_percent)
formatted_stats["Sharpe Ratio"] = formatted_stats["Sharpe Ratio"].map(format_number)
st.dataframe(formatted_stats, width="stretch")

st.subheader("Portfolio Weights")
weights_display = pd.DataFrame(
    {
        "Ticker": weights.index,
        "Weight": weights.values,
    }
)
fig_weights = px.bar(
    weights_display,
    x="Ticker",
    y="Weight",
    text=weights_display["Weight"].map(lambda value: f"{value:.1%}"),
    color="Ticker",
    template="plotly_white",
)
fig_weights.update_layout(
    showlegend=False,
    yaxis_tickformat=".0%",
    yaxis_title="Weight",
    xaxis_title="Ticker",
    margin=dict(l=20, r=20, t=20, b=20),
)
st.plotly_chart(fig_weights, width="stretch")

if show_optimization:
    st.subheader("Optimal Portfolio")
    simulations = simulate_portfolios(returns, risk_free_rate, number_of_portfolios)
    max_sharpe_portfolio = simulations.loc[simulations["Sharpe Ratio"].idxmax()]
    min_volatility_portfolio = simulations.loc[simulations["Volatility"].idxmin()]

    st.plotly_chart(
        make_optimization_chart(simulations, max_sharpe_portfolio, min_volatility_portfolio),
        width="stretch",
    )

    opt_col_1, opt_col_2 = st.columns(2)
    with opt_col_1:
        st.markdown("#### Max Sharpe Portfolio")
        st.metric("Expected Annual Return", format_percent(max_sharpe_portfolio["Return"]))
        st.metric("Expected Annual Volatility", format_percent(max_sharpe_portfolio["Volatility"]))
        st.metric("Expected Sharpe Ratio", format_number(max_sharpe_portfolio["Sharpe Ratio"]))
        max_sharpe_weights = extract_weight_table(max_sharpe_portfolio, valid_tickers)
        max_sharpe_weights["Weight"] = max_sharpe_weights["Weight"].map(format_percent)
        st.dataframe(max_sharpe_weights, width="stretch", hide_index=True)

    with opt_col_2:
        st.markdown("#### Minimum Volatility Portfolio")
        st.metric("Expected Annual Return", format_percent(min_volatility_portfolio["Return"]))
        st.metric("Expected Annual Volatility", format_percent(min_volatility_portfolio["Volatility"]))
        st.metric("Expected Sharpe Ratio", format_number(min_volatility_portfolio["Sharpe Ratio"]))
        min_vol_weights = extract_weight_table(min_volatility_portfolio, valid_tickers)
        min_vol_weights["Weight"] = min_vol_weights["Weight"].map(format_percent)
        st.dataframe(min_vol_weights, width="stretch", hide_index=True)

    st.caption(
        "Optimization uses random long-only portfolios based on historical return and covariance estimates. "
        "It is an educational approximation, not a recommendation."
    )

with st.expander("View adjusted price data"):
    st.dataframe(prices.tail(20), width="stretch")

st.caption("Educational project only. This dashboard is not financial advice.")
