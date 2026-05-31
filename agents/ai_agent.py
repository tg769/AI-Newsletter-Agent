import os
import feedparser
from datetime import datetime, timezone, timedelta
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# --- RSS Feed Sources ---
FEEDS = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "MIT News AI",
        "url": "https://news.mit.edu/rss/topic/artificial-intelligence2",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "Hacker News AI",
        # hnrss.org filters HN posts by keyword and minimum score — reduces noise significantly
        "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+machine+learning&points=40",
    },
    {
        "name": "r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/.rss",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
]

MAX_ARTICLES_PER_FEED = 5
USER_AGENT = "AI-Newsletter-Bot/1.0"


def fetch_ai_news() -> list[dict]:
    """
    Fetch AI news articles from RSS feeds published in the last 24 hours.
    Returns a list of dicts with title, url, source, and published fields.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    articles = []

    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], agent=USER_AGENT)

            count = 0
            for entry in feed.entries:
                if count >= MAX_ARTICLES_PER_FEED:
                    break

                # Parse published date if available
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass

                # Skip articles older than 24h when date is available
                if published and published < cutoff:
                    continue

                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()

                if not title or not url:
                    continue

                articles.append({
                    "title": title,
                    "url": url,
                    "source": feed_info["name"],
                    "published": published.strftime("%b %d, %H:%M UTC") if published else "Unknown",
                })
                count += 1

        except Exception as e:
            print(f"[ai_agent] Warning: could not fetch '{feed_info['name']}': {e}")

    return articles


def summarize_ai_news(articles: list[dict]) -> str:
    """
    Send fetched articles to Groq (Llama 3.3 70B) and return a structured
    morning briefing summary.
    """
    if not articles:
        return "No AI news articles found for today."

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Format article list for the prompt
    article_lines = []
    for i, a in enumerate(articles, 1):
        article_lines.append(f"{i}. [{a['source']}] {a['title']}\n   {a['url']}")
    articles_text = "\n".join(article_lines)

    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are an AI news analyst writing a morning briefing for an ML/AI engineer.

Today is {today}. Below are today's AI headlines pulled from multiple sources.

Your task:
1. Select the 5–8 most significant and distinct stories (skip near-duplicates, keep the most informative version)
2. Group them under relevant themes such as: Model Releases, Research Breakthroughs, Industry & Business, Policy & Regulation, Tools & Open Source
3. Write a 1–2 sentence summary per story — be specific and technical, this reader is an ML engineer who wants signal, not fluff
4. End with a single "Key Takeaway" sentence capturing the most important trend of the day

Output format (use exactly this structure):

## AI News — {today}

**[Theme]**
- **[Headline]**: [Summary]. ([Source])

**Key Takeaway:** [One sentence.]

---

Headlines:
{articles_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1400,
    )

    return response.choices[0].message.content


def run() -> str:
    """
    Main entry point for the AI News Agent.
    Fetches articles and returns a summarized briefing string.
    """
    print("[ai_agent] Fetching AI news from RSS feeds...")
    articles = fetch_ai_news()
    print(f"[ai_agent] Fetched {len(articles)} articles across {len(FEEDS)} feeds.")

    print("[ai_agent] Sending to Groq for summarization...")
    summary = summarize_ai_news(articles)
    print("[ai_agent] Done.")

    return summary


if __name__ == "__main__":
    print(run())
