"""
Free, keyless web search for the Research agent.

Uses the `ddgs` package (DuckDuckGo metasearch). No API key, no signup,
no credit card -- it just works. Rate limits are unofficial/soft, so this
is meant for a handful of research lookups per run, not high-volume use.
"""

from ddgs import DDGS


def search(query: str, max_results: int = 5) -> str:
    """Run a web search and return a plain-text block of results
    (title / url / snippet) that's easy to hand to an LLM as context."""
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as e:
        return f"(web search failed for query '{query}': {e})"

    if not results:
        return f"(no web results found for query '{query}')"

    chunks = []
    for r in results:
        title = r.get("title", "").strip()
        href = r.get("href", "").strip()
        body = r.get("body", "").strip()
        chunks.append(f"- {title}\n  {href}\n  {body}")
    return "\n".join(chunks)


def search_many(queries: list[str], max_results_each: int = 4) -> str:
    """Run several searches and concatenate the results with headers,
    for feeding to the Research agent in one go."""
    blocks = []
    for q in queries:
        blocks.append(f"### Search: {q}\n{search(q, max_results=max_results_each)}")
    return "\n\n".join(blocks)
