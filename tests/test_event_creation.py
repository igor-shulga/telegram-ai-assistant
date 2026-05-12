"""Tests for Feature 1: Calendar event creation via natural language."""

import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date

import pytest

from app.google_services import parse_event_from_text
from app.bot import detect_intent


# ─── Intent Detection ────────────────────────────────────────────────────────

class TestEventCreationIntent:
    """detect_intent should return 'create_event' for creation keywords."""

    def test_detect_create_event_ua_створи(self):
        assert detect_intent("Створи зустріч в четвер о 15:00") == "create_event"

    def test_detect_create_event_ua_додай(self):
        assert detect_intent("Додай зустріч з Токарським") == "create_event"

    def test_detect_create_event_ua_заплануй(self):
        assert detect_intent("Заплануй мітинг на завтра") == "create_event"

    def test_detect_create_event_en_schedule(self):
        assert detect_intent("Schedule a meeting tomorrow at 2pm") == "create_event"

    def test_detect_create_event_en_create(self):
        assert detect_intent("Create a meeting with John") == "create_event"

    def test_calendar_view_still_works(self):
        """Calendar view intent should still work for non-creation queries."""
        assert detect_intent("Що у мене завтра?") == "calendar"

    def test_email_intent_unchanged(self):
        assert detect_intent("Покажи листи") == "email"


# ─── Event Parsing ───────────────────────────────────────────────────────────

class TestParseEventFromText:
    """parse_event_from_text should use Gemini to extract event details."""

    @pytest.mark.asyncio
    async def test_parse_returns_dict_with_required_fields(self):
        """Parsed result should contain title, date, time, duration_minutes."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "title": "Зустріч з Токарським",
            "date": "2026-05-08",
            "time": "15:00",
            "duration_minutes": 60,
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await parse_event_from_text(
            "Створи зустріч в четвер о 15:00 з Токарським", mock_model
        )

        assert result is not None
        assert result["title"] == "Зустріч з Токарським"
        assert result["date"] == "2026-05-08"
        assert result["time"] == "15:00"
        assert result["duration_minutes"] == 60

    @pytest.mark.asyncio
    async def test_parse_returns_none_on_garbage_input(self):
        """Should return None when model returns invalid JSON."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "I cannot parse this."
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await parse_event_from_text("just some random text", mock_model)
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_returns_none_on_exception(self):
        """Should return None when model raises an exception."""
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("API error"))

        result = await parse_event_from_text("Створи зустріч завтра", mock_model)
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_strips_markdown_fences(self):
        """Should handle JSON wrapped in markdown code fences."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '```json\n{"title": "Meeting", "date": "2026-05-09", "time": "10:00", "duration_minutes": 30}\n```'
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await parse_event_from_text("Create meeting tomorrow 10am", mock_model)

        assert result is not None
        assert result["title"] == "Meeting"
        assert result["duration_minutes"] == 30
