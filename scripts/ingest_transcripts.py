#!/usr/bin/env python
"""
Transcript Ingestion CLI for The Lenny Growth Assistant.

Usage:
    python scripts/ingest_transcripts.py --limit 10
    python scripts/ingest_transcripts.py --all
    python scripts/ingest_transcripts.py --force
"""

import os
import sys
import argparse
import asyncio
import logging

# Add backend directory to sys.path so app imports work seamlessly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.retrieval.ingestion import ingest_transcripts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ingest_cli")


def main():
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast Transcripts into Vector Store.")
    parser.add_argument("--limit", type=int, default=15, help="Number of episodes to ingest (default: 15)")
    parser.add_argument("--all", action="store_true", help="Ingest all available episodes")
    parser.add_argument("--force", action="store_true", help="Force re-indexing of already processed episodes")
    parser.add_argument("--local-dir", type=str, default=None, help="Custom path to local transcript markdown files")

    args = parser.parse_args()
    limit = None if args.all else args.limit

    print("=" * 60)
    print("  Lenny Growth Assistant - Transcript Ingestion Pipeline")
    print("=" * 60)
    print(f"Target episodes: {'ALL' if args.all else limit}")
    print(f"Force re-index: {args.force}")
    print("Connecting to ChatPRD/lennys-podcast-transcripts repository...")
    print("=" * 60)

    try:
        total = asyncio.run(ingest_transcripts(
            limit=limit,
            local_dir=args.local_dir,
            force_reindex=args.force
        ))
        print("\n" + "=" * 60)
        print(f"[SUCCESS] Ingestion completed! Total indexed chunks: {total}")
        print("Knowledge base is ready for Grounded Q&A and Ship30 essay generation.")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n[ABORTED] Ingestion cancelled by user.")
    except Exception as e:
        logger.exception("Ingestion failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
