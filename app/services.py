from app.config import settings
import pygsheets
import pandas as pd
from pathlib import Path
from typing import Literal
from ast import literal_eval

FILE_PATH = Path(__file__).parent.parent.resolve()/"google_key.json"

def sheets_to_df(sheet_name: str, sheet_url: str) -> pd.DataFrame:
    """
    Get a Google sheet as a pandas dataframe
    """

    gc = pygsheets.authorize(service_account_file=FILE_PATH)
    sh = gc.open_by_url(sheet_url)
    wks = sh.worksheet_by_title(sheet_name)
    return wks.get_as_df()



# def get_highlights(df: pd.DataFrame, category=Literal["Finance", "Music", "Lifestyle", "Sports"], top_n=5):
#     """
#     Filters and retrieves the top news highlights for a specified category from a given DataFrame.
#
#     This function identifies and extracts the top `top_n` rows in terms of frequency for a
#     specific category from the supplied DataFrame. The resulting highlights are sorted
#     in descending order by frequency.
#
#     Args:
#         df (pd.DataFrame): The input DataFrame containing news articles with categories
#             and frequency information. It must include columns 'category' and 'Frequency'.
#         category (Literal["Finance", "Music", "Lifestyle", "Sports"]): The specific category
#             of news articles to filter from the DataFrame. Only articles matching this
#             category will be considered.
#         top_n (int): The number of top articles to retrieve based on frequency. Default is 5.
#
#     Returns:
#         pd.DataFrame: A DataFrame containing the top `top_n` news highlights for the
#         specified category, sorted by frequency in descending order.
#
#     Raises:
#         KeyError: If the provided DataFrame does not include the required 'category' or
#             'Frequency' columns.
#     """
#     if "category" not in df.columns or "num_articles" not in df.columns:
#         raise KeyError("DataFrame must include columns 'category' and 'num_articles'")
#
#     news = df[df['category'] == category].sort_values(by='Frequency', ascending=False, reset_index=True)
#
#     new_cols = {
#         "category": "Category",
#         "num_articles": "Frequency",
#         "keywords": "Keywords",
#         "title": "Title",
#         "Summary": "Summary"
#     }
#     news = news.rename(columns=new_cols)
#     return news.head(top_n)
