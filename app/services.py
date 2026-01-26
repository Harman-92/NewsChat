from app.config import settings
import pygsheets
import pandas as pd
from pathlib import Path
import weaviate
from weaviate.classes.init import Auth


FILE_PATH = Path(__file__).parent.parent.resolve()/"google_key.json"

def sheets_to_df(sheet_name: str, sheet_url: str) -> pd.DataFrame:
    """
    Get a Google sheet as a pandas dataframe
    """

    gc = pygsheets.authorize(service_account_file=FILE_PATH)
    sh = gc.open_by_url(sheet_url)
    wks = sh.worksheet_by_title(sheet_name)
    return wks.get_as_df()

def make_weaviate_client():
    # Load Weaviate credentials from environment variables
    weaviate_url = settings.WEAVIATE_URL
    weaviate_api_key = settings.WEAVIATE_API_KEY

    # Connect to Weaviate Cloud
    w_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )
    return w_client