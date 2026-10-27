# Machine-Readable Results

## Current Second Draft

- `independent_checks.json`: the full independent audit in Section 5.2,
  with exhaustive ranges, random seed and sample specifications, structured
  words, check counts, and first failures. A completed run has `profile: "full"`
  and `complete: true`.
- `example_checks.json`: four computations from Examples 5.1–5.3 and the
  exact symbolic verification of equation (3.5).

Regenerate these files from the repository root:

```console
python code/independent_checks.py --output data/independent_checks.json
python code/verify_examples.py --output data/example_checks.json
```

The independent audit's quick and large-only profiles have smaller or
partial coverage. Keep their output separate from the committed full run.

## Extended Regressions and Compatible Filenames

The remaining summaries use the recurrence-based ranges retained from the
first draft. The root README gives their reproduction commands.

| File | Current correspondence |
|---|---|
| `main_invariants.json` | Theorem 1.1 and recurrence validation |
| `alternating_suffix_injection.json` | Lemma 2.3 |
| `half_sandwich.json` | Corollary 4.2 and the paths in Section 4.2 |
| `transfer_polynomials.json` | Corollary 4.3 |
| `previous_letter_extremality.json` | Conjecture 5.4 and the previous-terminal specialization of proved equation (5.2) |
| `section7_conjectures.json` | Compatibility copy of `previous_letter_extremality.json` |
| `example_6_1.json` | The append-gain calculation in Example 5.3 |
| `example_6_2.json` | The diagonal-sum calculation in Example 5.3 |

Full recurrence profiles are named `extended`. The preserved filenames
with `6_1`, `6_2`, or `section7` do not refer to the current numbering.
When regenerating `previous_letter_extremality.json`, update its
`section7_conjectures.json` compatibility copy as well.

Stored Python versions identify the runs that produced the numerical
results. A documentation update does not change that provenance. Compare
reproductions by coverage, check counts, and results; elapsed time and
Python version can vary.
