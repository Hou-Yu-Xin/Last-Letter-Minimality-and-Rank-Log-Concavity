#!/usr/bin/env python3
"""Shared exact-integer routines for the paper's finite regressions.

All enumerations count distinct reduced scattered words, never embedding
multiplicities.  The direct implementation constructs a set of words.  The
frontier implementation uses the append-gain recurrence from the paper.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, product
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, Iterator, Sequence, Tuple

Word = Tuple[int, ...]
Polynomial = Tuple[int, ...]

if not __debug__:
    raise RuntimeError(
        "Verification requires assertions; run Python without -O or -OO."
    )


MAIN_RANGES = ((2, 20), (3, 15), (4, 11), (5, 9), (6, 7))
PATH_RANGES = ((2, 20), (3, 12), (4, 8), (5, 7), (6, 6))
EXTREMALITY_RANGES = PATH_RANGES
SECTION7_RANGES = EXTREMALITY_RANGES  # Compatibility with first-draft scripts.
RECURRENCE_RANGES = ((3, 9), (4, 8))


@dataclass(frozen=True)
class FrontierState:
    """Coefficient arrays A, E, C, and G at one reduced word."""

    A: Polynomial
    E: Tuple[Polynomial, ...]
    C: Tuple[Polynomial, ...]
    G: Tuple[Polynomial, ...]


def coefficient(seq: Sequence[int], k: int) -> int:
    return seq[k] if 0 <= k < len(seq) else 0


def add(*seqs: Sequence[int], cap: int | None = None) -> Polynomial:
    length = cap if cap is not None else max((len(seq) for seq in seqs), default=0)
    return tuple(sum(coefficient(seq, k) for seq in seqs) for k in range(length))


def subtract(a: Sequence[int], b: Sequence[int], cap: int | None = None) -> Polynomial:
    length = cap if cap is not None else max(len(a), len(b))
    return tuple(coefficient(a, k) - coefficient(b, k) for k in range(length))


def shift(seq: Sequence[int], cap: int | None = None) -> Polynomial:
    length = cap if cap is not None else len(seq) + 1
    return tuple(0 if k == 0 else coefficient(seq, k - 1) for k in range(length))


def trim_outer_zeros(seq: Sequence[int]) -> list[int]:
    lo = 0
    hi = len(seq)
    while lo < hi and seq[lo] == 0:
        lo += 1
    while hi > lo and seq[hi - 1] == 0:
        hi -= 1
    return list(seq[lo:hi])


def no_internal_zeros(seq: Sequence[int]) -> bool:
    return all(value > 0 for value in trim_outer_zeros(seq))


def log_concave(seq: Sequence[int]) -> bool:
    return all(
        coefficient(seq, k) ** 2
        >= coefficient(seq, k - 1) * coefficient(seq, k + 1)
        for k in range(len(seq))
    )


def bracket(P: Sequence[int], Q: Sequence[int], k: int) -> int:
    return (
        coefficient(P, k) * coefficient(Q, k - 1)
        - coefficient(P, k - 1) * coefficient(Q, k)
    )


def polynomial_equal(a: Sequence[int], b: Sequence[int]) -> bool:
    length = max(len(a), len(b))
    return all(coefficient(a, k) == coefficient(b, k) for k in range(length))


def reduced_words(alphabet_size: int, max_length: int) -> Iterator[Word]:
    """Generate reduced words by length, then lexicographically."""

    yield ()
    for length in range(1, max_length + 1):
        for first in range(alphabet_size):
            if length == 1:
                yield (first,)
                continue
            for choices in product(range(alphabet_size - 1), repeat=length - 1):
                word = [first]
                for choice in choices:
                    available = [letter for letter in range(alphabet_size) if letter != word[-1]]
                    word.append(available[choice])
                yield tuple(word)


def expected_word_count(alphabet_size: int, max_length: int) -> int:
    if max_length == 0:
        return 1
    if alphabet_size == 2:
        return 1 + 2 * max_length
    return 1 + alphabet_size * (
        (alphabet_size - 1) ** max_length - 1
    ) // (alphabet_size - 2)


@lru_cache(maxsize=None)
def distinct_reduced_subwords(word: Word) -> frozenset[Word]:
    """Enumerate distinct reduced scattered subwords set-theoretically."""

    states = {()}
    for letter in word:
        extensions = {
            subword + (letter,)
            for subword in states
            if not subword or subword[-1] != letter
        }
        states |= extensions
    return frozenset(states)


def count_by_degree(words: Iterable[Word], cap: int) -> Polynomial:
    counts = [0] * cap
    for word in words:
        counts[len(word)] += 1
    return tuple(counts)


def direct_state(word: Word, alphabet_size: int, cap: int | None = None) -> FrontierState:
    """Construct A, E, C, and G directly from distinct-word sets."""

    cap = cap if cap is not None else len(word) + 2
    subwords = distinct_reduced_subwords(word)
    A = count_by_degree(subwords, cap)
    E = []
    C = []
    G = []
    for letter in range(alphabet_size):
        ending = count_by_degree((u for u in subwords if u and u[-1] == letter), cap)
        continuation = subtract(A, ending, cap)
        E.append(ending)
        C.append(continuation)
        G.append(subtract(shift(continuation, cap), ending, cap))
    return FrontierState(A, tuple(E), tuple(C), tuple(G))


def initial_state(alphabet_size: int, cap: int) -> FrontierState:
    A = tuple([1] + [0] * (cap - 1))
    zero = tuple([0] * cap)
    continuation = A
    gain = shift(continuation, cap)
    return FrontierState(
        A,
        tuple(zero for _ in range(alphabet_size)),
        tuple(continuation for _ in range(alphabet_size)),
        tuple(gain for _ in range(alphabet_size)),
    )


def append_state(state: FrontierState, letter: int) -> FrontierState:
    """Apply the exact frontier recurrence for one legal append."""

    cap = len(state.A)
    A_new = add(state.A, state.G[letter], cap=cap)
    E_new = []
    C_new = []
    G_new = []
    shifted_gain = shift(state.G[letter], cap)
    zero = tuple([0] * cap)
    for target in range(len(state.C)):
        if target == letter:
            E_new.append(shift(state.C[letter], cap))
            C_new.append(state.C[letter])
            G_new.append(zero)
        else:
            E_new.append(state.E[target])
            C_new.append(add(state.C[target], state.G[letter], cap=cap))
            G_new.append(add(state.G[target], shifted_gain, cap=cap))
    return FrontierState(A_new, tuple(E_new), tuple(C_new), tuple(G_new))


def state_for_word(word: Word, alphabet_size: int, cap: int | None = None) -> FrontierState:
    cap = cap if cap is not None else len(word) + 2
    state = initial_state(alphabet_size, cap)
    for letter in word:
        state = append_state(state, letter)
    return state


def walk_frontier_states(
    alphabet_size: int, max_length: int, extra_degree: int = 1
) -> Iterator[tuple[Word, FrontierState]]:
    """Traverse reduced words in deterministic prefix-lexicographic order."""

    cap = max_length + extra_degree + 1

    def visit(word: Word, state: FrontierState) -> Iterator[tuple[Word, FrontierState]]:
        yield word, state
        if len(word) == max_length:
            return
        for letter in range(alphabet_size):
            if word and word[-1] == letter:
                continue
            yield from visit(word + (letter,), append_state(state, letter))

    yield from visit((), initial_state(alphabet_size, cap))


def continuation_set(word: Word, forbidden: frozenset[int], cap: int) -> Polynomial:
    subwords = distinct_reduced_subwords(word)
    selected = (u for u in subwords if not u or u[-1] not in forbidden)
    return count_by_degree(selected, cap)


def alternating_delete(word: Word, x: int, z: int) -> Word:
    """Delete the first letter of the maximal nonempty {x,z}-suffix."""

    if not word or word[-1] != x or x == z:
        raise ValueError("alternating_delete requires a word ending in x and x != z")
    start = len(word) - 1
    while start > 0 and word[start - 1] in (x, z):
        start -= 1
    return word[:start] + word[start + 1 :]


def alternating_inverse(image: Word, x: int, z: int) -> Word:
    """Reconstruct the source of alternating_delete from an image word."""

    start = len(image)
    while start > 0 and image[start - 1] in (x, z):
        start -= 1
    if start == len(image):
        return image + (x,)
    first = image[start]
    inserted = z if first == x else x
    return image[:start] + (inserted,) + image[start:]


def format_word(word: Word) -> str:
    return "epsilon" if not word else "".join(str(letter + 1) for letter in word)


def all_forbidden_sets(alphabet_size: int) -> list[frozenset[int]]:
    return [
        frozenset(combo)
        for size in range(alphabet_size + 1)
        for combo in combinations(range(alphabet_size), size)
    ]


def write_json(path: str | None, payload: Dict[str, object]) -> None:
    if path is None:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def base_summary(check: str) -> Dict[str, object]:
    return {
        "check": check,
        "counted_objects": "distinct reduced scattered words, not embeddings",
        "integer_arithmetic": "exact",
        "python_version": sys.version.split()[0],
    }
