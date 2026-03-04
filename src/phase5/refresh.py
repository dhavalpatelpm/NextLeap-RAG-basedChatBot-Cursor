"""
Data refresh: run Phase 1 (scrape + merge) → sync canonical to course_details → Phase 2 (rebuild RAG).
Writes last_updated timestamp. On Phase 1 failure, Phase 2 is not run.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.phase1.config import Paths, COURSE_URLS

from .config import Phase5Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _sync_canonical_to_course_details(repo_root: Optional[Path] = None) -> None:
    """Copy canonical/*.json to course_details/<key>/course.json so Phase 2 sees latest data."""
    paths = Paths.from_repo_root(repo_root)
    for key in COURSE_URLS.keys():
        src = paths.canonical / f"{key}.json"
        if not src.exists():
            logger.warning("Canonical file missing for %s, skipping sync", key)
            continue
        dest_dir = paths.course_details / key
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "course.json"
        content = src.read_text(encoding="utf-8")
        # Ensure source_url in course.json for Phase 3 responses
        try:
            data = json.loads(content)
            if "source_url" not in data:
                from src.phase1.config import get_course_url
                data["source_url"] = get_course_url(key)
                content = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            pass
        dest.write_text(content, encoding="utf-8")
        logger.info("Synced %s -> %s", src.name, dest)


def _write_last_refresh(config: Phase5Config) -> None:
    """Write current UTC timestamp to data/.last_refresh."""
    config.repo_root = config.repo_root or Path(__file__).resolve().parent.parent.parent
    data_dir = config.repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = config.last_refresh_path
    path.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    logger.info("Wrote last_refresh: %s", path)


def run_refresh(
    scrape: bool = True,
    config: Optional[Phase5Config] = None,
    repo_root: Optional[Path] = None,
) -> bool:
    """
    Run full data refresh: Phase 1 (optionally scrape + merge) → sync to course_details → Phase 2.
    Returns True if successful. On Phase 1 failure, returns False and does not run Phase 2.
    """
    cfg = config or Phase5Config()
    if repo_root is not None:
        cfg.repo_root = repo_root
    root = cfg.repo_root or Path(__file__).resolve().parent.parent.parent

    try:
        # Phase 1: scrape (optional) + merge → canonical
        from src.phase1.merge import run_phase1
        paths = Paths.from_repo_root(root)
        paths.scraped.mkdir(parents=True, exist_ok=True)
        paths.canonical.mkdir(parents=True, exist_ok=True)
        run_phase1(scrape_first=scrape, merge_after=True)
        logger.info("Phase 1 complete.")
    except Exception as e:
        logger.exception("Phase 1 failed: %s. Phase 2 will not run.", e)
        return False

    # Sync canonical → course_details so Phase 2 loader has latest
    _sync_canonical_to_course_details(root)

    try:
        # Phase 2: rebuild RAG index
        from src.phase2.build import run_phase2
        from src.phase2.config import RAGConfig
        rag_cfg = RAGConfig()
        rag_cfg.vector_store_path = root / "data" / "vector_store"
        run_phase2(config=rag_cfg)
        logger.info("Phase 2 complete.")
    except Exception as e:
        logger.exception("Phase 2 failed: %s", e)
        # Still write last_refresh since Phase 1 succeeded and canonical is updated
        _write_last_refresh(cfg)
        return False

    _write_last_refresh(cfg)
    return True


def get_last_refresh_iso(config: Optional[Phase5Config] = None) -> Optional[str]:
    """Return last refresh timestamp (ISO string) or None if never run."""
    cfg = config or Phase5Config()
    path = cfg.last_refresh_path
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return None
