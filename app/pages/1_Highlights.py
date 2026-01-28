import streamlit as st
import pandas as pd
from ast import literal_eval
from datetime import date, timedelta

from app.config import settings
from app.services import sheets_to_df
from app.utils import render_sidebar

st.set_page_config(page_title="News Highlights", layout="wide")
st.title("News Highlights")
render_sidebar()


# Page Filters
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    category = st.selectbox("Category", ["All", "Music", "Finance", "Lifestyle", "Sports"], index=0)

with col2:
    today = date.today()
    default_start = today - timedelta(days=14)
    start_date, end_date = st.date_input(
        "Date range",
        value=(default_start, today),
    )

with col3:
    # Sort control
    sort_mode = st.selectbox("Sort highlights by", ["Frequency", "Recency"], index=0)
    #top_n = st.number_input("Top highlights", min_value=5, max_value=50, value=15, step=5)

st.divider()

# Styling
st.markdown(
    """
    <style>
      .card {
        border: 1px solid rgba(255,255,255,0.14);
        padding: 14px;
        border-radius: 10px;               /* <- more square */
        margin-bottom: 12px;
        background: rgba(255,255,255,0.06);/* <- visible in dark theme */
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        transition: all 120ms ease-in-out;
      }
      .card:hover{
        border-color: rgba(255,255,255,0.30);
        background: rgba(255,255,255,0.09);
        transform: translateY(-1px);
      }

      .card-title {
        font-weight: 750;
        font-size: 1.02rem;
        margin-bottom: 6px;
        line-height: 1.25;
        color: rgba(255,255,255,0.92);
      }

      .meta {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 10px;
      }

      .badge {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.14);
        color: rgba(255,255,255,0.85);
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 0.8rem;
      }

      .muted {
        color: rgba(255,255,255,0.62);
        font-size: 0.85rem;
      }

      .summary {
        margin-bottom: 10px;
        color: rgba(255,255,255,0.82);
      }

      .chips { display: flex; gap: 6px; flex-wrap: wrap; }

      .chip {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        color: rgba(255,255,255,0.78);
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.78rem;
      }
    </style>
    
    """,
    unsafe_allow_html=True,
)

# Special CSS for buttons
st.markdown(
    """
    <style>
    /* Make Streamlit buttons shorter (height) */
    div[data-testid="stButton"] > button {
        padding-top: 0.20rem !important;
        padding-bottom: 0.20rem !important;
        min-height: 1.75rem !important;
        height: 1.75rem !important;
        line-height: 1.1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Load data from Google Sheets
@st.cache_data(ttl=600)
def load_clusters(sheet_url: str) -> pd.DataFrame:
    df = sheets_to_df(sheet_name="clusters_db", sheet_url=sheet_url)

    if "keywords" in df.columns:
        df["keywords"] = df["keywords"].apply(literal_eval)

    if "embedding" in df.columns:
        df = df.drop(columns=["embedding"])

    return df


@st.cache_data(ttl=600)
def load_articles(sheet_url: str) -> pd.DataFrame:
    df = sheets_to_df(sheet_name="articles_db", sheet_url=sheet_url)

    if "published" in df.columns:
        df["published"] = pd.to_datetime(df["published"], errors="coerce", utc=True)

    if "embedding" in df.columns:
        df = df.drop(columns=["embedding"])

    return df


clusters_df = load_clusters(settings.SHEET_URL)
articles_df = load_articles(settings.SHEET_URL)


# Highlights computation
def compute_highlights(
        clusters_df: pd.DataFrame,
        articles_df: pd.DataFrame,
        category: str,
        start_date: date,
        end_date: date,
        top_n: int = 20,
) -> pd.DataFrame:
    a = articles_df.copy()

    # Filter category
    if category != "All" and "category" in a.columns:
        a = a[a["category"] == category]

    # Filter date range (articles only)
    if "published" in a.columns:
        mask = (a["published"].dt.date >= start_date) & (a["published"].dt.date <= end_date)
        a = a[mask]

    if a.empty or "cluster_id" not in a.columns:
        return pd.DataFrame()

    # Ensure source column
    if "source" not in a.columns:
        a["source"] = ""

    # Run a few aggregations for cluster metadata
    agg = (
        a.groupby("cluster_id", dropna=False)
        .agg(
            frequency=("cluster_id", "size"), # could have reused num_articles
            unique_sources=("source", pd.Series.nunique),
            last_published=("published", "max"),
        )
        .reset_index()
    )

    # Join cluster metadata
    if "cluster_id" in clusters_df.columns:
        out = agg.merge(clusters_df, on="cluster_id", how="left")
    else:
        out = agg

    # Sort values
    out = out.sort_values(["frequency", "last_published"], ascending=[False, False]).head(int(top_n))
    return out


highlights = compute_highlights(clusters_df, articles_df, category, start_date, end_date)


# Render UI
def _chips(items, max_n=10):
    items = [str(x) for x in (items or []) if str(x).strip()]
    items = items[:max_n]
    if not items:
        return ""
    return " ".join([f"<span class='chip'>{x}</span>" for x in items])

def _format_date(x, time=False) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    try:
        if time:
            return pd.to_datetime(x, utc=True).strftime("%Y-%m-%d")
        else:
            return pd.to_datetime(x, utc=True).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(x)

def render_cluster_tile(row: pd.Series, idx: int):
    cid = row.get("cluster_id")
    title = row.get("title") or "(untitled cluster)"

    summary = (row.get("summary") or "").strip()
    summary_snip = (summary[:220] + "…") if len(summary) > 220 else summary

    freq = int(row.get("frequency") or 0)
    srcs = int(row.get("unique_sources") or 0)
    last_pub_str = _format_date(row.get("last_published"))

    kw_html = _chips(row.get("keywords") or [], max_n=12)

    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">{title}</div>
          <div class="meta">
            <span class="badge">{freq} articles</span>
            <span class="badge">{srcs} sources</span>
            {f'<span class="muted">Last: {last_pub_str}</span>' if last_pub_str else ''}
          </div>
          <div class="summary">{summary_snip if summary_snip else "<span class='muted'>No summary available.</span>"}</div>
          <div class="chips">{kw_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("View articles", key=f"view_{cid}", use_container_width=True):
        st.session_state.selected_cluster_id = cid
        st.session_state.selected_cluster_title = title
        st.rerun()


if highlights.empty:
    st.info("No highlights found for the selected filters.")
    st.stop()


if sort_mode == "Recency":
    highlights = highlights.sort_values(["last_published", "frequency"], ascending=[False, False])
else:
    highlights = highlights.sort_values(["frequency", "last_published"], ascending=[False, False])


# Track filter changes to reset selected cluster
filters_sig = (category, start_date, end_date, sort_mode)

if st.session_state.get("filters_sig") != filters_sig:
    st.session_state.filters_sig = filters_sig
    st.session_state.selected_cluster_id = None
    st.session_state.selected_cluster_title = None

# Ensure keys exist (only initialize once)
if "selected_cluster_id" not in st.session_state:
    st.session_state.selected_cluster_id = None
    st.session_state.selected_cluster_title = None

# If a cluster is selected but no longer exists in current highlights, go back to "All clusters"
valid_ids = set(highlights["cluster_id"].dropna().astype(str).tolist()) if not highlights.empty else set()
cur = st.session_state.get("selected_cluster_id")

if cur is not None and str(cur) not in valid_ids:
    st.session_state.selected_cluster_id = None
    st.session_state.selected_cluster_title = None

# Layout: left = highlights, right = articles
left, right = st.columns([4, 6])


with left:
    st.subheader("Top Highlights")
    st.caption("Click **View articles** to open details on the right.")

    for i, (_, row) in enumerate(highlights.iterrows()):
        render_cluster_tile(row, i)

with right:
    st.subheader("Articles")
    selected_cid = st.session_state.get("selected_cluster_id")
    selected_title = st.session_state.get("selected_cluster_title")

    if selected_cid:
        c1, c2 = st.columns([4, 1], vertical_alignment="top")

        with c1:
            st.caption(f"Showing articles for selected cluster: **{selected_title}**")

        with c2:
            if st.button("Show all", use_container_width=True):
                st.session_state.selected_cluster_id = None
                st.session_state.selected_cluster_title = None
                st.rerun()
    else:
        st.caption("Showing articles across all clusters in current results")

    highlight_cluster_ids = (
        highlights["cluster_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    if not highlight_cluster_ids:
        st.info("No clusters in current results.")
        st.stop()

    # --- Choose articles scope ---
    if selected_cid:
        # Articles in selected cluster only
        members = articles_df[articles_df["cluster_id"].astype(str) == str(selected_cid)].copy()
    else:
        # Articles in all highlighted clusters (filtered)
        members = articles_df[articles_df["cluster_id"].astype(str).isin(highlight_cluster_ids)].copy()

    # Date filter only (category already applied via highlights; don't double-filter)
    if "published" in members.columns:
        mask = (members["published"].dt.date >= start_date) & (members["published"].dt.date <= end_date)
        members = members[mask].sort_values("published", ascending=False)

    # Reset index and format dates
    members = members.reset_index(drop=True)
    members["published"] = members["published"].apply(lambda x: _format_date(x, time=True))
    cols = [c for c in ["published", "title", "source", "author", "url"] if c in members.columns]
    st.dataframe(members[cols], use_container_width=True, height=780)
