# -*- coding: utf-8 -*-
"""
Data provider interfaces and implementations for fetching stock market data.
"""

import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from polygon import RESTClient

MOVING_AVERAGE_WINDOW = 200


@dataclass(frozen=True)
class StockInfo:
    """Data class to hold stock information."""

    ticker: str
    current_price: float
    high_52_week: float
    low_52_week: float
    current_pct_from_low: float
    moving_average_200d: float


class DataProvider(ABC):
    """Abstract base class for data providers."""

    @abstractmethod
    def fetch_stock_data(self, tickers):
        """
        Fetch and compute stock information for a list of tickers.

        Parameters:
            tickers  list[str]: List of stock tickers to process.

        Returns:
            dict[str, StockInfo]: A dictionary of StockInfo objects with the ticker as the key.
        """


class YFinanceDataProvider(DataProvider):
    """Data provider for Yahoo Finance."""

    def _download_data(self, tickers):
        """
        Download 1-year historical price data from Yahoo Finance.

        Parameters:
            tickers (list[str]): List of stock tickers to download.

        Returns:
            pandas.DataFrame: A DataFrame containing the historical data, or None if download fails.
        """
        logging.info(
            "Downloading stock data for %s tickers from Yahoo Finance.", len(tickers)
        )
        try:
            data = yf.download(tickers, period="1y")
            return data
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error downloading data from yfinance: {e}")
            sys.exit(1)

    def _process_ticker_data(self, ticker, all_data):
        """
        Process the downloaded data for a single ticker to compute metrics.

        Parameters:
            ticker (str): The stock ticker to process.
            all_data (pandas.DataFrame): The DataFrame containing data for all tickers.

        Returns:
            StockInfo: A StockInfo object with the computed metrics.
        """
        ticker_data = all_data["Close"][ticker]
        current_price = ticker_data.iloc[-1]
        high_52_week = ticker_data.max()
        low_52_week = ticker_data.min()
        current_pct_from_low = ((current_price - low_52_week) / low_52_week) * 100
        moving_average_200d = (
            ticker_data.rolling(window=MOVING_AVERAGE_WINDOW).mean().iloc[-1]
        )

        return StockInfo(
            ticker=ticker,
            current_price=current_price,
            high_52_week=high_52_week,
            low_52_week=low_52_week,
            current_pct_from_low=current_pct_from_low,
            moving_average_200d=moving_average_200d,
        )

    def fetch_stock_data(self, tickers):
        """
        Fetch stock information from Yahoo Finance.

        Parameters:
            tickers (list[str]): List of stock tickers to process.

        Returns:
            dict[str, StockInfo]: A dictionary of StockInfo objects with the ticker as the key.
        """
        all_data = self._download_data(tickers)

        stock_data = {}
        for ticker in tickers:
            stock_info = self._process_ticker_data(ticker, all_data)
            stock_data[stock_info.ticker] = stock_info

        logging.info("Successfully processed data for %s stocks.", len(stock_data))
        return stock_data


class PolygonDataProvider(DataProvider):
    """
    Data provider for Polygon.io, using the official polygon-api-client.
    """

    def __init__(self, api_key):
        """
        Initialize PolygonDataProvider.

        Parameters:
            api_key (str): The API key for accessing the Polygon API.
        """
        self.client = RESTClient(api_key)

    def _get_ticker_data(self, ticker, start_date, end_date):
        """
        Fetch raw aggregate and close data for a single ticker from Polygon.io.

        Parameters:
            ticker (str): The stock ticker to fetch data for.
            start_date (datetime.date): The start date for the historical data query.
            end_date (datetime.date): The end date for the historical data query.

        Returns:
            tuple[list, float | None]: (aggregates, previous_close). If no data is
                 available, returns (None, None).
        """
        aggs = self.client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=start_date.strftime("%Y-%m-%d"),
            to=end_date.strftime("%Y-%m-%d"),
            limit=50000,
        )

        if not aggs:
            logging.warning("No aggregate data for ticker '%s' from Polygon.", ticker)
            return None, None

        # 2. Get the most recent closing price
        resp = self.client.get_previous_close_agg(ticker)
        previous_close = resp[0].close if resp else None

        return aggs, previous_close

    def _process_ticker_data(self, ticker, aggs, previous_close):
        """
        Process raw ticker data to compute metrics and create a StockInfo object.

        Parameters:
            ticker (str): The stock ticker being processed.
            aggs (list): A list of aggregate bar objects from the Polygon API.
            previous_close (float): The previous day's closing price.

        Returns:
            StockInfo: A StockInfo object with the computed metrics.
        """
        close_prices = pd.Series([a.close for a in aggs])

        # Use the previous close if available, otherwise fall back to the last in the series
        current_price = previous_close if previous_close else close_prices.iloc[-1]

        # Perform calculations
        high_52_week = close_prices.max()
        low_52_week = close_prices.min()
        current_pct_from_low = ((current_price - low_52_week) / low_52_week) * 100
        moving_average_200d = (
            close_prices.rolling(window=MOVING_AVERAGE_WINDOW).mean().iloc[-1]
        )

        return StockInfo(
            ticker=ticker,
            current_price=current_price,
            high_52_week=high_52_week,
            low_52_week=low_52_week,
            current_pct_from_low=current_pct_from_low,
            moving_average_200d=moving_average_200d,
        )

    def fetch_stock_data(self, tickers):
        """
        Fetch stock information from Polygon.io for multiple tickers.

        Parameters:
            tickers (list[str]): List of stock tickers to process.

        Returns:
            dict[str, StockInfo]: A dictionary of StockInfo objects with the ticker as the key.
        """
        logging.info("Downloading stock data from Polygon.io.")
        stock_data = {}

        # Define the date range for the 52-week data query
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)

        for ticker in tickers:
            try:
                aggs, previous_close = self._get_ticker_data(
                    ticker, start_date, end_date
                )

                if aggs:
                    stock_info = self._process_ticker_data(ticker, aggs, previous_close)
                    stock_data[stock_info.ticker] = stock_info

            except Exception as e:  # pylint: disable=broad-exception-caught
                logging.error(
                    "An error occurred for ticker '%s' with Polygon: %s", ticker, e
                )
                continue

        logging.info("Successfully processed data for %s stocks.", len(stock_data))
        return stock_data
