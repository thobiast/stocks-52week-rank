# -*- coding: utf-8 -*-
"""Tests for create_dataframe and YFinanceDataProvider."""

from unittest.mock import patch

import pandas as pd
import pytest

from stocks_52week_rank.main import create_dataframe
from stocks_52week_rank.providers import (
    StockInfo,
    YFinanceDataProvider,
)

# Generate mock data for testing
dates = pd.date_range("2023-01-01", periods=250)
mock_stocks_prices = {
    "AAAA": [150 + i for i in range(250)],
    "AAAB": [300 + i for i in range(250)],
    "AAAC": [1000 + i for i in range(250)],
    "AAAD": [2000 + i for i in range(250)],
    "AAAE": [250 + i for i in range(250)],
}

mock_pd_prices_data = {
    ticker: pd.Series(prices, index=dates)
    for ticker, prices in mock_stocks_prices.items()
}


# Compute expected values
def compute_expected_values(prices):
    """Return expected metric for price series used in the test."""
    current_price = prices[-1]
    high_52_week = max(prices)
    low_52_week = min(prices)
    current_pct_from_low = ((current_price - low_52_week) / low_52_week) * 100
    moving_average_200d = sum(prices[-200:]) / 200
    return {
        "current_price": current_price,
        "high_52_week": high_52_week,
        "low_52_week": low_52_week,
        "current_pct_from_low": current_pct_from_low,
        "moving_average_200d": moving_average_200d,
    }


@pytest.fixture(name="provider")
def _provider():
    """Concrete provider for tests."""
    return YFinanceDataProvider()


@pytest.fixture(name="populated_stock_data")
def _populated_stock_data():
    """
    Build a stock_data dict[str, StockInfo] with deterministic values
    """
    stock_data = {}

    for ticker, prices in mock_stocks_prices.items():
        expected_values = compute_expected_values(prices)
        stock_data[ticker] = StockInfo(
            ticker=ticker,
            current_price=expected_values["current_price"],
            high_52_week=expected_values["high_52_week"],
            low_52_week=expected_values["low_52_week"],
            current_pct_from_low=expected_values["current_pct_from_low"],
            moving_average_200d=expected_values["moving_average_200d"],
        )

    return stock_data


###############
# tests
###############


@patch("yfinance.download")
@pytest.mark.parametrize(
    "ticker, expected_data",
    [
        (ticker, compute_expected_values(prices))
        for ticker, prices in mock_stocks_prices.items()
    ],
)
def test_fetch_stock_data(mock_yf_download, provider, ticker, expected_data):
    """
    Test the fetch_stock_data method.

    Parameters:
        mock_yf_download (Mock): Mock object for yfinance.download.
        provider (YFinanceDataProvider): The data provider instance under test.
        ticker (str): The stock ticker symbol being tested.
        expected_data (dict): A dictionary containing the expected stock metrics, including:
            - current_price (float): The most recent stock price.
            - high_52_week (float): The highest stock price in the past 52 weeks.
            - low_52_week (float): The lowest stock price in the past 52 weeks.
            - current_pct_from_low (float): The percentage increase from the lowest price.
            - moving_average_200d (float): The 200-day moving average of the stock price.
    """
    mock_yf_download.return_value = pd.DataFrame({"Close": mock_pd_prices_data})

    # Execute
    stock_data = provider.fetch_stock_data(list(mock_stocks_prices.keys()))

    # Get stock_info for the ticker
    stock_info = stock_data.get(ticker)
    assert stock_info is not None

    assert stock_info.current_price == expected_data["current_price"]
    assert stock_info.high_52_week == expected_data["high_52_week"]
    assert stock_info.low_52_week == expected_data["low_52_week"]
    assert stock_info.current_pct_from_low == expected_data["current_pct_from_low"]
    assert stock_info.moving_average_200d == expected_data["moving_average_200d"]


def test_dataframe_sorted_by_pct_from_low(populated_stock_data):
    """
    create_dataframe sorts ascending by current_pct_from_low.
    """
    df = create_dataframe(populated_stock_data, top=len(populated_stock_data))

    # After reset_index, the index is 0-based; Rank is a column starting at 1
    assert df.columns[0] == "Rank"
    assert df.loc[0, "Rank"] == 1

    sorted_by_metric = sorted(
        populated_stock_data.values(), key=lambda s: s.current_pct_from_low
    )
    expected_order = [s.ticker for s in sorted_by_metric]

    got_order = list(df["ticker"])
    assert got_order == expected_order


@pytest.mark.parametrize(
    "top_n, expected_sorted_tickers",
    [
        (3, ["AAAD", "AAAC", "AAAB"]),
        (5, ["AAAD", "AAAC", "AAAB", "AAAE", "AAAA"]),
    ],
)
def test_create_dataframe(populated_stock_data, top_n, expected_sorted_tickers):
    """
    create_dataframe returns only top N rows, ordered by current_pct_from_low asc.
    """

    df = create_dataframe(populated_stock_data, top=top_n)

    # shape matches top
    assert df.shape[0] == top_n

    for idx, ticker in enumerate(expected_sorted_tickers[:top_n]):
        assert df.iloc[idx]["ticker"] == ticker
