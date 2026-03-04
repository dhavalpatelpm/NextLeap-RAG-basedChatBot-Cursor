"""Phase 5 config: schedule, last_updated path."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_REFRESH_INTERVAL_HOURS = 24
LAST_REFRESH_FILENAME = ".last_refresh"


@dataclass
class Phase5Config:
    repo_root: Optional[Path] = None
    refresh_interval_hours: int = DEFAULT_REFRESH_INTERVAL_HOURS

    def __post_init__(self) -> None:
        if self.repo_root is None:
            self.repo_root = Path(__file__).resolve().parent.parent.parent

    @property
    def last_refresh_path(self) -> Path:
        return self.repo_root / "data" / LAST_REFRESH_FILENAME
