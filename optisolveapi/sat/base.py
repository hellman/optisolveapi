import logging

from optisolveapi.vector import Vector
from optisolveapi.solver_base import SolverBase

from .constraints import Constraints


class CNF(SolverBase, Constraints):
    BY_SOLVER = {}
    DEFAULT_PREFERENCE = (
        "pysat/cadical195",
        "pysat/cadical153",
        "ext/kissat",
    )

    log = logging.getLogger("CNF")

    def __init__(self, solver=None):
        if type(self) is CNF:
            raise TypeError("Creation of CNF problems should be done using CNF.new(solver=...)")
        if solver is None:
            raise TypeError("solver not passed")

        self.n_vars = 0
        self.n_clauses = 0
        self.solver = solver

        self.ZERO = self.var()
        self.add_clause([-self.ZERO])
        self.ONE = -self.ZERO

        self.log.info(f"SAT solver '{solver}'")

    def solve(self, assumptions=()):
        raise NotImplementedError()

    def var(self):
        self.n_vars += 1
        return self.n_vars

    def vars(self, n):
        return Vector([self.var() for _ in range(n)])

    def add_clause(self, c):
        self.n_clauses += 1
        self._solver.add_clause(c)

    def add_clauses(self, cs):
        self.n_clauses += len(cs)
        self._solver.append_formula(cs)

    def make_assumption(self, xs, values):
        return [x if bit else -x for x, bit in zip(xs, values)]

    def sol_eval(self, sol, vec):
        return tuple(sol[abs(v)] ^ (1 if v < 0 else 0) for v in vec if v)

    def apply(self, cnf, inp):
        assert cnf.n_vars == 1 + len(inp)
        assert cnf.clauses[0] == [-cnf.ZERO] == [-1]
        mapping = {1: 1, -1: -1}
        # 0 is skipped, 1 is ZERO
        # starting at 2
        for i, v in enumerate(inp):
            i += 2
            mapping[i] = v
            mapping[-i] = -v

        for c in cnf.clauses[1:]:
            self.add_clause([mapping[i] for i in c])
