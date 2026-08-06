#!/usr/bin/env python3
"""Compatibility wrapper for Bramble's generic engine package export."""

from __future__ import annotations

from export_character_engine_packages import export_character


def main() -> int:
    export_character("bramble")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
