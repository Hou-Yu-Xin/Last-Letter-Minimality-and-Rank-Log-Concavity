#!/usr/bin/env python3
"""Finite checks for previous-letter extremality and proved compensation.

Paper locations: Conjecture 5.4 and equation (5.2).
Previous-letter extremality remains conjectural. Equation (5.2) follows
from Theorem 1.1(i); this script checks its previous-terminal specialization.
The extended default ranges retain the first-draft regressions, with
10,088,798 comparison checks and 2,548,760 terminal events.
"""
from __future__ import annotations

import argparse

from verification_core import (
    EXTREMALITY_RANGES,
    base_summary,
    bracket,
    walk_frontier_states,
    write_json,
)

QUICK_RANGES = ((3, 8), (4, 6))


def run(ranges: tuple[tuple[int, int], ...]) -> dict[str, object]:
    per_range = []
    comparison_checks = 0
    terminal_events = 0
    compensation_checks = 0
    for alphabet_size, max_length in ranges:
        local_comparisons = 0
        local_events = 0
        for word, state in walk_frontier_states(alphabet_size, max_length):
            if not word:
                continue
            previous_terminal = word[-1]
            for new_terminal in range(alphabet_size):
                if new_terminal == previous_terminal:
                    continue
                # The extended regression totals count the nonnegative degrees
                # k=0,...,|word|+1. Negative indices remain zero-extended in
                # the shared coefficient routine but are not separate events.
                for k in range(0, len(word) + 2):
                    gamma = bracket(state.G[new_terminal], state.C[new_terminal], k)
                    reference = bracket(
                        state.C[new_terminal], state.C[previous_terminal], k
                    )
                    assert reference <= gamma, (
                        "proved adjacent-step compensation",
                        word,
                        new_terminal,
                        previous_terminal,
                        k,
                        reference,
                        gamma,
                    )
                    compensation_checks += 1
                    terminal_events += 1
                    local_events += 1
                    defects = []
                    for comparison in range(alphabet_size):
                        if comparison == new_terminal:
                            continue
                        defect = bracket(
                            state.C[new_terminal], state.C[comparison], k
                        )
                        assert defect <= reference, (
                            "previous-letter extremality",
                            word,
                            new_terminal,
                            previous_terminal,
                            comparison,
                            k,
                            defect,
                            reference,
                        )
                        defects.append(defect)
                        comparison_checks += 1
                        local_comparisons += 1
                    assert reference == max(defects)
        per_range.append(
            {
                "alphabet_size": alphabet_size,
                "maximum_length": max_length,
                "previous_letter_checks": local_comparisons,
                "terminal_events": local_events,
            }
        )
    return {
        "ranges": per_range,
        "previous_letter_checks": comparison_checks,
        "terminal_events": terminal_events,
        "previous_terminal_maximizer_events": terminal_events,
        "adjacent_compensation_checks": compensation_checks,
        "failures": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="use smaller smoke-test ranges")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    summary = run(QUICK_RANGES if args.quick else EXTREMALITY_RANGES)
    if not args.quick:
        assert summary["previous_letter_checks"] == 10_088_798
        assert summary["terminal_events"] == 2_548_760
        assert summary["adjacent_compensation_checks"] == 2_548_760
    payload = base_summary("previous-letter extremality and proved compensation")
    payload.update(
        {
            "profile": "quick" if args.quick else "extended",
            **summary,
            "statement_status": {
                "previous_letter_extremality": "conjectural: Conjecture 5.4",
                "adjacent_compensation": (
                    "proved: equation (5.2); checked here for the previous terminal"
                ),
            },
            "result": (
                "all checks passed; no counterexample to previous-letter "
                "extremality in the tested ranges"
            ),
        }
    )
    write_json(args.output, payload)
    print("Previous-letter extremality and proved compensation checks completed.")
    print(f"previous-letter checks: {summary['previous_letter_checks']:,}")
    print(f"terminal/maximizer events: {summary['terminal_events']:,}")
    print(f"adjacent compensation checks: {summary['adjacent_compensation_checks']:,}")
    print("No counterexample to Conjecture 5.4 in the tested ranges.")


if __name__ == "__main__":
    main()
