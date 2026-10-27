#!/usr/bin/env python3
"""Compatibility entry point for the first-draft Section 7 verifier.

Use verify_previous_letter_extremality.py for the current paper.
Previous-letter extremality is Conjecture 5.4; compensation is proved in (5.2).
"""
from verify_previous_letter_extremality import QUICK_RANGES, main, run

__all__ = ["QUICK_RANGES", "main", "run"]


if __name__ == "__main__":
    main()
