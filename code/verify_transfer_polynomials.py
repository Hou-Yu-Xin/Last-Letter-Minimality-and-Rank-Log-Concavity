#!/usr/bin/env python3
"""Regression checks for off-diagonal transfer-polynomial log-concavity.

Paper location: Corollary 4.3 (Transfer log-concavity).
The extended default run retains the first-draft regression ranges.
Checked object: Phi_w^{r->q}=C_w^q+G_w^r for every q != r.
Mathematical role: finite regression evidence for transfer closure, not proof.
"""
from __future__ import annotations

import argparse

from verification_core import (
    MAIN_RANGES,
    add,
    base_summary,
    expected_word_count,
    log_concave,
    no_internal_zeros,
    walk_frontier_states,
    write_json,
)

QUICK_RANGES = ((3, 8), (4, 6))


def run(ranges: tuple[tuple[int, int], ...]) -> dict[str, object]:
    per_range = []
    total_words = 0
    transfer_checks = 0
    for alphabet_size, max_length in ranges:
        words = 0
        for word, state in walk_frontier_states(alphabet_size, max_length):
            cap = len(state.A)
            for append_direction in range(alphabet_size):
                for target in range(alphabet_size):
                    if target == append_direction:
                        continue
                    phi = add(
                        state.C[target], state.G[append_direction], cap=cap
                    )
                    assert no_internal_zeros(phi), (
                        "transfer support",
                        word,
                        append_direction,
                        target,
                        phi,
                    )
                    assert log_concave(phi), (
                        "transfer log-concavity",
                        word,
                        append_direction,
                        target,
                        phi,
                    )
                    transfer_checks += 1
            words += 1
        assert words == expected_word_count(alphabet_size, max_length)
        total_words += words
        per_range.append(
            {"alphabet_size": alphabet_size, "maximum_length": max_length, "words": words}
        )
    return {
        "ranges": per_range,
        "words": total_words,
        "transfer_polynomials": transfer_checks,
        "failures": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="use smaller smoke-test ranges")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    summary = run(QUICK_RANGES if args.quick else MAIN_RANGES)
    if not args.quick:
        assert summary["words"] == 1_006_729
    payload = base_summary("transfer-polynomial regression")
    payload.update(
        {
            "profile": "quick" if args.quick else "extended",
            **summary,
            "result": "all assertions passed",
        }
    )
    write_json(args.output, payload)
    print("Transfer-polynomial regression: all assertions passed.")
    print(f"words: {summary['words']:,}")
    print(f"off-diagonal transfer polynomials: {summary['transfer_polynomials']:,}")


if __name__ == "__main__":
    main()
