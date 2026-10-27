#!/usr/bin/env python3
"""Reproduce Examples 5.1--5.3 and the defect identity (3.5).

These are the four computations in the examples of Rank Log-Concavity in
Universal Coxeter Groups (second draft).

Counting uses the independent position-subset enumerator in
independent_checks.py. Symbolic verification uses exact multivariate integer
polynomials, with no external dependencies. Only the small examples are run.

Run from the repository root:
    python code/verify_examples.py --output data/example_checks.json
Any failed check raises AssertionError and exits with nonzero status.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from independent_checks import by_position_subsets


def require(condition, message):
    """Do not rely on assert statements, which Python's -O option disables."""
    if not condition:
        raise AssertionError(message)


def trim(sequence):
    result = list(sequence)
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result


def state(word):
    return by_position_subsets(tuple('abc'.index(letter) for letter in word), 3)


def reduced_embedding_counts(word):
    counts = [0] * (len(word) + 1)
    for mask in range(1 << len(word)):
        selected = tuple(word[i] for i in range(len(word)) if mask & (1 << i))
        if all(selected[i] != selected[i + 1] for i in range(len(selected) - 1)):
            counts[len(selected)] += 1
    return counts


def example_checks():
    ababa = state('ababa')
    ababac = state('ababac')
    ab = state('ab')
    abc = state('abc')
    bac = state('bac')
    abca = state('abca')
    baca = state('baca')
    embeddings = reduced_embedding_counts('ababa')
    diagonal = trim([a + b for a, b in zip(ab.C[0], ab.G[0])])
    examples = {
        'ababa_distinct_vs_embeddings': {
            'word': 'ababa',
            'distinct_reduced_word_coefficients': trim(ababa.A),
            'reduced_position_embedding_coefficients': embeddings,
            'embedding_LC_failure_degree': 4,
            'embedding_LC_defect': embeddings[4] ** 2 - embeddings[3] * embeddings[5],
        },
        'ababac_gain': {
            'word': 'ababac',
            'append_letter': 'b',
            'gain_coefficients': trim(ababac.G[1]),
            'gain_LC_failure_degree': 4,
            'gain_LC_defect': ababac.G[1][4] ** 2 - ababac.G[1][3] * ababac.G[1][5],
        },
        'ab_diagonal_sum': {
            'word': 'ab',
            'letter': 'a',
            'continuation_coefficients': trim(ab.C[0]),
            'gain_coefficients': trim(ab.G[0]),
            'diagonal_sum_coefficients': diagonal,
            'diagonal_sum_LC_failure_degree': 1,
            'diagonal_sum_LC_defect': diagonal[1] ** 2 - diagonal[0] * diagonal[2],
        },
        'abc_bac_same_rank_different_continuation': {
            'words': ['abc', 'bac'],
            'append_letter': 'a',
            'A_abc_coefficients': trim(abc.A),
            'A_bac_coefficients': trim(bac.A),
            'C_abc_a_coefficients': trim(abc.C[0]),
            'C_bac_a_coefficients': trim(bac.C[0]),
            'A_abca_coefficients': trim(abca.A),
            'A_baca_coefficients': trim(baca.A),
            'A_abca_minus_A_baca_coefficients': trim([a - b for a, b in zip(abca.A, baca.A)]),
        },
    }
    expected = {
        ('ababa_distinct_vs_embeddings', 'distinct_reduced_word_coefficients'): [1, 2, 2, 2, 2, 1],
        ('ababa_distinct_vs_embeddings', 'reduced_position_embedding_coefficients'): [1, 5, 6, 5, 2, 1],
        ('ababa_distinct_vs_embeddings', 'embedding_LC_defect'): -1,
        ('ababac_gain', 'gain_coefficients'): [0, 0, 1, 2, 2, 3, 3, 1],
        ('ababac_gain', 'gain_LC_defect'): -2,
        ('ab_diagonal_sum', 'continuation_coefficients'): [1, 1, 1],
        ('ab_diagonal_sum', 'gain_coefficients'): [0, 0, 1, 1],
        ('ab_diagonal_sum', 'diagonal_sum_coefficients'): [1, 1, 2, 1],
        ('ab_diagonal_sum', 'diagonal_sum_LC_defect'): -1,
        ('abc_bac_same_rank_different_continuation', 'A_abc_coefficients'): [1, 3, 3, 1],
        ('abc_bac_same_rank_different_continuation', 'A_bac_coefficients'): [1, 3, 3, 1],
        ('abc_bac_same_rank_different_continuation', 'C_abc_a_coefficients'): [1, 2, 3, 1],
        ('abc_bac_same_rank_different_continuation', 'C_bac_a_coefficients'): [1, 2, 2, 1],
        ('abc_bac_same_rank_different_continuation', 'A_abca_coefficients'): [1, 3, 5, 4, 1],
        ('abc_bac_same_rank_different_continuation', 'A_baca_coefficients'): [1, 3, 4, 3, 1],
        ('abc_bac_same_rank_different_continuation', 'A_abca_minus_A_baca_coefficients'): [0, 0, 1, 1],
    }
    for (example, field), value in expected.items():
        require(examples[example][field] == value, f'Failed example: {example}.{field}')
    return examples


VARIABLE_NAMES = ['M_k_minus_2', 'M_k_minus_1', 'M_k', 'F_k_minus_1', 'F_k']


def variable(index):
    monomial = [0] * len(VARIABLE_NAMES)
    monomial[index] = 1
    return {tuple(monomial): 1}


def add(*polynomials):
    result = Counter()
    for polynomial in polynomials:
        for monomial, coefficient in polynomial.items():
            result[monomial] += coefficient
    return {monomial: coefficient for monomial, coefficient in result.items() if coefficient}


def negate(polynomial):
    return {monomial: -coefficient for monomial, coefficient in polynomial.items()}


def multiply(left, right):
    result = Counter()
    for monomial_left, coefficient_left in left.items():
        for monomial_right, coefficient_right in right.items():
            monomial = tuple(a + b for a, b in zip(monomial_left, monomial_right))
            result[monomial] += coefficient_left * coefficient_right
    return {monomial: coefficient for monomial, coefficient in result.items() if coefficient}


def serialize_polynomial(polynomial):
    return [
        {
            'powers': {name: exponent for name, exponent in zip(VARIABLE_NAMES, monomial) if exponent},
            'coefficient': coefficient,
        }
        for monomial, coefficient in sorted(polynomial.items())
    ]


def symbolic_identity_check():
    a, b, c, d, e = [variable(i) for i in range(5)]
    y_k = add(c, b, negate(e))
    y_k_minus_1 = add(b, a, negate(d))
    defect = add(multiply(y_k, b), negate(multiply(y_k_minus_1, c)))
    lhs = multiply(b, defect)
    rhs = add(
        multiply(add(multiply(b, b), negate(multiply(a, c))), add(b, negate(e))),
        multiply(c, add(multiply(b, d), negate(multiply(a, e)))),
    )
    residual = add(lhs, negate(rhs))
    require(not residual, 'The symbolic nonnegative-defect identity has a nonzero residual.')
    # Check the common expansion against its explicit four expected monomials.
    expected_expansion = {
        (0, 3, 0, 0, 0): 1,
        (0, 2, 0, 0, 1): -1,
        (1, 1, 1, 0, 0): -1,
        (0, 1, 1, 1, 0): 1,
    }
    require(lhs == expected_expansion, 'The common symbolic expansion is unexpected.')
    return {
        'method': 'Exact independent expansion in the polynomial ring Z[M_(k-2),M_(k-1),M_k,F_(k-1),F_k], implemented as integer coefficient dictionaries.',
        'lhs': 'M_(k-1)*(((M_k+M_(k-1)-F_k)*M_(k-1))-((M_(k-1)+M_(k-2)-F_(k-1))*M_k))',
        'rhs': '(M_(k-1)^2-M_(k-2)*M_k)*(M_(k-1)-F_k)+M_k*(M_(k-1)*F_(k-1)-M_(k-2)*F_k)',
        'lhs_expansion': serialize_polynomial(lhs),
        'rhs_expansion': serialize_polynomial(rhs),
        'lhs_minus_rhs': serialize_polynomial(residual),
        'identity_holds_identically': True,
        'scope': 'The equality holds for arbitrary values of the five scalar parameters, independently of the inequalities used to prove nonnegativity.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='data/example_checks.json',
                        help='JSON result path (default: data/example_checks.json)')
    args = parser.parse_args()
    result = {
        'source': 'Rank Log-Concavity in Universal Coxeter Groups (second draft), Examples 5.1--5.3 and equation (3.5)',
        'counting_method': 'Enumerate position subsets, reject selected words with adjacent equal letters, and deduplicate reduced label words; embeddings retain multiplicity.',
        'examples': example_checks(),
        'symbolic_nonnegative_defect_identity': symbolic_identity_check(),
        'all_checks_passed': True,
        'notes': [
            'The four computations reproduce Examples 5.1--5.3 of the second draft.',
            'The symbolic expansion checks equation (3.5).',
            'Reproduce with python code/verify_examples.py; any failed check raises an exception and exits with nonzero status.',
        ],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                           encoding='utf-8')
    print(json.dumps({'examples_checked': len(result['examples']),
                      'symbolic_identity_holds_identically': True,
                      'all_checks_passed': True,
                      'output': args.output}, ensure_ascii=False))


if __name__ == '__main__':
    main()
