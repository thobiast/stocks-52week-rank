# -*- coding: utf-8 -*-
from unittest.mock import patch

import pandas as pd
import pytest

from src.stocks_52week_rank import StockDataProcessor, StockInfo

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


@pytest.fixture
def stock_processor():
    """
    Fixture to create a StockDataProcessor instance.

    This initializes a StockDataProcessor instance with a list of mock stock tickers.

    Returns:
    StockDataProcessor: An instance of StockDataProcessor initialized with mock tickers.
    """
    return StockDataProcessor(list(mock_stocks_prices.keys()))


@pytest.fixture
def populated_stock_processor(stock_processor):
    """
    Fixture to create a StockDataProcessor instance with populated stock data.

    This fixture initializes a StockDataProcessor instance using the stock_processor
    fixture and populates its stock_data attribute with precomputed expected values
    for each stock ticker.

    Parameters:
    stock_processor (StockDataProcessor): An instance of StockDataProcessor initialized
    with mock tickers.

    Returns:
    StockDataProcessor: An instance of StockDataProcessor with populated stock data.
    """
    stock_processor.stock_data = {}
    for ticker, prices in mock_stocks_prices.items():
        expected_values = compute_expected_values(prices)
        stock_info = StockInfo(
            ticker=ticker,
            current_price=expected_values["current_price"],
            high_52_week=expected_values["high_52_week"],
            low_52_week=expected_values["low_52_week"],
            current_pct_from_low=expected_values["current_pct_from_low"],
            moving_average_200d=expected_values["moving_average_200d"],
        )
        stock_processor.stock_data[ticker] = stock_info

    return stock_processor


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
def test_fetch_stock_data(mock_yf_download, stock_processor, ticker, expected_data):
    """
    Test the fetch_stock_data method.

    Parameters:
    mock_yf_download (Mock): Mock object for yfinance.download.
    stock_processor (StockDataProcessor): Instance of StockDataProcessor to be tested.
    ticker (str): The stock ticker symbol being tested.
    expected_data (dict): A dictionary containing the expected stock metrics, including:
        - current_price (float): The most recent stock price.
        - high_52_week (float): The highest stock price in the past 52 weeks.
        - low_52_week (float): The lowest stock price in the past 52 weeks.
        - current_pct_from_low (float): The percentage increase from the lowest price.
        - moving_average_200d (float): The 200-day moving average of the stock price.
    """
    # Mock yfinance.download
    mock_yf_download.return_value = pd.DataFrame({"Close": mock_pd_prices_data})

    # Execute the method
    stock_processor.fetch_stock_data()

    # Get stock_info for the ticker
    stock_info = stock_processor.stock_data.get(ticker)
    assert stock_info is not None

    assert stock_info.current_price == expected_data["current_price"]
    assert stock_info.high_52_week == expected_data["high_52_week"]
    assert stock_info.low_52_week == expected_data["low_52_week"]
    assert stock_info.current_pct_from_low == expected_data["current_pct_from_low"]
    assert stock_info.moving_average_200d == expected_data["moving_average_200d"]


def test_sort_stock_data(populated_stock_processor):
    """
    Test the sort_stock_data method.
    """
    # Execute the method to get data sorted by the
    # current percentage from the 52-week low
    sorted_data = populated_stock_processor.sort_stock_data()
    # Get only current_pct_from_low values from sorted_data
    current_pct_from_low = [data.current_pct_from_low for data in sorted_data]

    # Verify that current_pct_from_low values are sorted
    assert current_pct_from_low == sorted(current_pct_from_low)


@pytest.mark.parametrize(
    "top_n, expected_sorted_tickers",
    [
        (3, ["AAAC", "AAAB", "AAAD"]),
        (5, ["AAAC", "AAAB", "AAAD", "AAAA", "AAAE"]),
    ],
)
def test_create_dataframe(stock_processor, top_n, expected_sorted_tickers):
    """
    Test the create_dataframe method.
    """
    # Manually set stock_data
    stock_processor.stock_data = {
        "AAAA": StockInfo(
            ticker="AAAA",
            current_price=1,
            high_52_week=2,
            low_52_week=1,
            current_pct_from_low=50.0,
            moving_average_200d=1,
        ),
        "AAAB": StockInfo(
            ticker="AAAB",
            current_price=1,
            high_52_week=2,
            low_52_week=2,
            current_pct_from_low=25.0,
            moving_average_200d=2,
        ),
        "AAAC": StockInfo(
            ticker="AAAC",
            current_price=1,
            high_52_week=2,
            low_52_week=1,
            current_pct_from_low=15.0,
            moving_average_200d=1,
        ),
        "AAAD": StockInfo(
            ticker="AAAD",
            current_price=1,
            high_52_week=2,
            low_52_week=1,
            current_pct_from_low=33.0,
            moving_average_200d=1,
        ),
        "AAAE": StockInfo(
            ticker="AAAE",
            current_price=1,
            high_52_week=2,
            low_52_week=2,
            current_pct_from_low=60.0,
            moving_average_200d=1,
        ),
    }

    # Execute the method
    df = stock_processor.create_dataframe(top=top_n)

    assert df.shape[0] == top_n
    for idx, ticker in enumerate(expected_sorted_tickers[:top_n]):
        assert df.loc[idx, "ticker"] == ticker
