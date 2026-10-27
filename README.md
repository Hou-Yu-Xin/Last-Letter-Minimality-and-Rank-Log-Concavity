# Rank Log-Concavity in Universal Coxeter Groups

Computational material for the second draft of **Rank Log-Concavity in
Universal Coxeter Groups**, by Hou Yuxin. The correspondence below follows
the manuscript dated October 19, 2026, with its October 27 prose revisions.
The repository retains its original name and URL.

The paper proves that every principal Bruhat interval `[e,w]` in a universal
Coxeter group has a log-concave rank sequence. The programs check its
recurrences, inequalities, examples, and the remaining previous-letter
extremality conjecture using exact integer arithmetic.

Counts refer to distinct reduced scattered words. Example 5.2 also counts
position embeddings to compare the two counting conventions.

## Requirements

- Python 3.11 or later, in standard mode: some verifiers use `assert` and
  therefore reject `python -O`.
- No third-party Python packages.

Run the following commands from the repository root.

## Reproduce the Second Draft

```console
python code/verify_examples.py --output data/example_checks.json
python code/independent_checks.py --output data/independent_checks.json
```

`verify_examples.py` reproduces Examples 5.1–5.3 (four numerical
computations) and verifies the polynomial identity (3.5) by exact symbolic
expansion.

`independent_checks.py` implements two counters: position-subset enumeration
with deduplication, and path counting in the earliest-embedding automaton.
Neither counter uses the terminal or append-gain recurrences being checked.

The full run reproduces Section 5.2:

| Check | Coverage |
|---|---:|
| All reduced words in rank 3 through length 10, including the empty word | 3,070 |
| All reduced words in rank 4 through length 8, including the empty word | 13,121 |
| Agreement of both counters through length 6 in those two ranks | 1,647 |
| Random samples in ranks 2–6, lengths 100–1,000 | 151 |
| Structured words of lengths 300, 300, 360, and 400 | 4 |

The random seed is `20261019`; repeated samples are allowed. The JSON records
the exact sample specifications, the four structured words, and counts for
24 check families. Explicit alternating-deletion and greedy-endpoint word
checks use exhaustive inputs of length at most six; larger inputs test the
coefficient identities and inequalities.

For a shorter run:

```console
python code/independent_checks.py --quick --output .verification-output/independent_checks.quick.json
```

The quick profile reduces the exhaustive ranges and random samples, while
retaining the four structured words. Partial profiles use separate default
output paths so that they do not overwrite the full summary.

## Correspondence With the Paper

| Current location | Checked object | Program |
|---|---|---|
| Theorem 1.1; Lemmas 2.1–2.2 | Rank and continuation log-concavity, last-letter minimum, terminal recurrences, support | `independent_checks.py`, `verify_main_invariants.py` |
| Lemma 2.3 | Alternating-suffix deletion and injectivity | `independent_checks.py`, `verify_alternating_suffix_injection.py` |
| Lemma 3.2, equation (3.5) | Factorized defect identity | `verify_examples.py` |
| Corollaries 4.1–4.2 | Continuation–ending and continuation-set inequalities; append sandwich | `independent_checks.py`, `verify_half_sandwich.py` |
| Corollary 4.3; Section 4.2 | Off-diagonal transfer log-concavity; return and open paths | `verify_transfer_polynomials.py`, `verify_half_sandwich.py` |
| Examples 5.1–5.3 | Equal rank polynomials with different appends; embeddings; gain and diagonal failures | `verify_examples.py` |
| Conjecture 5.4 | Previous-letter extremality | `independent_checks.py`, `verify_previous_letter_extremality.py` |
| Equation (5.2) | Proved compensation inequality, tested at the previous terminal letter | `independent_checks.py`, `verify_previous_letter_extremality.py` |
| Equation (5.4) | Greedy-endpoint description of append gain | `independent_checks.py` |

Previous-letter extremality remains conjectural. Compensation in equation
(5.2) follows from Theorem 1.1(i). The numerical checks supplement these
statements; finite computation is not a proof of the conjecture.

## Extended Regressions

The original recurrence-based regressions remain available. Their larger
ranges come from the first draft and are additional to the independent
checks in the current Section 5.2.

```console
python code/verify_append_gain_failure.py --output data/example_6_1.json
python code/verify_diagonal_transfer_failure.py --output data/example_6_2.json
python code/verify_alternating_suffix_injection.py --output data/alternating_suffix_injection.json
python code/verify_half_sandwich.py --output data/half_sandwich.json
python code/verify_main_invariants.py --output data/main_invariants.json
python code/verify_transfer_polynomials.py --output data/transfer_polynomials.json
python code/verify_previous_letter_extremality.py --output data/previous_letter_extremality.json
```

| Extended check | Full-range total |
|---|---:|
| Alternating-suffix source instances | 2,346 |
| Instances for each structural half-sandwich identity | 2,304 |
| Words in the main-invariant regression | 1,006,729 |
| Previous-letter comparisons | 10,088,798 |
| Previous-terminal maximizer events | 2,548,760 |
| Previous-terminal compensation checks | 2,548,760 |

The four large scripts accept `--quick`. For example:

```console
python code/verify_half_sandwich.py --quick
python code/verify_main_invariants.py --quick
python code/verify_transfer_polynomials.py --quick
python code/verify_previous_letter_extremality.py --quick
```

The earlier command `verify_section7_conjectures.py` is a compatibility
entry point for `verify_previous_letter_extremality.py`. The old data
filenames `example_6_1.json` and `example_6_2.json` now both correspond to
Example 5.3; `section7_conjectures.json` is a compatibility copy of
`previous_letter_extremality.json`.

## Results and Automated Checks

Result files are described in [data/README.md](data/README.md); the numerical
examples are listed in [examples/README.md](examples/README.md).

The independent audit records the first failure in each check family,
finishes the requested run, and exits with a nonzero status if a check
failed. Its final JSON has `complete: true`; intermediate checkpoints have
`complete: false`. The other verifiers stop on a failed check.

Coverage, counts, and mathematical results are reproducible. Runtime and
Python-version metadata can differ between machines.

The [verification workflow](.github/workflows/verify.yml) reruns the full
independent audit and examples, compares them with the stored results,
and runs the smaller profiles of the extended regressions on pushes and
pull requests that change the verification material.
