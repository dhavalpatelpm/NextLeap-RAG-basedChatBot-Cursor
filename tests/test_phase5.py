"""
Tests for Phase 5: data refresh (sync, last_refresh, run_refresh with --no-scrape).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Repo root
REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPhase5SyncAndLastRefresh:
    """Test sync canonical → course_details and last_refresh file."""

    def test_get_last_refresh_returns_none_when_no_file(self):
        from src.phase5.refresh import get_last_refresh_iso
        from src.phase5.config import Phase5Config
        cfg = Phase5Config(repo_root=REPO_ROOT)
        path = cfg.last_refresh_path
        if path.exists():
            path.unlink()
        assert get_last_refresh_iso(cfg) is None

    def test_sync_canonical_to_course_details_skips_missing(self):
        """If canonical has no file for a key, sync skips without error."""
        from src.phase5.refresh import _sync_canonical_to_course_details
        # Ensure at least reference-based course_details exist; sync may skip missing canonical
        _sync_canonical_to_course_details(REPO_ROOT)
        # No exception
        assert True

    @pytest.mark.skip(reason="run_refresh loads Phase 2 (sentence_transformers/torch); run manually: python scripts/run_phase5_refresh.py --no-scrape")
    def test_run_refresh_no_scrape_merge_and_phase2(self):
        """run_refresh(scrape=False) runs merge + sync + Phase 2 and writes last_refresh."""
        from src.phase5 import run_refresh
        from src.phase5.refresh import get_last_refresh_iso
        from src.phase5.config import Phase5Config
        cfg = Phase5Config(repo_root=REPO_ROOT)
        ok = run_refresh(scrape=False, config=cfg)
        iso = get_last_refresh_iso(cfg)
        assert iso is not None
        assert "T" in iso or "Z" in iso or "-" in iso


class TestPhase5StatusEndpoint:
    """Phase 4 /api/status exposes data_last_refreshed_at when Phase 5 has run."""

    def test_status_includes_last_refresh_key(self):
        from fastapi.testclient import TestClient
        from src.phase4.api import app
        client = TestClient(app)
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.json()
        assert "data_last_refreshed_at" in data
        assert data.get("status") == "ok"
