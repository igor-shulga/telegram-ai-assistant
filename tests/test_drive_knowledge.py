"""Tests for Feature 3: Google Drive as additional knowledge source."""

import os
from unittest.mock import patch, MagicMock

import pytest

from app.knowledge import get_drive_context, get_context


# ─── Drive Context ───────────────────────────────────────────────────────────

class TestGetDriveContext:
    """get_drive_context should find and read relevant Drive files."""

    @patch("app.google_services.read_drive_file")
    @patch("app.google_services.list_drive_files")
    @patch("app.knowledge.google_enabled", return_value=True)
    def test_returns_content_for_matching_files(self, mock_enabled, mock_list, mock_read):
        mock_list.return_value = [
            {"id": "f1", "name": "facilitation-tips.md", "description": ""},
            {"id": "f2", "name": "project-notes.md", "description": ""},
        ]
        mock_read.side_effect = lambda fid: {
            "f1": "Facilitation content here",
            "f2": "Project notes content",
        }.get(fid, "")

        result = get_drive_context("facilitation tips for remote meetings")

        assert "Facilitation content here" in result
        mock_list.assert_called_once()

    @patch("app.google_services.read_drive_file")
    @patch("app.google_services.list_drive_files")
    @patch("app.knowledge.google_enabled", return_value=True)
    def test_returns_empty_when_no_files_match(self, mock_enabled, mock_list, mock_read):
        mock_list.return_value = [
            {"id": "f1", "name": "cooking-recipes.md", "description": ""},
        ]

        result = get_drive_context("quantum physics")
        assert result == ""

    @patch("app.google_services.list_drive_files")
    @patch("app.knowledge.google_enabled", return_value=True)
    def test_returns_empty_when_no_drive_files(self, mock_enabled, mock_list):
        mock_list.return_value = []
        result = get_drive_context("anything")
        assert result == ""

    @patch("app.knowledge.google_enabled", return_value=False)
    def test_skips_when_google_not_configured(self, mock_enabled):
        result = get_drive_context("anything")
        assert result == ""


# ─── Combined Context ────────────────────────────────────────────────────────

class TestGetContextCombined:
    """get_context should combine GitHub KB and Drive KB results."""

    @pytest.mark.asyncio
    @patch("app.knowledge.get_drive_context")
    @patch("app.knowledge.fetch_raw")
    async def test_combines_github_and_drive(self, mock_fetch, mock_drive):
        mock_fetch.return_value = "# GitHub KB content"
        mock_drive.return_value = "Drive content about facilitation"

        result = await get_context("фасилітація overview", model=None)

        assert "GitHub KB content" in result
        assert "Drive content about facilitation" in result

    @pytest.mark.asyncio
    @patch("app.knowledge.get_drive_context")
    @patch("app.knowledge.fetch_raw")
    async def test_returns_only_github_when_drive_empty(self, mock_fetch, mock_drive):
        mock_fetch.return_value = "# GitHub content"
        mock_drive.return_value = ""

        result = await get_context("фасилітація", model=None)

        assert "GitHub content" in result

    @pytest.mark.asyncio
    @patch("app.knowledge.get_drive_context")
    @patch("app.knowledge.select_files_by_keywords")
    async def test_returns_only_drive_when_github_empty(self, mock_select, mock_drive):
        mock_select.return_value = []
        mock_drive.return_value = "Drive-only content"

        result = await get_context("some drive topic", model=None)

        assert "Drive-only content" in result
