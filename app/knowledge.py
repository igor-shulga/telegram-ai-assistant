"""
Knowledge base integration — reads from GitHub repo and Google Drive.
Uses keyword matching (no LLM) to select relevant files — saves API quota.
"""

import os
import logging
import httpx
import re

logger = logging.getLogger(__name__)


def google_enabled() -> bool:
    """Check if Google services are configured."""
    return bool(os.environ.get("GOOGLE_REFRESH_TOKEN"))

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


def get_drive_context(question: str) -> str:
    """Get relevant knowledge from Google Drive 'my-brain' folder.

    Uses keyword matching on file names to select relevant Drive files.
    Returns empty string if Google not configured or no matches found.
    """
    if not google_enabled():
        return ""

    try:
        from app.google_services import list_drive_files, read_drive_file

        files = list_drive_files(folder_name="my-brain")
        if not files:
            return ""

        q = question.lower()
        matched = []
        for f in files:
            name = f.get("name", "").lower().replace(".md", "").replace("-", " ").replace("_", " ")
            desc = f.get("description", "").lower() if f.get("description") else ""
            # Check if any word from the question appears in file name or description
            words = re.findall(r"\w{3,}", q)
            if any(w in name or w in desc for w in words):
                matched.append(f)

        if not matched:
            return ""

        # Read up to 3 matched files
        contents = []
        for f in matched[:3]:
            content = read_drive_file(f["id"])
            if content:
                contents.append(f"## Drive: {f['name']}\n\n{content}")
                logger.info("Loaded Drive KB file: %s", f["name"])

        return "\n\n---\n\n".join(contents)
    except Exception as e:
        logger.error("Drive KB error: %s", e)
        return ""


async def get_context(question: str, model=None) -> str:
    """Get relevant knowledge base context from GitHub and Google Drive.

    Combines both sources. model param kept for API compatibility but not used.
    """
    parts = []

    # GitHub KB
    files = select_files_by_keywords(question)
    if files:
        for filepath in files:
            content = await fetch_raw(filepath)
            if content:
                parts.append(f"## {filepath}\n\n{content}")
                logger.info("Loaded KB file: %s", filepath)

    # Google Drive KB
    drive_content = get_drive_context(question)
    if drive_content:
        parts.append(drive_content)
        logger.info("Drive KB context added (%d chars)", len(drive_content))

    return "\n\n---\n\n".join(parts)
