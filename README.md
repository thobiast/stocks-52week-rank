# Stocks 52-Week Low Ranker

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


This script ranks stocks based on their proximity to the 52-week low. It fetches historical stock data for a given list of tickers, calculates some metrics, and ranks the stocks. The output can be displayed in different formats including text, HTML, or as an image.

## Features

- Fetches historical stock data for a list of tickers.
- Calculates key metrics including 52-week high, 52-week low, percentage from 52-week low, and 200-day moving average.
- Ranks stocks based on their proximity to the 52-week low.
- Outputs the ranked data in text, HTML, or image format.

## Requirements

- `yfinance` library
- `pandas` library
- `matplotlib` library

## Ticker File

Create a text file (e.g., stocks.txt) containing the list of stock tickers, one ticker per line:

```bash
$ cat stocks.txt
AAPL
MSFT
GOOGL
AMZN
TSLA

# Example for Brazil stocks
$ cat brazil_stocks.txt
BBAS3.SA
EGIE3.SA
ITSA4.SA
PETR4.SA
VALE3.SA
WEGE3.SA
```

## Usage:

```bash
$ stocks-52week-rank --help
usage: stocks-52week-rank [-h] [-d] [--output {text,image,html}] [--top TOP] --file FILE

Rank stocks based on their proximity to the 52-week low.

options:
  -h, --help            show this help message and exit
  -d, --debug           debug flag
  --output {text,image,html}
                        Choose the output format::
                                    'text' displays on screen,
                                    'image' saves as a file (.png),
                                    'html'  saves as a file (.html)
  --top TOP             Number of stocks to display
  --file FILE           File with the list of stock symbols. One per line.

    Usage examples:
        stocks-52week-rank
        stocks-52week-rank --output image
        stocks-52week-rank --top 10
        stocks-52week-rank --top 10 --file ./my_stocks.txt --output image



$ stocks-52week-rank --file ./brazil_stocks.txt --top 10
  ticker  current_price  high_52_week  low_52_week current_pct_from_low  moving_average_200d
0  BBDC4          12.36         17.55        12.36                 0.0%                14.62
1 TAEE11          33.23         38.38        33.23                 0.0%                35.56
2  TAEE4          11.12         12.86        11.12                 0.0%                11.90
3  GGBR4          16.87         24.38        16.85                 0.1%                18.79
4  FLRY3          13.94         18.58        13.87                 0.5%                15.68
5  ABEV3          11.23         15.55        11.09                 1.3%                12.93
6  SLCE3          17.49         22.45        17.23                 1.5%                18.93
7  CSAN3          12.50         20.49        12.31                 1.5%                16.67
8  VALE3          60.68         77.90        59.71                 1.6%                67.09
9  DXCO3           6.58          9.51         6.46                 1.9%                 7.55

```


## Installation

Clone or download the repository to your local machine.

### Install in development mode using pip
```bash
$ pip install -e .
```

### Install in development mode using pipx
```bash
$ pipx install -e .
```
