#!/usr/bin/env python3
"""Verify the alternating-suffix injection and its inverse.

Paper location: Lemma 2.3 (Alternating-suffix deletion).
Checked object: the distinct-word injection E_{u,x,k} -> C_{u,z,k-1}.
Mathematical role: coefficientwise control used in the proof of Theorem 1.1.
The default regression range has n=3 and |u|<=5 and contains 2,346 sources.
"""
from __future__ import annotations

import argparse
from collections import Counter

from verification_core import (
    alternating_delete,
    alternating_inverse,
    base_summary,
    distinct_reduced_subwords,
    reduced_words,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--alphabet-size", type=int, default=3)
    parser.add_argument("-m", "--max-length", type=int, default=5)
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()

    by_length: Counter[int] = Counter()
    source_count = 0
    ambient_count = 0
    for ambient in reduced_words(args.alphabet_size, args.max_length):
        ambient_count += 1
        subwords = distinct_reduced_subwords(ambient)
        for x in range(args.alphabet_size):
            for z in range(args.alphabet_size):
                if x == z:
                    continue
                images = {}
                for source in sorted(subwords):
                    if not source or source[-1] != x:
                        continue
                    image = alternating_delete(source, x, z)
                    assert image in subwords, (ambient, x, z, source, image)
                    assert len(image) == len(source) - 1
                    assert not image or image[-1] != z
                    assert alternating_inverse(image, x, z) == source
                    assert image not in images, (
                        "collision",
                        ambient,
                        x,
                        z,
                        images.get(image),
                        source,
                        image,
                    )
                    images[image] = source
                    source_count += 1
                    by_length[len(ambient)] += 1

    if args.alphabet_size == 3 and args.max_length == 5:
        expected = {1: 6, 2: 36, 3: 144, 4: 504, 5: 1656}
        assert dict(sorted(by_length.items())) == expected
        assert source_count == 2346

    payload = base_summary("alternating-suffix injection")
    payload.update(
        {
            "alphabet_size": args.alphabet_size,
            "maximum_ambient_length": args.max_length,
            "ambient_words": ambient_count,
            "sources": source_count,
            "sources_by_ambient_length": dict(sorted(by_length.items())),
            "inverse_reconstructions": source_count,
            "collisions": 0,
            "result": "all assertions passed",
        }
    )
    write_json(args.output, payload)
    print("Alternating-suffix injection: all assertions passed.")
    print(f"source instances: {source_count:,}")
    print(f"by ambient length: {dict(sorted(by_length.items()))}")


if __name__ == "__main__":
    main()
