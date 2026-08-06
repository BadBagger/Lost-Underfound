#!/usr/bin/env python3
"""Compatibility wrapper for Bramble's generic engine-export QA."""

from __future__ import annotations

from check_character_engine_export import check_character


def main() -> None:
    check_character("bramble")


if __name__ == "__main__":
    main()
