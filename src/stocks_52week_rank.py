#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to rank stocks based on their proximity to the 52-week low.

This script fetches historical stock data for a given list of tickers, calculates
some metrics, and ranks the stocks based on their proximity to the 52-week low.
The output can be displayed in different formats including text, HTML, or as an image.
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


@dataclass
class StockInfo:
    """Data class to hold stock information."""

    ticker: str
    current_price: float
    high_52_week: float
    low_52_week: float
    current_pct_from_low: float
    moving_average_200d: float


class StockDataProcessor:
    """
    A class to process and fetch stock data.

    Attributes:
    tickers (list of str): List of stock tickers to process.
    stock_data (list of StockInfo): List of processed stock data.
    """

    def __init__(self, tickers):
        """
        Initialize StockDataProcessor object.

        Parameters:
        tickers (list of str): List of stock tickers.
        """
        self.tickers = tickers
        self.stock_data = []

    def fetch_stock_data(self):
        """Fetch stock information for tickers and store in self.stock_data."""
        logging.info("Downloading stock data.")

        try:
            data = yf.download(self.tickers, period="1y")
        except Exception as e:
            print(f"Error downloading data: {e}")
            sys.exit(1)

        for ticker in self.tickers:
            ticker_data = data["Close"][ticker]
            current_price = ticker_data.iloc[-1]
            high_52_week = ticker_data.max()
            low_52_week = ticker_data.min()
            current_pct_from_low = ((current_price - low_52_week) / low_52_week) * 100
            moving_average_200d = ticker_data.rolling(window=200).mean().iloc[-1]

            clean_ticker = (
                ticker.replace(".SA", "") if ticker.endswith(".SA") else ticker
            )

            stock_info = StockInfo(
                ticker=clean_ticker,
                current_price=current_price,
                high_52_week=high_52_week,
                low_52_week=low_52_week,
                current_pct_from_low=current_pct_from_low,
                moving_average_200d=moving_average_200d,
            )
            self.stock_data.append(stock_info)

        logging.info(f"Successfully processed data for {len(self.stock_data)} stocks.")

    def sort_stock_data(self):
        """Sort stock data by the current percentage from the 52-week low in ascending order."""
        logging.info("Sorting stock data.")

        return sorted(self.stock_data, key=lambda x: x.current_pct_from_low)

    def create_dataframe(self, top):
        """
        Create and format a pandas DataFrame from stock data.

        Parameters:
        top (int): Number of top stocks to include in the DataFrame.

        Returns:
        pandas.DataFrame: Formatted DataFrame containing the top stock data.
        """
        logging.info("Creating dataframe from stock data.")

        sorted_stock_data = self.sort_stock_data()

        # Convert the list of StockInfo objects to a pandas DataFrame
        df = pd.DataFrame([stock.__dict__ for stock in sorted_stock_data])

        if df.empty:
            logging.info("Empty dataframe")
            return df

        # Format the float numbers to use 2 decimal places
        df = df.round(2)

        # Format 'current_pct_from_low' to one decimal place and add '%'
        df["current_pct_from_low"] = df["current_pct_from_low"].apply(
            lambda x: f"{x:.1f}%"
        )

        # Reset index to include index values
        df.reset_index(inplace=True)
        df.columns.values[0] = ""  # Remove the index column name

        # Filter and return the DataFrame to include only the top X stocks
        return df.head(top)


def parse_parameters():
    """Command line parser."""
    epilog = """
    Usage examples:
        %(prog)s
        %(prog)s --output image
        %(prog)s --top 10
        %(prog)s --top 10 --file ./my_stocks.txt --output image
    """
    parser = argparse.ArgumentParser(
        description="Rank stocks based on their proximity to the 52-week low.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", dest="debug", help="debug flag"
    )
    parser.add_argument(
        "--output",
        choices=["text", "image", "html"],
        default="text",
        help="""Choose the output format::
            'text' displays on screen,
            'image' saves as a file (.png),
            'html'  saves as a file (.html)""",
    )
    parser.add_argument(
        "--top", type=int, default=25, help="Number of stocks to display"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="File with the list of stock symbols. One per line.",
    )

    return parser.parse_args()


def configure_logging(debug_flag):
    """Configure logging based on the command line argument."""

    if debug_flag:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s %(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(level=logging.CRITICAL)


def read_tickers(file_path):
    """Read the list of tickers from a file, ignoring blank lines."""
    logging.info(f"Reading tickers from file {file_path}.")

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, "r") as file:
        tickers = [line.strip() for line in file.readlines() if line.strip()]

    logging.info(f"Read {len(tickers)} tickers from file {file_path}.")
    return tickers


def create_image(df, filename):
    """Create and save the stock data table as an image."""
    logging.info("Creating image from the dataframe.")

    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("tight")
    ax.axis("off")

    # Add extra space at the top for the title
    fig.subplots_adjust(top=1.7)

    plt.title(
        "Stocks ranked by their distance from the 52-week low",
        fontsize=10,
        weight="bold",
        y=1.05,
    )

    # Add subtitle with today's date
    today = datetime.today().strftime("%Y-%m-%d")
    plt.text(
        0.5, 1.75, f"Date: {today}", ha="center", fontsize=10, transform=fig.transFigure
    )

    # Create a table
    mpl_table = ax.table(
        cellText=df.values, colLabels=df.columns, cellLoc="center", loc="upper center"
    )
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(6)
    mpl_table.scale(1, 1)

    # Style the table
    for (i, j), cell in mpl_table.get_celld().items():
        if i == 0 or j == -1:
            cell.set_facecolor("#40466e")  # Dark background for header
            cell.set_text_props(weight="bold", color="w")
        elif i > 0 and i % 2 == 0:  # Apply alternate color for odd rows
            cell.set_facecolor("#f0f0f0")  # Light gray background

    # Adjust column widths
    col_widths = [0.1, 0.2, 0.2, 0.2, 0.2, 0.2]
    for i, _width in enumerate(col_widths):
        mpl_table.auto_set_column_width([i])

    # Save the table as an image
    plt.savefig(f"{filename}", bbox_inches="tight", dpi=300)
    plt.close()


def print_dataframe_as_text(df):
    """Print the DataFrame as text to the console."""

    print(df.to_string(index=False))


def save_dataframe_as_html(df, base_filename):
    """Save the DataFrame as an HTML file."""

    filename = f"{base_filename}.html"
    df.to_html(filename, index=False)
    logging.info(f"HTML file saved as {filename}")


def save_dataframe_as_image(df, base_filename):
    """Save the DataFrame as an image file."""

    filename = f"{base_filename}.png"
    create_image(df, filename)
    logging.info(f"Image file saved as {filename}")


def run(output, top, tickers_file, debug_flag):
    """
    Process stock data and generate output.

    This function reads the list of tickers from the specified file, validates the tickers,
    fetches stock information, ranks the stocks based on their proximity to the 52-week low,
    and generates the output in the specified format.

    Parameters:
    output (str): The output format ('text', 'image', 'html').
    top (int): The number of top stocks to display or save.
    tickers_file (str): Path to the file containing the list of tickers.
    debug_flag (bool): Flag to enable or disable debugging output.
    """

    configure_logging(debug_flag)

    tickers = read_tickers(tickers_file)
    if not tickers:
        print("Error: No tickers read from the file.")
        sys.exit(1)

    stocks = StockDataProcessor(tickers)
    stocks.fetch_stock_data()
    df = stocks.create_dataframe(top)

    today = datetime.today().strftime("%Y-%m-%d")
    base_filename = f"stocks_52w_low_{today}"

    if output == "text":
        print_dataframe_as_text(df)
    elif output == "html":
        save_dataframe_as_html(df, base_filename)
    else:
        save_dataframe_as_image(df, base_filename)


def main():
    """
    Main entry point for the stocks-52week-rank script.

    This function parses command-line arguments and calls the run function with the parsed arguments.
    """

    args = parse_parameters()
    run(args.output, args.top, args.file, args.debug)


##############################################################################
# Run from command line
##############################################################################
if __name__ == "__main__":
    main()

# vim: ts=4
