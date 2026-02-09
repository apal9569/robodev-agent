from datetime import date
from typing import List
from robodev.daily_digest.feed_parser import Article, fetch_feeds, save_digest, load_digest
from robodev.daily_digest.send_mail import send_digest_email
import json
import re

FILTER_PROMPT_TEMPLATE = """You are a robotics news curator for an engineer with this profile:
- Stack: {stack}
- Robot type: {robot_type}
- Interests: {interests}

Here are today's articles (title | source | abstract):
{article_block}

Tasks:
1. Score each article 0-10 for relevance to the engineer's profile.
2. Pick the TOP 10 most relevant.
3. For each, write a paragraph of actionable summary (what's new, why it matters, link to paper/code if mentioned).
4. Group into categories: 🔬 Research, 🛠 Tools/Libraries, 📰 Industry News, 💡 Tutorials

Output JSON:
{{
  "date": "{today}",
  "highlights": [
    {{
      "title": "...",
      "url": "...",
      "category": "...",
      "relevance": N,
      "summary": "..."
    }}
  ],
  "one_liner": "One sentence TL;DR of today's most important development"
}}
"""


def build_digest(llm, memory, force: bool = False, email: bool = False) -> str:
    today = date.today().isoformat()

    # Check cache
    if not force:
        cached = load_digest(today)
        if cached:
            result = _format_digest(cached)
            if email:
                _send_email(today, result)
            return result

    # Fetch
    articles = fetch_feeds()
    if not articles:
        return "No articles fetched today."

    # Limit to 20 articles max and truncate summaries
    articles = articles[:20]
    article_block = "\n".join(
        f"- {a.title.strip()} | {a.source.strip()} | {a.summary[:100].strip()}"
        for a in articles
        if a.title.strip()
    )

    m = memory.data
    prompt = FILTER_PROMPT_TEMPLATE.format(
        stack=m.get("stack", "ROS2"),
        robot_type=m.get("robot_type", "general"),
        interests="motion planning, control, perception, SLAM, manipulation, sim-to-real, Simulation",
        article_block=article_block,
        today=today,
    )

    print(f"📡 Fetched {len(articles)} articles, prompt size: {len(prompt)} chars")

    try:
        raw = llm.chat(prompt, timeout=300, task="digest")
    except Exception as e:
        result = f"❌ LLM call failed: {e}"
        if email:
            _send_email(today, result)
        return result

    try:
        # Extract JSON from response (LLM sometimes wraps it in markdown)
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            digest = json.loads(json_match.group())
        else:
            digest = json.loads(raw)
        save_digest(today, digest)
        result = _format_digest(digest)
    except (json.JSONDecodeError, AttributeError):
        result = raw

    if email:
        _send_email(today, result)

    return result

def _send_email(today: str, body: str):
    print(f"📧 Attempting to send email... (body length: {len(body)} chars)")
    try:
        send_digest_email(
            subject=f"🤖 RoboDev Daily Digest — {today}",
            body_markdown=body,
        )
    except FileNotFoundError as e:
        print(f"⚠ Mail config missing: {e}")
    except Exception as e:
        print(f"❌ Email failed: {type(e).__name__}: {e}")


def _format_digest(digest: dict) -> str:
    lines = [
        f"# 🤖 RoboDev Daily Digest — {digest.get('date', 'today')}",
        f"\n> {digest.get('one_liner', '')}",
        "",
    ]

    # Group by category, assign default if empty
    categories = {}
    for h in digest.get("highlights", []):
        cat = h.get("category", "").strip()
        if not cat:
            # Auto-assign based on relevance or default
            cat = "📰 Industry News"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(h)

    # Sort categories in preferred order
    cat_order = ["🔬 Research", "🛠 Tools/Libraries", "📰 Industry News", "💡 Tutorials"]
    sorted_cats = sorted(
        categories.keys(),
        key=lambda c: cat_order.index(c) if c in cat_order else 99
    )

    for cat in sorted_cats:
        lines.append(f"\n## {cat}\n")
        for h in categories[cat]:
            title = h.get("title", "Untitled")
            url = h.get("url", "")
            relevance = h.get("relevance", "?")
            summary = h.get("summary", "")

            if url:
                lines.append(f"### [{title}]({url})")
            else:
                lines.append(f"### {title}")
            lines.append(f"**Relevance: {relevance}/10**")
            lines.append(f"{summary}")
            lines.append("")

    lines.append("---")
    lines.append(f"_Total articles reviewed: {len(digest.get('highlights', []))}_")
    return "\n".join(lines)