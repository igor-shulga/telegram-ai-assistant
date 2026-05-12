"""Shared fixtures for all tests."""

import os
import pytest

# Set required env vars before importing app modules
os.environ.setdefault("GOOGLE_API_KEY", "test-api-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
os.environ.setdefault("WEBHOOK_BASE_URL", "https://test.example.com")
