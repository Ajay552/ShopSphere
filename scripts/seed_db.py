#!/usr/bin/env python3
"""Create and seed ShopSphere SQLite database from data/*.json."""

import argparse
import sys
from pathlib import Path

# Allow running as: python scripts/seed_db.py from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.db import DEFAULT_SQLITE_PATH, get_database_url
from tools.seed import seed_from_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ShopSphere SQLite from JSON files.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop and recreate all tables, then re-import from JSON.",
    )
    args = parser.parse_args()

    seed_from_json(force=args.force)
    print(f"Database seeded: {get_database_url()}")
    if get_database_url().startswith("sqlite"):
        print(f"SQLite file: {DEFAULT_SQLITE_PATH}")


if __name__ == "__main__":
    main()
