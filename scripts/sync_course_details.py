#!/usr/bin/env python3
"""
Sync data/course_details/ from data/reference/ so each course folder has the latest course.json.
Run after updating reference JSONs (e.g. after feeding new course data).
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.phase1.config import Paths, COURSE_URLS

def main():
    paths = Paths.from_repo_root()
    ref = paths.reference
    details = paths.course_details
    for key in COURSE_URLS.keys():
        ref_file = ref / f"{key}.json"
        dest_dir = details / key
        dest_file = dest_dir / "course.json"
        if not ref_file.exists():
            print(f"Skip {key}: no reference file {ref_file}")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(ref_file.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Synced {key} -> {dest_file}")
    print("Done. course_details/ is in sync with reference/.")

if __name__ == "__main__":
    main()
