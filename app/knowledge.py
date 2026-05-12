"""
Knowledge base integration — reads from Google Drive 'my-brain' folder.
Uses keyword matching on file names to select relevant files.
"""

import os
import re
import logging

logger = logging.getLogger(__name__)


def google_enabled() -> bool:
    return bool(os.environ.get("GOOGLE_REFRESH_TOKEN"))


def get_drive_context(question: str) -> str:
    """Get relevant knowledge from Google Drive 'my-brain' folder."""
    if not google_enabled():
        return ""

    try:
        from app.google_services import list_drive_files, read_drive_file

        files = list_drive_files(folder_name="my-brain")
        if not files:
            logger.warning("No files found in Drive 'my-brain' folder")
            return ""

        q = question.lower()
        matched = []
        for f in files:
            name = f.get("name", "").lower().replace(".md", "").replace("-", " ").replace("_", " ")
            desc = f.get("description", "").lower() if f.get("description") else ""
            words = re.findall(r"\w{3,}", q)
            if any(w in name or w in desc for w in words):
                matched.append(f)

        if not matched:
            return ""

        contents = []
        for f in matched[:3]:
            content = read_drive_file(f["id"])
            if content:
                contents.append(f"## {f['name']}\n\n{content}")
                logger.info("Loaded Drive KB file: %s", f["name"])

        return "\n\n---\n\n".join(contents)
    except Exception as e:
        logger.error("Drive KB error: %s", e)
        return ""


async def get_context(question: str, model=None) -> str:
    """Get relevant knowledge base context from Google Drive."""
    context = get_drive_context(question)
    if context:
        logger.info("Drive KB context loaded (%d chars)", len(context))
    return context
