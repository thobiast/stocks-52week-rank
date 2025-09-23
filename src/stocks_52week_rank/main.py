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
from datetime import datetime

import pandas as pd

from .providers import PolygonDataProvider, YFinanceDataProvider
from .report import (
    print_dataframe_as_text,
    save_dataframe_as_html,
    save_dataframe_as_image,
)


def parse_parameters():
    """Command line parser."""
    epilog = """
    Usage examples:
        %(prog)s
        %(prog)s --file ./my_stocks.txt
        %(prog)s --file ./my_stocks.txt --top 10
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
        "--source",
        choices=["yfinance", "polygon"],
        default="yfinance",
        help="Choose the data source for stock data. Choices: %(choices)s. (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "image", "html"],
        default="text",
        help="""Choose the output format::
            'text' displays on screen,
            'image' saves as a file (.png),
            'html'  saves as a file (.html)
            (default: %(default)s)""",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Number of stocks to display. (default: %(default)s)",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="File with the list of stock symbols. One per line.",
    )

    return parser.parse_args()


def configure_logging(debug_flag):
    """
    Configure logging based on the debug flag.

    Parameters:
        debug_flag (bool): If True, sets logging level to INFO; otherwise, CRITICAL.
    """

    if debug_flag:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s %(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(level=logging.CRITICAL)


def read_tickers(file_path):
    """
    Read the list of tickers from a file, ignoring blank lines.

    Parameters:
        file_path (str): The path to the file containing tickers.

    Returns:
        list of str: A list of stock tickers.
    """
    logging.info("Reading tickers from file %s", file_path)

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as file:
        tickers = [line.strip() for line in file.readlines() if line.strip()]

    logging.info("Read %s tickers from file %s", len(tickers), file_path)
    return tickers


def create_dataframe(stock_data, top):
    """
    Create and format a pandas DataFrame ranked by proximity to the 52-week low.

    Parameters:
        stock_data (dict[str, StockInfo]): A dictionary of StockInfo objects with the
            ticker as the key.
        top         (int): Number of top-ranked DataFrame rows to return.

    Returns:
        pandas.DataFrame: Formatted DataFrame containing the top stock data.
            First column is "Rank" (1-based).
    """
    logging.info("Creating and sorting dataframe from stock data.")

    # Sort stock data by the current percentage from the 52-week low in asc order
    sorted_stock = sorted(stock_data.values(), key=lambda x: x.current_pct_from_low)

    # Convert the list of StockInfo objects to a pandas DataFrame
    df = pd.DataFrame([stock.__dict__ for stock in sorted_stock])
    if df.empty:
        logging.info("Empty dataframe")
        return df

    # Format the float numbers to use 2 decimal places
    df = df.round(2)

    # Format 'current_pct_from_low' to one decimal place and add '%'
    df["current_pct_from_low"] = df["current_pct_from_low"].apply(lambda x: f"{x:.1f}%")

    # Make index start at 1 and change index name
    df.index = df.index + 1
    df.index.name = "Rank"
    # Reset index to include index values
    df.reset_index(inplace=True)

    # Filter and return the DataFrame to include only the top X stocks
    return df.head(top)


def run(output, top, tickers_file, debug_flag, source):
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
        source (str): The data source to use ('yfinance' or 'polygon').
    """

    configure_logging(debug_flag)

    tickers = read_tickers(tickers_file)
    if not tickers:
        print("Error: No tickers read from the file.")
        sys.exit(1)

    if source == "polygon":
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            print("Error: POLYGON_API_KEY environment variable not set.")
            sys.exit(1)
        data_provider = PolygonDataProvider(api_key)
    else:
        data_provider = YFinanceDataProvider()

    stock_data = data_provider.fetch_stock_data(tickers)
    df = create_dataframe(stock_data, top)

    if df.empty:
        print("No data could be processed. Please check the tickers or debug logs.")
        return

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

    This function parses command-line arguments and calls the run function.
    """

    args = parse_parameters()
    run(args.output, args.top, args.file, args.debug, args.source)


##############################################################################
# Run from command line
##############################################################################
if __name__ == "__main__":
    main()

# vim: ts=4
