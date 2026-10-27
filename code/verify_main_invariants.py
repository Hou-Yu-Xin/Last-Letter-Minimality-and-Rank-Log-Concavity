#!/usr/bin/env python3
"""Regression checks for the main invariants and rank log-concavity.

Paper locations: Lemmas 2.1 and 2.2 and Theorem 1.1.
Checked objects: direct-enumeration versus frontier recurrence, continuation
log-concavity, the last-letter ratio minimum, and rank log-concavity.
The extended default run retains the first-draft ranges and checks
1,006,729 recurrence states. The independent counts reported in Section 5.2
are reproduced by independent_checks.py.
"""
from __future__ import annotations

import argparse

from verification_core import (
    MAIN_RANGES,
    RECURRENCE_RANGES,
    base_summary,
    bracket,
    direct_state,
    expected_word_count,
    log_concave,
    no_internal_zeros,
    walk_frontier_states,
    write_json,
)

QUICK_MAIN_RANGES = ((3, 8), (4, 6))
QUICK_RECURRENCE_RANGES = ((3, 6), (4, 5))


def recurrence_validation(ranges: tuple[tuple[int, int], ...]) -> dict[str, object]:
    per_range = []
    total = 0
    for alphabet_size, max_length in ranges:
        count = 0
        for word, recurrent in walk_frontier_states(alphabet_size, max_length):
            direct = direct_state(word, alphabet_size, cap=len(recurrent.A))
            assert recurrent == direct, ("recurrence mismatch", word, recurrent, direct)
            count += 1
        assert count == expected_word_count(alphabet_size, max_length)
        total += count
        per_range.append(
            {"alphabet_size": alphabet_size, "maximum_length": max_length, "words": count}
        )
    return {"ranges": per_range, "words": total, "mismatches": 0}


def main_invariant_regression(ranges: tuple[tuple[int, int], ...]) -> dict[str, object]:
    per_range = []
    total_words = 0
    continuation_checks = 0
    last_letter_checks = 0
    for alphabet_size, max_length in ranges:
        words = 0
        for word, state in walk_frontier_states(alphabet_size, max_length):
            assert log_concave(state.A), ("rank log-concavity", word, state.A)
            for letter in range(alphabet_size):
                assert no_internal_zeros(state.C[letter]), (
                    "continuation support",
                    word,
                    letter,
                    state.C[letter],
                )
                assert log_concave(state.C[letter]), (
                    "continuation log-concavity",
                    word,
                    letter,
                    state.C[letter],
                )
                continuation_checks += 1
            if word:
                terminal = word[-1]
                for comparison in range(alphabet_size):
                    if comparison == terminal:
                        continue
                    for k in range(-1, len(word) + 2):
                        defect = bracket(state.C[comparison], state.C[terminal], k)
                        assert defect >= 0, (
                            "last-letter ratio minimum",
                            word,
                            comparison,
                            terminal,
                            k,
                            defect,
                        )
                        last_letter_checks += 1
            words += 1
        assert words == expected_word_count(alphabet_size, max_length)
        total_words += words
        per_range.append(
            {"alphabet_size": alphabet_size, "maximum_length": max_length, "words": words}
        )
    return {
        "ranges": per_range,
        "words": total_words,
        "continuation_polynomials": continuation_checks,
        "last_letter_defects": last_letter_checks,
        "failures": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="use smaller smoke-test ranges")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    recurrence_ranges = QUICK_RECURRENCE_RANGES if args.quick else RECURRENCE_RANGES
    main_ranges = QUICK_MAIN_RANGES if args.quick else MAIN_RANGES
    recurrence = recurrence_validation(recurrence_ranges)
    invariants = main_invariant_regression(main_ranges)
    if not args.quick:
        assert invariants["words"] == 1_006_729

    payload = base_summary("main invariant regression")
    payload.update(
        {
            "profile": "quick" if args.quick else "extended",
            "recurrence_validation": recurrence,
            "main_invariants": invariants,
            "result": "all assertions passed",
        }
    )
    write_json(args.output, payload)
    print("Main invariant regression: all assertions passed.")
    print(f"recurrence-validation words: {recurrence['words']:,}")
    print(f"main-regression words: {invariants['words']:,}")
    print(f"continuation polynomials: {invariants['continuation_polynomials']:,}")
    print(f"last-letter defects: {invariants['last_letter_defects']:,}")


if __name__ == "__main__":
    main()
