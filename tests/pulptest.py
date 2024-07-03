from time import time
from random import sample, randrange, seed
ss = randrange(2**128)
print("seed", ss)
seed(ss)
#import gurobipy

solver, mysolver = "glpk", "swiglpk"
#solver, mysolver = "gurobi", "swiglpk"
#solver, mysolver = "scip", "scip"
#solver, mysolver = "gurobi_direct_v2", "gurobi"
# solver, mysolver = "gurobi_v2", "gurobi"
#solver, mysolver = "gurobi", "gurobi"

from optisolveapi.milp import MILP
# model = MILP.minimization(solver=mysolver)

V = 1000
Cv = int(0.9 * V)
C = 200

# V = 20
# Cv = int(0.9 * V)
# C = 10

CS = [
    [randrange(-10, 10) for _ in range(Cv + 1)]
    for _ in range(C + 1)
]
VS = [
    sample(list(range(V)), Cv)
    for _ in range(C + 1)
]

print("solver", repr(solver))

# ======================================

t0 = time()
import pyomo.environ as pyo
import pyomo.kernel as pmo
print("pyo import 0", time() -t0)


t0 = time()
model = pyo.ConcreteModel()
print("pyo import 1", time() -t0)

t00 = t0 = time()
model = pyo.ConcreteModel()

model.x = pyo.Var(range(V), domain=pyo.Binary)
xs = list(model.x.values())

model.OBJ = pyo.Objective(expr = pyo.summation(model.x))

print("pyo T1:", time() - t0)
print()

t0 = time()
for j in range(C):
    cs = CS[j][:-1]
    lb = CS[j][-1]
    vs = [xs[j] for j in VS[j]]
    #model += mip.xsum(c*v for c, v in zip(vs, cs)) >= randrange(10)
    #print(cs)
    #print(vs)
    setattr(
        model,
        "Constraint%d" % j,
        pyo.Constraint(expr=pyo.quicksum(v*c for v, c in zip(vs, cs)) >= lb)
        # pyo.Constraint(expr=pyo.sum_product(vs, cs, index=list(range(len(vs)))) >= randrange(10))
    )

print("pyo T2 (constr):", time() - t0)

t0 = time()
opt = pyo.SolverFactory(solver)
print("pyo T3:", time() - t0)

t0 = time()
res = None
try:
    res = opt.solve(model)
except RuntimeError as err:
    print("err", err)
print("res", res)
print("pyo T4 (solve):", time() - t0)

t0 = time()
j = C
cs = CS[j][:-1]
lb = CS[j][-1]
vs = [xs[j] for j in VS[j]]
# setattr(
#     model,
#     "Constraint%d" % j,
#     pyo.Constraint(expr=pyo.quicksum(v*c for v, c in zip(vs, cs)) >= lb)
# )
try:
    res = opt.solve(model)
except RuntimeError as err:
    print("err", err)
print("res", res)
print("pyo T5 (increm):", time() - t0)

print("pyo total", time() - t00)
print()

# ======================================

if 0:
    # MIP does not have GLPK
    # also slowish
    # supports pypy for gurobi though
    t0 = time()
    import mip
    mip.Model(sense=mip.MINIMIZE, solver_name=solver.upper())
    print("import", time() -t0)

    for _ in range(1):
        t0 = time()
        model = mip.Model(sense=mip.MINIMIZE, solver_name=solver)

        xs = [
            model.add_var(name="x%d" % i, var_type=mip.BINARY)
            for i in range(V)
        ]

        t00 = time()

        #model.set_objective((v, 1) for v in xs)
        model.objective = mip.xsum(xs)
        print("MIP T1:", time() - t0)

        t0 = time()
        for j in range(C):
            t = Cv
            cs = [randrange(-10, 10) for _ in range(t)]
            vs = sample(xs, t)
            model += mip.xsum(c*v for c, v in zip(vs, cs)) >= randrange(10)
            #model.add_constraint(zip(vs, cs), lb=randrange(10))

        print("MIP T2 const:", time() - t0)

        t0 = time()
        model.optimize()
        print("MIP T3 solve:", time() - t0)
        print("MIP total:", time() - t00)
        print()
        print()
        print()

# ======================================


if 0:
    from pulp import *
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

    # throwing the problem to the solver takes a lot...
    # also: non-incremental..
    prob.solve(GLPK(msg = 0))
    print("PuLP T3:", time() - t0)

print()

# ======================================


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
    print()

# ======================================

from optisolveapi.milp import MILP

t00 = t0 = time()
model = MILP.minimization(solver=mysolver)

xs = [
    model.var_binary("x%d" % i)
    for i in range(V)
]

model.set_objective((v, 1) for v in xs)
print("OPTI T1:", time() - t0)

t0 = time()
for j in range(C):
    cs = CS[j][:-1]
    lb = CS[j][-1]
    vs = [xs[j] for j in VS[j]]
    model.add_constraint(zip(vs, cs), lb=lb)

print("OPTI T2 (const):", time() - t0)

t0 = time()
res = model.optimize()
print("res", res)
# print([cs[-1] for cs in CS])
# print(model.solutions)
print("OPTI T3 (solve):", time() - t0)

t0  =time()
j = C
cs = CS[j][:-1]
lb = CS[j][-1]
vs = [xs[j] for j in VS[j]]
# model.add_constraint(zip(vs, cs), lb=lb)
res = model.optimize()
print("OPTI T4 (increm)", time() - t0)

print("OPTI total:", time() - t00)

'''
V = 1000
C = 1000
Cv = 200

PuLP T1: 0.2424466609954834
PuLP T2: 11.888185501098633 !!!
OPTI T1: 0.004148006439208984
OPTI T2: 0.45085763931274414
'''
