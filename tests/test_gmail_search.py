"""Tests for Feature 2: Gmail search via natural language."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.google_services import extract_gmail_query
from app.bot import detect_intent


# ─── Intent Detection ────────────────────────────────────────────────────────

class TestGmailSearchIntent:
    """detect_intent should return 'email_search' for search keywords."""

    def test_detect_email_search_ua_знайди(self):
        assert detect_intent("Знайди листи від Іванова") == "email_search"

    def test_detect_email_search_ua_пошук(self):
        assert detect_intent("Пошук листів про проект") == "email_search"

    def test_detect_email_search_en_search(self):
        assert detect_intent("Search emails about project") == "email_search"

    def test_detect_email_search_en_find(self):
        assert detect_intent("Find emails from John") == "email_search"

    def test_detect_email_search_ua_покажи_листи_від(self):
        assert detect_intent("Покажи листи від Петрова") == "email_search"

    def test_regular_email_intent_unchanged(self):
        """Non-search email queries should still return 'email'."""
        assert detect_intent("Покажи непрочитані листи") == "email"

    def test_покажи_листи_за_тиждень_is_search(self):
        assert detect_intent("Покажи листи за тиждень") == "email_search"


# ─── Gmail Query Extraction ─────────────────────────────────────────────────

class TestExtractGmailQuery:
    """extract_gmail_query should use Gemini to convert natural language to Gmail query."""

    @pytest.mark.asyncio
    async def test_extract_from_sender(self):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "from:Іванова"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await extract_gmail_query("Знайди листи від Іванова", mock_model)
        assert result == "from:Іванова"

    @pytest.mark.asyncio
    async def test_extract_time_based(self):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "newer_than:7d"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await extract_gmail_query("Покажи листи за тиждень", mock_model)
        assert result == "newer_than:7d"

    @pytest.mark.asyncio
    async def test_extract_subject(self):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "subject:проект"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await extract_gmail_query("Покажи листи про проект", mock_model)
        assert result == "subject:проект"

    @pytest.mark.asyncio
    async def test_strips_whitespace(self):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "  from:test@example.com  \n"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await extract_gmail_query("Find emails from test", mock_model)
        assert result == "from:test@example.com"

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("fail"))

        result = await extract_gmail_query("Search something", mock_model)
        assert result == ""
