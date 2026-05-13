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
