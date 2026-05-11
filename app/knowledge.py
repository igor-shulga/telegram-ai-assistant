"""
Knowledge base integration — reads from public GitHub repo.
Uses two-phase navigation: README/index → select relevant files → load content.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

REPO_RAW = "https://raw.githubusercontent.com/igor-shulga/telegram-ai-knowledge/main"
WIKI_INDEX = f"{REPO_RAW}/wiki/index.md"
README = f"{REPO_RAW}/README.md"


async def fetch_raw(path: str) -> str:
    """Fetch raw file content from GitHub."""
    url = f"{REPO_RAW}/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            return resp.text
        logger.warning("Could not fetch %s (status %d)", url, resp.status_code)
        return ""


async def get_context(question: str, model) -> str:
    """
    Two-phase knowledge retrieval:
    1. Load wiki/index.md — Gemini selects relevant pages
    2. Load those pages — return combined content
    """
    index = await fetch_raw("wiki/index.md")
    if not index:
        return ""

    # Phase 1: ask model which files are relevant
    selection_prompt = f"""You are a knowledge base navigator.

Here is the index of available wiki pages:

{index}

User question: {question}

List the filenames (e.g. wiki/03-divergence.md) that are most relevant to answer this question.
Return ONLY a comma-separated list of filenames, nothing else. Maximum 3 files.
If nothing is relevant, return: none
"""
    response = model.generate_content(selection_prompt)
    selected = response.text.strip()
    logger.info("Knowledge navigator selected: %s", selected)

    if selected.lower() == "none" or not selected:
        return ""

    # Phase 2: load selected files
    files = [f.strip() for f in selected.split(",") if f.strip()]
    contents = []
    for filepath in files[:3]:
        content = await fetch_raw(filepath)
        if content:
            contents.append(f"## {filepath}\n\n{content}")
            logger.info("Loaded knowledge file: %s", filepath)

    return "\n\n---\n\n".join(contents)
