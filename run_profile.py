#!/usr/bin/env python

from cProfile import Profile
import pstats
from liar.formula import Formula, Neg, Or, Var

N = 1000

# fs = [Formula.random(10,10) for _ in range(N)]

A, B = Var.generate(2)
f = A | B

with Profile() as pr:
    f == A

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.TIME)
stats.print_stats()
stats.dump_stats(filename="profile.prof")
