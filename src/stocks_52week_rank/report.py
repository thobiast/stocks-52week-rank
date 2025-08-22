# -*- coding: utf-8 -*-
"""
Report generation utilities for presenting stock ranking data.
"""

import logging
import sys
from datetime import datetime

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

IMAGE_COLUMN_WIDTHS = [0.1, 0.2, 0.2, 0.2, 0.2, 0.2]


def create_image(df, filename):
    """
    Create and save the stock data table as an image.

    Parameters:
        df (pandas.DataFrame): The DataFrame to be converted to an image.
        filename (str): The name of the output image file.
    """
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
    for i, _width in enumerate(IMAGE_COLUMN_WIDTHS):
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
    logging.info("HTML file saved as %s", filename)


def save_dataframe_as_image(df, base_filename):
    """Save the DataFrame as an image file."""

    if plt is None:
        print("matplotlib is required for image output. Please install it.")
        sys.exit(1)

    filename = f"{base_filename}.png"
    create_image(df, filename)
    logging.info("Image file saved as %s", filename)
