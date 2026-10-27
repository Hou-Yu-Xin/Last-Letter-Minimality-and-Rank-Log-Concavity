#!/usr/bin/env python3
"""Reproduce Example 5.3 (append gain): a non-log-concave append-gain polynomial.

Paper location: Example 5.3, first part.
Checked object: G_w^r for w=121213 and r=2 (one-based letters).
Mathematical role: shows that append closure cannot require G itself to be
log-concave.  The script prints the full coefficients and the failed defect.
"""
from __future__ import annotations

import argparse

from verification_core import base_summary, direct_state, trim_outer_zeros, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    word = (0, 1, 0, 1, 0, 2)
    direction = 1
    state = direct_state(word, alphabet_size=3)
    coefficients = list(state.G[direction])
    expected = [0, 0, 1, 2, 2, 3, 3, 1]
    assert coefficients == expected, (coefficients, expected)
    trimmed = trim_outer_zeros(coefficients)
    lhs = coefficients[4] ** 2
    rhs = coefficients[3] * coefficients[5]
    assert lhs == 4 and rhs == 6 and lhs < rhs

    payload = base_summary("Example 5.3 append-gain failure")
    payload.update(
        {
            "word": "121213",
            "append_direction": "2",
            "coefficients": coefficients,
            "trimmed_coefficients": trimmed,
            "failed_degree": 4,
            "log_concavity_lhs": lhs,
            "log_concavity_rhs": rhs,
            "result": "expected failure reproduced",
        }
    )
    write_json(args.output, payload)
    print("Example 5.3 append-gain failure reproduced.")
    print(f"G coefficients: {coefficients}")
    print(f"trimmed coefficients: {trimmed}")
    print(f"failed defect: {lhs} < {rhs}")


if __name__ == "__main__":
    main()
