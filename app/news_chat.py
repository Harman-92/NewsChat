from typing import Optional, Dict, Any, List
from datetime import datetime
from weaviate.classes.query import Filter, MetadataQuery, QueryReference
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from langsmith import traceable
import weaviate
from openai import OpenAI

# Initialise OpenAI client
oa_client = OpenAI()

def get_embedding(text: str, model="text-embedding-3-small") -> list[float]:
    text = text.replace("\n", " ")
    return oa_client.embeddings.create(input = [text], model=model).data[0].embedding


def _and(a: Optional[Filter], b: Optional[Filter]) -> Filter:
    """Combine Weaviate filters."""
    return b if a is None else (a & b)


def _to_rfc3339_start(s: str) -> str:
    s = (s or "").strip()
    # if already RFC3339
    if "T" in s:
        return s
    return f"{s}T00:00:00Z"


def _to_rfc3339_end(s: str) -> str:
    s = (s or "").strip()
    # if already RFC3339
    if "T" in s:
        return s
    return f"{s}T23:59:59Z"


class NewsChat:
    """
    A comprehensive utility for interacting with a news database to facilitate searching and answering queries in natural language.
    """
    SYSTEM_PROMPT = f"""
You are a helpful news assistant that answers users query by exploring news database for Finance, Music, Lifestyle and Sports categories.
Today is {datetime.now().strftime("%A, %B %-d, %Y")}.
Database:
- Cluster collection fields: cluster_id, title, summary, category, num_articles, keywords
- Article collection fields: url, author, title, published, summary, category
- Cross-reference: Article.cluster -> Cluster

Important:
- Clusters do NOT have dates. Do NOT apply date filtering to clusters.
- Date filtering (start_date/end_date) applies ONLY to articles via Article.published.

Tools:
- Use search_clusters for topics, highlights, news, stories(ranked by num_articles from tool results if needed).
- Use search_articles for article search, author search, sources, time ranges, or listing articles within a cluster (use cluster_id).
- If user asks for "articles in a cluster", do:
  1) search_clusters(query=..., category=..., limit=...) to find the cluster_id
  2) search_articles(cluster_id=..., ...) to list articles

Filtering:
- Category must be one of: Sports, Lifestyle, Music, Finance (use exact casing).
- If user specifies a time range (e.g., "last 7 days", "since Jan 10", "today"), pass start_date/end_date to search_articles.
- If the user does NOT specify keywords, you may call tools with query="" and rely on filters.


Examples:
1) News:
User: "Are there any stories related to technology?"
Tool: search_clusters(query="technology", limit=5)

2) Articles by author:
User: "What has Jane Doe written?"
Tool: search_articles(query="Jane Doe", limit=50)

3) Articles in a cluster:
User: "Show me articles from the AI cluster"
Tool: search_articles(cluster_id="<cluster_id>", limit=10)

4) Category filtering:
User: "Give me top stories about finance"
Tool: search_clusters(query="", category="Finance", limit=10)

5) Date filtering on articles only:
User: "Sports articles from the last 7 days about Novak Djokovic"
Tool: search_articles(query="Novak Djokovic", category="Sports", start_date="2026-01-18", end_date="2026-01-25", limit=10)

Response style:
- Be concise and data-driven. If needed, summarise the response and only output what is relevant.
- Keep your tone formal.
- Never invent fields, counts, dates, authors, or URLs.
- If no results, say so.
"""

    def __init__(
            self,
            weaviate_client: weaviate.WeaviateClient,
            model: str = "openai/gpt-4o",
            app_name: str = "news_chat",
    ):
        self.client = weaviate_client
        self.app_name = app_name

        self.model = LiteLlm(model=model)
        self.session_service = InMemorySessionService()

        # Tools
        self.cluster_tool = FunctionTool(func=self.search_clusters)
        self.article_tool = FunctionTool(func=self.search_articles)

        self.agent = Agent(
            name="news_agent",
            model=self.model,
            instruction=self.SYSTEM_PROMPT,
            tools=[self.cluster_tool, self.article_tool],
        )

        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

    # ---------- Session ----------
    # @traceable(name="create_session")
    def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        session = self.session_service.create_session_sync(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
            state={"app:weaviate_client": self.client},
        )
        return session.id

    # ---------- Tool: Clusters ----------
    # @traceable(name="tool.search_clusters")
    def search_clusters(
        self,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 5,
        tool_context: Optional[ToolContext] = None,
    ) -> Dict[str, Any]:
        """
        Search News/Highlights/Story Cluster objects.
        - No date filtering here (clusters have no dates).
        """
        if tool_context is None:
            raise ValueError("tool_context is required")

        client: weaviate.WeaviateClient = tool_context.state["app:weaviate_client"]
        col = client.collections.get("Cluster")

        # Basic query validation
        q = (query or "").strip()

        # Capping it incase the model suggests a very high limit
        limit = max(limit, 50)

        f: Optional[Filter] = None
        if category:
            f = _and(f, Filter.by_property("category").equal(category))

        if q:
            res = col.query.hybrid(
                query=q,
                vector=get_embedding(q),
                alpha=0.7,
                limit=limit,
                filters=f,
                return_metadata=MetadataQuery(score=True),
            )
        else:
            res = col.query.fetch_objects(
                limit=limit,
                filters=f,
                return_metadata=MetadataQuery(score=True),
            )

        out: List[Dict[str, Any]] = []
        for o in res.objects:
            p = o.properties or {}
            out.append(
                {
                    "cluster_id": p.get("cluster_id"),
                    "title": p.get("title"),
                    "summary": p.get("summary"),
                    "category": p.get("category"),
                    "num_articles": p.get("num_articles"),
                    "keywords": p.get("keywords"),
                    "score": getattr(o.metadata, "score", None),
                }
            )

        # # Save context for follow-up queries
        # tool_context.state["last_clusters"] = out[:10]

        return {"count": len(out), "results": out}



    # ---------- Tool: Articles ----------
    # @traceable(name="tool.search_articles")
    def search_articles(
        self,
        query: str = "",
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        cluster_id: Optional[str] = None,
        tool_context: Optional[ToolContext] = None,
    ) -> dict[str, Any]:
        """
        Search Article objects.
        - Supports date filtering via Article.published
        - Supports category filtering via Article.category
        - Supports cluster filtering via reference Article.cluster -> Cluster.cluster_id
        - Empty query uses fetch_objects to avoid hybrid/vector issues
        """
        if tool_context is None:
            raise ValueError("tool_context is required")

        client: weaviate.WeaviateClient = tool_context.state["app:weaviate_client"]
        col = client.collections.get("Article")

        # Basic query validation
        q = (query or "").strip()

        # Capping it incase the model suggests a very high limit
        limit = max(limit, 50)

        f: Optional[Filter] = None

        if category:
            f = _and(f, Filter.by_property("category").equal(category))

        if start_date:
            f = _and(f, Filter.by_property("published").greater_or_equal(_to_rfc3339_start(start_date)))
        if end_date:
            f = _and(f, Filter.by_property("published").less_or_equal(_to_rfc3339_end(end_date)))

        if cluster_id:
            f = _and(f, Filter.by_ref("cluster").by_property("cluster_id").equal(cluster_id))

        # Query references so article results include the linked cluster metadata
        refs = [
            QueryReference(
                link_on="cluster",
                return_properties=["cluster_id", "title", "category", "summary", "num_articles", "keywords"],
            )
        ]

        if q:
            res = col.query.hybrid(
                query=q,
                vector=get_embedding(q),
                alpha=0.6,
                limit=limit,
                filters=f,
                return_references=refs,
                return_metadata=MetadataQuery(score=True),
            )
        else:
            res = col.query.fetch_objects(
                limit=limit,
                filters=f,
                return_references=refs,
                return_metadata=MetadataQuery(score=True),
            )

        out = []
        for o in res.objects:
            p = o.properties or {}

            # Extract referenced cluster (handles common response shapes)
            cluster_ref = None
            refs_obj = getattr(o, "references", None) or {}
            cluster_objs = None

            if "cluster" in refs_obj and hasattr(refs_obj["cluster"], "objects"):
                cluster_objs = refs_obj["cluster"].objects
            elif isinstance(refs_obj.get("cluster"), dict):
                cluster_objs = refs_obj["cluster"].get("objects")

            if cluster_objs:
                cluster_ref = (cluster_objs[0].properties or {})

            out.append(
                {
                    "url": p.get("url"),
                    "title": p.get("title"),
                    "author": p.get("author"),
                    "published": p.get("published"),
                    "summary": p.get("summary"),
                    "category": p.get("category"),
                    "source": p.get("source"),
                    "cluster": cluster_ref,
                    "score": getattr(o.metadata, "score", None),
                }
            )
        # # For follow-up queries, save the last 10 articles
        # tool_context.state["last_articles"] = out[:10]

        return {"count": len(out), "results": out}

    # ---------- Query ----------
    @traceable(name="query_agent")
    def query(self, user_id: str, session_id: str, message: str) -> str:
        content = types.Content(role="user", parts=[types.Part(text=message)])

        response_text = ""
        for event in self.runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = "".join([p.text or "" for p in event.content.parts]).strip()


        return response_text or "No response generated."

    def close(self):
        if self.client:
            self.client.close()