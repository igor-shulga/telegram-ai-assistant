"""
Knowledge base integration — reads from public GitHub repo.
Uses keyword matching (no LLM) to select relevant files — saves API quota.
"""

import logging
import httpx
import re

logger = logging.getLogger(__name__)

REPO_RAW = "https://raw.githubusercontent.com/igor-shulga/telegram-ai-knowledge/main"

# Map keywords to wiki files (no LLM needed for navigation)
KEYWORD_MAP = {
    "wiki/01-preparation.md":       ["підготовка", "preparation", "plan", "план", "agenda", "агенда", "цілі", "goals"],
    "wiki/02-opening.md":           ["відкриття", "opening", "старт", "start", "check-in", "знайомство"],
    "wiki/03-divergence.md":        ["дивергенція", "divergence", "brainstorm", "брейнсторм", "ідеї", "ideas", "генерація"],
    "wiki/04-emergence.md":         ["emergence", "групова динаміка", "group dynamics", "консенсус", "consensus"],
    "wiki/05-convergence.md":       ["конвергенція", "convergence", "рішення", "decision", "вибір", "choice", "пріоритет", "voting", "голосування", "dotmocracy"],
    "wiki/06-action-planning.md":   ["дії", "actions", "план дій", "action plan", "наступні кроки", "next steps"],
    "wiki/07-closing.md":           ["закриття", "closing", "завершення", "wrap", "підсумок", "summary"],
    "wiki/08-hybrid-remote.md":     ["онлайн", "online", "remote", "гібрид", "hybrid", "zoom", "miro", "mural", "virtual"],
    "wiki/09-retrospectives.md":    ["ретро", "retro", "retrospective", "ретроспектива", "sprint review"],
    "wiki/10-digital-tools.md":     ["інструменти", "tools", "miro", "mural", "mentimeter", "digital", "цифров"],
    "wiki/11-cultural-competency.md": ["культура", "culture", "різноманіття", "diversity", "крос-культур", "cross-cultural"],
    "wiki/12-facilitator-development.md": ["розвиток", "development", "навички фасилітатора", "facilitator skills", "коуч", "coach"],
    "wiki/13-quick-reference.md":   ["техніка", "technique", "метод", "method", "інструмент", "tool", "швидко", "quick", "reference"],
    "wiki/overview.md":             ["фасилітація", "facilitation", "що таке", "what is", "огляд", "overview"],
}


async def fetch_raw(path: str) -> str:
    url = f"{REPO_RAW}/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            return resp.text
        logger.warning("Could not fetch %s (status %d)", url, resp.status_code)
        return ""


def select_files_by_keywords(question: str) -> list[str]:
    """Select relevant wiki files using keyword matching — no LLM needed."""
    q = question.lower()
    scores = {}
    for filepath, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[filepath] = score

    # Return top 2 files by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    selected = [f for f, _ in ranked[:2]]
    logger.info("KB keyword match: %s", selected or "none")
    return selected


async def get_context(question: str, model=None) -> str:
    """
    Get relevant knowledge base context using keyword matching.
    model param kept for API compatibility but not used.
    """
    files = select_files_by_keywords(question)
    if not files:
        return ""

    contents = []
    for filepath in files:
        content = await fetch_raw(filepath)
        if content:
            contents.append(f"## {filepath}\n\n{content}")
            logger.info("Loaded KB file: %s", filepath)

    return "\n\n---\n\n".join(contents)
