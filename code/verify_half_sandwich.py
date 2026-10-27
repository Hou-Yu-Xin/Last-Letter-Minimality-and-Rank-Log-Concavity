#!/usr/bin/env python3
"""Verify structural defect identities and return/open path sandwiches.

Paper locations: Corollary 4.2 and the return/open paths in Section 4.2.
Checked objects: the transfer-surplus decomposition, left-defect expansion,
right-defect cancellation, and both cross-multiplied path inequalities.
The structural range has exactly 2,304 (u,z,x,k) instances per identity.
The extended default run retains the first-draft path regression ranges.
"""
from __future__ import annotations

import argparse

from verification_core import (
    PATH_RANGES,
    add,
    append_state,
    base_summary,
    coefficient,
    continuation_set,
    direct_state,
    reduced_words,
    shift,
    subtract,
    walk_frontier_states,
    write_json,
)

QUICK_PATH_RANGES = ((3, 7), (4, 6))


def structural_identities() -> dict[str, object]:
    alphabet_size = 3
    max_length = 5
    transfer_count = 0
    left_count = 0
    right_count = 0
    for word in reduced_words(alphabet_size, max_length):
        cap = len(word) + 4
        state = direct_state(word, alphabet_size, cap=cap)
        for append_direction in range(alphabet_size):
            if word and word[-1] == append_direction:
                continue
            child = direct_state(
                word + (append_direction,), alphabet_size, cap=cap
            )
            for target in range(alphabet_size):
                if target == append_direction:
                    continue
                M = state.C[append_direction]
                F = state.E[target]
                Y = child.C[target]
                sigma = subtract(shift(M, cap), F, cap=cap)
                continuation_pair = continuation_set(
                    word, frozenset((target, append_direction)), cap
                )
                for k in range(len(word) + 2):
                    transfer_lhs = coefficient(Y, k)
                    transfer_rhs = coefficient(M, k) + coefficient(sigma, k)
                    assert transfer_lhs == transfer_rhs, (
                        "transfer-surplus decomposition",
                        word,
                        append_direction,
                        target,
                        k,
                        transfer_lhs,
                        transfer_rhs,
                    )
                    transfer_count += 1

                    left = (
                        coefficient(Y, k) * coefficient(M, k - 1)
                        - coefficient(Y, k - 1) * coefficient(M, k)
                    )
                    left_expansion = (
                        coefficient(M, k - 1) ** 2
                        - coefficient(M, k - 2) * coefficient(M, k)
                        - coefficient(F, k) * coefficient(M, k - 1)
                        + coefficient(F, k - 1) * coefficient(M, k)
                    )
                    assert left == left_expansion, (
                        "left defect expansion",
                        word,
                        append_direction,
                        target,
                        k,
                        left,
                        left_expansion,
                    )
                    left_count += 1

                    right = (
                        coefficient(M, k) * coefficient(Y, k)
                        - coefficient(M, k - 1) * coefficient(Y, k + 1)
                    )
                    right_cancellation = (
                        coefficient(M, k) * coefficient(continuation_pair, k)
                        - coefficient(M, k - 1)
                        * coefficient(continuation_pair, k + 1)
                    )
                    assert right == right_cancellation, (
                        "right defect cancellation",
                        word,
                        append_direction,
                        target,
                        k,
                        right,
                        right_cancellation,
                    )
                    right_count += 1

    assert transfer_count == 2304
    assert left_count == 2304
    assert right_count == 2304
    return {
        "alphabet_size": 3,
        "maximum_length": 5,
        "transfer_surplus_instances": transfer_count,
        "left_defect_instances": left_count,
        "right_defect_instances": right_count,
        "mismatches": 0,
    }


def path_sandwiches(ranges: tuple[tuple[int, int], ...]) -> dict[str, object]:
    per_range = []
    return_paths = 0
    open_paths = 0
    defect_checks = 0
    minimum_defect = None
    for alphabet_size, max_length in ranges:
        local_return = 0
        local_open = 0
        for word, state in walk_frontier_states(
            alphabet_size, max_length, extra_degree=3
        ):
            for first_append in range(alphabet_size):
                if word and word[-1] == first_append:
                    continue
                middle_state = append_state(state, first_append)
                for second_append in range(alphabet_size):
                    if second_append == first_append:
                        continue
                    final_state = append_state(middle_state, second_append)
                    M = middle_state.C[second_append]
                    for target in range(alphabet_size):
                        if target == second_append:
                            continue
                        Y = final_state.C[target]
                        if target == first_append:
                            return_paths += 1
                            local_return += 1
                        else:
                            open_paths += 1
                            local_open += 1
                        for k in range(-1, len(word) + 4):
                            left = (
                                coefficient(Y, k) * coefficient(M, k - 1)
                                - coefficient(Y, k - 1) * coefficient(M, k)
                            )
                            right = (
                                coefficient(M, k) * coefficient(Y, k)
                                - coefficient(M, k - 1) * coefficient(Y, k + 1)
                            )
                            assert left >= 0, (
                                "return/open left sandwich",
                                word,
                                first_append,
                                second_append,
                                target,
                                k,
                                left,
                            )
                            assert right >= 0, (
                                "return/open right sandwich",
                                word,
                                first_append,
                                second_append,
                                target,
                                k,
                                right,
                            )
                            minimum_defect = (
                                min(left, right)
                                if minimum_defect is None
                                else min(minimum_defect, left, right)
                            )
                            defect_checks += 2
        per_range.append(
            {
                "alphabet_size": alphabet_size,
                "maximum_length": max_length,
                "return_paths": local_return,
                "open_paths": local_open,
            }
        )
    return {
        "ranges": per_range,
        "return_paths": return_paths,
        "open_paths": open_paths,
        "defect_checks": defect_checks,
        "minimum_defect": minimum_defect,
        "negative_values": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="use smaller path ranges")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    identities = structural_identities()
    paths = path_sandwiches(QUICK_PATH_RANGES if args.quick else PATH_RANGES)
    payload = base_summary("half-sandwich identities and path regression")
    payload.update(
        {
            "profile": "quick" if args.quick else "extended",
            "structural_identities": identities,
            "path_sandwiches": paths,
            "result": "all assertions passed",
        }
    )
    write_json(args.output, payload)
    print("Half-sandwich verification: all assertions passed.")
    print("structural instances per identity: 2,304")
    print(f"return paths: {paths['return_paths']:,}")
    print(f"open paths: {paths['open_paths']:,}")
    print(f"minimum cross-multiplied defect: {paths['minimum_defect']}")


if __name__ == "__main__":
    main()
