# Examples in the Second Draft

Run all four numerical computations in Examples 5.1–5.3:

```console
python code/verify_examples.py --output data/example_checks.json
```

| Example | Computation |
|---|---|
| 5.1 | `abc` and `bac` have the same rank polynomial, but appending `a` gives rank polynomials differing by `t^2+t^3`. |
| 5.2 | For `ababa`, distinct reduced-word counts are `(1,2,2,2,2,1)`; embedding counts are `(1,5,6,5,2,1)`. |
| 5.3, first part | For `ababac`, the gain in direction `b` has coefficients `(0,0,1,2,2,3,3,1)` and fails log-concavity at degree 4. |
| 5.3, second part | For `ab`, the diagonal sum in direction `a` has coefficients `(1,1,2,1)` and fails log-concavity at degree 1. |

The same script verifies the factorized defect identity (3.5) by expanding
both sides as polynomials in five independent integer-coefficient variables.

The two original commands remain available for the parts of Example 5.3:

```console
python code/verify_append_gain_failure.py
python code/verify_diagonal_transfer_failure.py
```

Their output paths `data/example_6_1.json` and `data/example_6_2.json`
retain the numbering used in the first draft.
