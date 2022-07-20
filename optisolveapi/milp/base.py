import logging
from collections import namedtuple

from optisolveapi.solver_base import SolverBase

log = logging.getLogger(__name__)


class MILP(SolverBase):
    """
    Less nice but more efficient syntax for constraints.

    Example:
        .add_constraint({x1: 2, x2: 3}, lb=3)
        2*x1 + 3*x2 >= 3
    """
    BY_SOLVER = {}

    DEFAULT_PREFERENCE = (
        "swiglpk",
        "scip",
        "gurobi",
        "sage/glpk",
    )

    EPS = 1e-9
    debug = 0
    err = None

    @classmethod
    def maximization(cls, *args, solver=None, **opts):
        if not solver:
            solver = cls.DEFAULT_SOLVER
        log.info(f"MILP maximization with solver '{solver}'")

        assert cls is MILP
        return cls.BY_SOLVER[solver.lower()](
            *args,
            maximization=True, solver=solver,
            **opts
        )

    @classmethod
    def minimization(cls, *args, solver=None, **opts):
        if not solver:
            solver = cls.DEFAULT_SOLVER
        log.info(f"MILP minimization with solver '{solver}'")

        assert cls is MILP
        return cls.BY_SOLVER[solver.lower()](
            *args,
            maximization=False, solver=solver,
            **opts
        )

    @classmethod
    def feasibility(cls, *args, solver=None, **opts):
        if not solver:
            solver = cls.DEFAULT_SOLVER
        log.info(f"MILP feasibility with solver '{solver}'")

        assert cls is MILP
        return cls.BY_SOLVER[solver.lower()](
            *args,
            maximization=None, solver=solver,
            **opts
        )

    def trunc(self, v):
        r = round(v)
        if abs(r - v) < self.EPS:
            return int(r)
        else:
            return v

    def write_lp(self, filename):
        self.model.write_lp(filename)

    # ======================================

    def __init__(self, maximization, solver):
        self.maximization = maximization
        self.solver = solver

        self._constraint_id = 10**6
        self.constraints = {}
        self.vars = {}

    VarInfo = namedtuple("VarInfo", ("name", "typ"))

    def _var(self, *args, **kwargs):
        return self.VarInfo(*args, **kwargs)

    def set_var_bounds(self, var, lb=None, ub=None):
        raise NotImplementedError

    def var_int(self, name, lb=None, ub=None):
        assert name not in self.vars
        v = self.vars[name] = self._var(name=name, typ="I")
        self.set_var_bounds(name, lb, ub)
        return v

    def var_real(self, name, lb=None, ub=None):
        assert name not in self.vars
        v = self.vars[name] = self._var(name=name, typ="C")
        self.set_var_bounds(name, lb, ub)
        return v

    def var_binary(self, name):
        assert name not in self.vars
        v = self.vars[name] = self._var(name=name, typ="B")
        return v

    def add_constraint_kw(self, lb=None, ub=None, **coefs: dict[str, float]):
        """
        2*x1 -10*x2 >= 10
        model.add_constraint_kw(x1=2, x2=-10, lb=10)
        """
        return self.add_constraint(coefs.items(), lb=lb, ub=ub)

    def add_constraint_dict(self, coefs: dict[str, float], lb=None, ub=None):
        """
        2*x1 -10*x2 >= 10
        model.add_constraint_kw({x1: 2, x2: -10}, lb=10)
        """
        return self.add_constraint(coefs.items(), lb=lb, ub=ub)

    def add_constraint(self, coefs: list[(str, float)], lb=None, ub=None):
        """
        2*x1 -10*x2 >= 10
        model.add_constraint([("x1", 2), ("x2", -10)], lb=10)
        """
        raise NotImplementedError

    def remove_constraint(self, c):
        raise NotImplementedError

    def remove_constraints(self, cs: tuple):
        raise NotImplementedError

    def set_objective_kw(self, **coefs: dict[str, float]):
        return self.set_objective(coefs.items())

    def set_objective_dict(self, coefs: dict[str, float]):
        return self.set_objective(coefs.items())

    def set_objective(self, coefs: list[(str, float)]):
        raise NotImplementedError

    def optimize(self, solution_limit=1, log=None, only_best=True):
        raise NotImplementedError
