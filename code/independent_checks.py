#!/usr/bin/env python3
"""Independent checks for Rank Log-Concavity in Universal Coxeter Groups.

Small words: enumerate position subsets, reject adjacent equal letters, then
deduplicate resulting label words. Large words: count paths in the deterministic
earliest-embedding automaton. Neither counter uses the manuscript's terminal
slice/gain recurrence. Recurrences are checked only after independent counting.
The default run reproduces Section 5.2 of the second draft. Finite checks are
evidence, not proofs. Run from the repository root:

    python code/independent_checks.py --output data/independent_checks.json

The first failure in each check family is recorded. The requested run continues
and exits with nonzero status if any check failed.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import random
import time
from pathlib import Path


class State:
    def __init__(self, word, alphabet_size, ending):
        self.word = tuple(word)
        self.n = len(word)
        self.r = alphabet_size
        self.E = [list(row) + [0, 0, 0] for row in ending]
        self.A = [sum(row[k] for row in self.E) for k in range(self.n + 4)]
        self.A[0] = 1
        self.C = [[self.A[k] - row[k] for k in range(self.n + 4)]
                  for row in self.E]
        self.G = [[(row[k-1] if k else 0) - self.E[x][k]
                   for k in range(self.n + 4)] for x, row in enumerate(self.C)]

    def set_continuation(self, mask):
        row = [sum(self.E[y][k] for y in range(self.r) if not mask & (1 << y))
               for k in range(self.n + 4)]
        row[0] = 1
        return row


def by_position_subsets(word, r, return_words=False):
    """Enumerate all 2^n position subsets and deduplicate resulting reduced words."""
    n = len(word)
    found = {()}
    for mask in range(1, 1 << n):
        value = []
        previous = -1
        rest = mask
        valid = True
        while rest:
            bit = rest & -rest
            letter = word[bit.bit_length() - 1]
            if letter == previous:
                valid = False
                break
            value.append(letter)
            previous = letter
            rest -= bit
        if valid:
            found.add(tuple(value))
    ending = [[0] * (n + 1) for _ in range(r)]
    for value in found:
        if value:
            ending[value[-1]][len(value)] += 1
    state = State(word, r, ending)
    return (state, found) if return_words else state


def by_earliest_embedding_automaton(word, r):
    """Each distinct reduced label word has a unique deterministic DAG path.

    State i is the earliest endpoint (position, 1-based). A transition with
    label x goes to the first occurrence of x after i, excluding x equal to
    the previous label. Paths of length k are accumulated at each position.
    """
    n = len(word)
    next_position = [[-1] * r for _ in range(n + 1)]
    following = [-1] * r
    for i in range(n, -1, -1):
        next_position[i] = following.copy()
        if i:
            following[word[i-1]] = i
    paths = [[0] * (i + 1) for i in range(n + 1)]
    paths[0][0] = 1
    for i in range(n + 1):
        previous = word[i-1] if i else -1
        for label, j in enumerate(next_position[i]):
            if j == -1 or label == previous:
                continue
            target = paths[j]
            for k, count in enumerate(paths[i]):
                if count:
                    target[k+1] += count
    ending = [[0] * (n + 1) for _ in range(r)]
    for i in range(1, n + 1):
        for k, count in enumerate(paths[i]):
            ending[word[i-1]][k] += count
    return State(word, r, ending)


def at(row, k):
    return row[k] if 0 <= k < len(row) else 0


def bracket(p, q, k):
    return at(p, k)*at(q, k-1) - at(p, k-1)*at(q, k)


class Audit:
    def __init__(self, profile='full'):
        self.counts = collections.Counter()
        self.failures = {}
        self.notes = []
        self.profile = profile

    def check(self, key, value, word, **detail):
        self.counts[key] += 1
        if not value and key not in self.failures:
            self.failures[key] = {'word': list(word), **detail}
            print('FAILURE', key, self.failures[key], flush=True)

    def state(self, s, all_sets=True, explicit_words=None):
        w, n, r = s.word, s.n, s.r
        for x, row in enumerate([s.A] + s.C):
            self.check('rank_and_continuation_LC',
                       all(row[k]**2 >= row[k-1]*row[k+1] for k in range(1, n+2)),
                       w, polynomial=('A' if x == 0 else f'C^{x-1}'), coefficients=row)
            support = [k for k, c in enumerate(row) if c]
            self.check('rank_and_continuation_interval_support',
                       support == list(range(max(support)+1)), w, polynomial=x)
        for x in range(r):
            self.check('append_gain_nonnegative', min(s.G[x]) >= 0, w, x=x, G=s.G[x])
            if w:
                z = w[-1]
                self.check('last_letter_ratio_minimum',
                           all(bracket(s.C[x], s.C[z], k) >= 0 for k in range(n+3)),
                           w, x=x, z=z, Cx=s.C[x], Cz=s.C[z])
                self.check('last_letter_coefficient_minimum',
                           all(a >= b for a, b in zip(s.C[x], s.C[z])), w, x=x, z=z)
            for y in range(r):
                self.check('continuation_ending_crossing',
                           all(at(s.C[x],k-1)*at(s.E[y],k-1) >=
                               at(s.C[x],k-2)*at(s.E[y],k)
                               for k in range(-1,n+4)), w, x=x, y=y)
                if x != y:
                    self.check('alternating_suffix_surplus_nonnegative',
                               all(at(s.C[y],k-1) >= at(s.E[x],k) for k in range(n+3)),
                               w, x=x, z=y)
                    Y = [at(s.C[y],k) + at(s.C[y],k-1) - at(s.E[x],k)
                         for k in range(n+4)]
                    self.check('all_formal_left_half_sandwiches',
                               all(bracket(Y,s.C[y],k) >= 0 for k in range(n+3)),
                               w, x=x, z=y)
                    self.check('all_formal_right_half_sandwiches',
                               all(at(s.C[y],k)*at(Y,k) >= at(s.C[y],k-1)*at(Y,k+1)
                                   for k in range(n+3)), w, x=x, z=y)
                    # The algebraic identities remain valid even for an illegal append.
                    pair = s.set_continuation((1 << x)|(1 << y))
                    self.check('two_letter_cancellation_identity',
                               all(at(s.C[y],k)*at(Y,k) - at(s.C[y],k-1)*at(Y,k+1) ==
                                   at(s.C[y],k)*at(pair,k) - at(s.C[y],k-1)*at(pair,k+1)
                                   for k in range(n+3)), w, x=x, z=y)
                    M, F = s.C[y], s.E[x]
                    self.check('monotone_deficit_ratio',
                               all(at(F,k)*at(M,k-2) <= at(F,k-1)*at(M,k-1)
                                   for k in range(2,n+3)), w, x=x, z=y)
                    self.check('monotone_deficit_expansion',
                               all(bracket(Y,M,k) ==
                                   at(M,k-1)**2 - at(M,k-1)*at(F,k) -
                                   at(M,k-2)*at(M,k) + at(M,k)*at(F,k-1)
                                   for k in range(n+3)), w, x=x, z=y)
        masks = range(1 << r) if all_sets else sorted({0, (1 << r)-1} |
                    {1 << x for x in range(r)} |
                    {(1 << x)|(1 << y) for x in range(r) for y in range(r)})
        for mask in masks:
            row = s.set_continuation(mask)
            for x in range(r):
                self.check('singleton_set_interlacing',
                           all(at(s.C[x],k-1)*at(row,k-1) >=
                               at(s.C[x],k-2)*at(row,k) for k in range(-1,n+4)),
                           w, singleton=x, forbidden_mask=mask)
        if w:
            z = w[-1]
            for y in range(r):
                if y == z:
                    continue
                for x in range(r):
                    if x == y:
                        continue
                    self.check('conjecture_previous_letter_extremality',
                               all(bracket(s.C[y],s.C[x],k) <= bracket(s.C[y],s.C[z],k)
                                   for k in range(n+3)), w, x=x,y=y,z=z)
                self.check('adjacent_step_compensation',
                           all(bracket(s.C[y],s.C[z],k) <= bracket(s.G[y],s.C[y],k)
                               for k in range(n+3)),w,y=y,z=z)
        if explicit_words is not None:
            for x in range(r):
                last = max((i for i,a in enumerate(w,1) if a==x),default=-1)
                tail = [0]*(n+4)
                for value in explicit_words:
                    if value and value[-1] == x:
                        continue
                    endpoint = 0
                    for letter in value:
                        endpoint = w.index(letter,endpoint)+1
                    if endpoint > last:
                        tail[len(value)+1] += 1
                self.check('greedy_tail_gain_identity',tail==s.G[x],w,x=x)
            for x,y in itertools.permutations(range(r),2):
                domain = [v for v in explicit_words if v and v[-1] == x]
                images = []
                for value in domain:
                    begin=len(value)-1
                    while begin and value[begin-1] in (x,y):
                        begin-=1
                    out=value[:begin]+value[begin+1:]
                    images.append(out)
                    self.check('alternating_deletion_image_membership',
                               out in explicit_words and (not out or out[-1]!=y),w,
                               x=x,z=y,input_word=value,output_word=out)
                self.check('alternating_deletion_injective',len(set(images))==len(images),
                           w,x=x,z=y)

    def edge(self, old, new):
        w, r, z = new.word, new.r, new.word[-1]
        self.check('terminal_split_total_rank_recurrence',
                   all(at(new.A,k)==at(old.C[z],k)+at(old.C[z],k-1)
                       for k in range(new.n+3)),w)
        for x in range(r):
            self.check('terminal_ending_recurrence',
                       all(at(new.E[x],k)==(at(old.C[z],k-1) if x==z else at(old.E[x],k))
                           for k in range(new.n+3)),w,x=x)
            self.check('append_continuation_recurrence',
                       all(at(new.C[x],k)==at(old.C[x],k)+(at(old.G[z],k) if x!=z else 0)
                           for k in range(new.n+3)),w,x=x)
            self.check('append_gain_recurrence',
                       all(at(new.G[x],k)==(at(old.G[x],k)+at(old.G[z],k-1) if x!=z else 0)
                           for k in range(new.n+3)),w,x=x)
            if x!=z:
                self.check('transfer_surplus_decomposition',
                           all(at(new.C[x],k)==at(old.C[z],k)+at(old.C[z],k-1)-at(old.E[x],k)
                               for k in range(new.n+3)),w,x=x,z=z)

    def finish(self, coverage, start, output, *, complete=False):
        result = {'profile':self.profile,'complete':complete,
                  'coverage':coverage,'assertion_counts':dict(self.counts),
                  'first_failures':self.failures,'notes':self.notes,
                  'elapsed_seconds':round(time.time()-start,2),
                  'warning':'Finite computations are not a proof.'}
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',
                               encoding='utf-8')
        print(json.dumps({'check_families':len(self.counts),
                          'aggregate_assertions':sum(self.counts.values()),
                          'failure_families':list(self.failures),
                          'elapsed_seconds':result['elapsed_seconds']},ensure_ascii=False),flush=True)
        return result


def reduced_words(r,n):
    if n==0:
        yield ()
        return
    for prefix in reduced_words(r,n-1):
        for x in range(r):
            if not prefix or prefix[-1]!=x:
                yield prefix+(x,)


def random_reduced(r,n,rng):
    word=[]
    for _ in range(n):
        letters=[x for x in range(r) if not word or x!=word[-1]]
        word.append(rng.choice(letters))
    return tuple(word)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',
                        help='JSON path (default: data/independent_checks.json for full runs; '
                             '.verification-output/independent_checks.<profile>.json otherwise)')
    parser.add_argument('--quick',action='store_true',
                        help='Use smaller exhaustive and random ranges; retain all four structured words')
    parser.add_argument('--large-only',action='store_true',
                        help='Skip exhaustive small words and run only random and structured automaton checks')
    args=parser.parse_args()
    start=time.time()
    profile = ('quick-large-only' if args.quick else 'large-only') if args.large_only else (
        'quick' if args.quick else 'full')
    if args.output is None:
        args.output = ('data/independent_checks.json' if profile == 'full' else
                       f'.verification-output/independent_checks.{profile}.json')
    audit=Audit(profile=profile)
    coverage={'small_exhaustive':[],'large_automaton':[],'random_seed':20261019}
    if not args.large_only:
        limits=((3,7),(4,6)) if args.quick else ((3,10),(4,8))
        for r,limit in limits:
            previous={}
            total=0
            for n in range(limit+1):
                current={}
                for w in reduced_words(r,n):
                    s,found=by_position_subsets(w,r,return_words=True)
                    # Check all subset masks/individual words for n <= 6.
                    audit.state(s,explicit_words=found if n<=6 else None)
                    if w:
                        audit.edge(previous[w[:-1]],s)
                    if n<=6:
                        independent=by_earliest_embedding_automaton(w,r)
                        audit.check('subset_vs_automaton_count_agreement',
                                    independent.E==s.E,w,r=r)
                    current[w]=s
                    total+=1
                previous=current
                print(f'exhaustive U{r}, length {n}: {len(current)} words; '
                      f'failures={list(audit.failures)}',flush=True)
            coverage['small_exhaustive'].append({'rank':r,'maximum_length':limit,
                                                'all_reduced_words_including_empty':total})
            audit.finish(coverage,start,args.output)
    rng=random.Random(20261019)
    specs=((3,30,4),(4,30,4)) if args.quick else ((2,1000,3),(3,120,50),
             (3,300,12),(4,120,50),(4,300,12),(5,150,12),(6,100,12))
    for r,n,count in specs:
        for i in range(count):
            w=random_reduced(r,n,rng)
            s=by_earliest_embedding_automaton(w,r)
            audit.state(s,all_sets=(r<=6))
            old=by_earliest_embedding_automaton(w[:-1],r)
            audit.edge(old,s)
        coverage['large_automaton'].append({'rank':r,'length':n,'word_count':count})
        print(f'automaton U{r}, length {n}, count {count}; failures={list(audit.failures)}',flush=True)
        audit.finish(coverage,start,args.output)
    # Structured words separately stress repeated and changing periodic blocks.
    structured=[(3,tuple(([0,1,2]*40)+([1,2,0]*40)+([2,0,1]*40))),
                (3,tuple(([0,1]*100)+([2,0,2,1]*50))),
                (4,tuple(([0,1,2,3]*75))),
                (4,tuple(([0,1]*50)+([2,3]*50)+([0,2]*50)))]
    coverage['structured_automaton']=[]
    for r,w in structured:
        assert all(w[i]!=w[i+1] for i in range(len(w)-1))
        s=by_earliest_embedding_automaton(w,r)
        audit.state(s)
        audit.edge(by_earliest_embedding_automaton(w[:-1],r),s)
        coverage['structured_automaton'].append({'rank':r,'length':len(w),'word':list(w)})
    audit.notes.append('Adjacent-Step Compensation is already a consequence of the stated last-letter ratio minimum: specialize its comparison letter to the previous last letter.')
    audit.finish(coverage,start,args.output,complete=True)
    return 1 if audit.failures else 0


if __name__=='__main__':
    raise SystemExit(main())
