"""Fallback wrapper for users who haven't `uv tool install`ed the package globally.

Usage:
    python scripts/generate.py --image ... --prompt "..." --output ./out
"""
import sys

from sangpye_skill.cli import main

if __name__ == "__main__":
    sys.exit(main())
