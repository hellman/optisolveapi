from time import time
from random import sample, randrange

V = 1000
C = 1000
Cv = 200


from pulp import *

if 0:
    t0 = time()
    prob = LpProblem("The Whiskas Problem", LpMinimize)

    xs = [
        LpVariable("x%d" % i, upBound=1)
        for i in range(V)
    ]

    prob += sum(xs)
    print("PuLP T1:", time() - t0)

    t0 = time()
    for j in range(C):
        t = Cv
        cs = [randrange(-10, 10) for _ in range(t)]
        vs = sample(xs, t)
        # ineq = sum(c*x for c, x in zip(cs, vs)) >= randrange(10)
        # prob += ineq

    print("PuLP T2:", time() - t0)

# ======================================

t0 = time()
prob = LpProblem("The Whiskas Problem", LpMinimize)

xs = [
    LpVariable("x%d" % i, upBound=1)
    for i in range(V)
]

prob += sum(xs)
print("PuLP T1:", time() - t0)

t0 = time()
for j in range(C):
    t = Cv
    cs = [randrange(-10, 10) for _ in range(t)]
    vs = sample(xs, t)
    # raw API is faster
    # but it only records the system
    # the solver is not even created yet
    ineq = LpConstraint(zip(vs, cs), rhs=randrange(10))
    prob += ineq

print("PuLP T2:", time() - t0)

t0 = time()

# throwing the problem to the solver takes a lot...
# also: non-incremental..
prob.solve(GLPK(msg = 0))
print("PuLP T3:", time() - t0)

# ======================================

from optisolveapi.milp import MILP

t0 = time()
model = MILP.minimization()

xs = [
    model.var_binary("x%d" % i)
    for i in range(V)
]

model.set_objective((v, 1) for v in xs)
print("OPTI T1:", time() - t0)

t0 = time()
for j in range(C):
    t = Cv
    cs = [randrange(-10, 10) for _ in range(t)]
    vs = sample(xs, t)
    model.add_constraint(zip(vs, cs), lb=randrange(10))

print("OPTI T2:", time() - t0)

t0 = time()
model.optimize()
print("OPTI T3:", time() - t0)

'''
V = 1000
C = 1000
Cv = 200

PuLP T1: 0.2424466609954834
PuLP T2: 11.888185501098633 !!!
OPTI T1: 0.004148006439208984
OPTI T2: 0.45085763931274414
'''
