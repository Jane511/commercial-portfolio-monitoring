"""Command-line entry point for the portfolio-monitor pipeline."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline import main


if __name__ == "__main__":
    main()
