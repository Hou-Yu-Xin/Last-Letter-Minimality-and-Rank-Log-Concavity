#!/usr/bin/env python3
"""Reproduce Example 5.3 (diagonal sum): failure of the diagonal transfer analogue.

Paper location: Example 5.3, second part.
Checked object: C_w^1+G_w^1 for w=12.
Mathematical role: explains the off-diagonal condition q != r in Phi.
The script prints the coefficient sequence and its failed LC defect.
"""
from __future__ import annotations

import argparse

from verification_core import add, base_summary, direct_state, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    word = (0, 1)
    direction = 0
    state = direct_state(word, alphabet_size=2)
    coefficients = list(add(state.C[direction], state.G[direction]))
    expected = [1, 1, 2, 1]
    assert coefficients == expected, (coefficients, expected)
    lhs = coefficients[1] ** 2
    rhs = coefficients[0] * coefficients[2]
    assert lhs == 1 and rhs == 2 and lhs < rhs

    payload = base_summary("Example 5.3 diagonal transfer failure")
    payload.update(
        {
            "word": "12",
            "diagonal_direction": "1",
            "coefficients": coefficients,
            "failed_degree": 1,
            "log_concavity_lhs": lhs,
            "log_concavity_rhs": rhs,
            "result": "expected failure reproduced",
        }
    )
    write_json(args.output, payload)
    print("Example 5.3 diagonal transfer failure reproduced.")
    print(f"diagonal coefficients: {coefficients}")
    print(f"failed defect: {lhs} < {rhs}")


if __name__ == "__main__":
    main()
