try:
    import gurobipy as gp
    from gurobipy import GRB
    has_gurobi = True
except ImportError:
    has_gurobi = False

from .base import MILP

if has_gurobi:
    import logging
    # disable duplicate logging
    # although this prevents from logging to .log...
    logging.getLogger("gurobipy").setLevel(logging.WARNING)


TYPE_MAP = dict(
    R=GRB.CONTINUOUS,
    C=GRB.CONTINUOUS,
    I=GRB.INTEGER,
    B=GRB.BINARY,
)

@MILP.register("gurobi")
class Gurobi(MILP):
    def __init__(self, maximization, solver):
        super().__init__(maximization, solver)
        assert has_gurobi

        self.model = gp.Model()
        self.model.setParam("OutputFlag", 0)
        # self.model.setParam("OutputFile", "")
        # self.model.setParam("LogToConsole", 1)
        # self.model.setParam("LogFile", "/dev/null")

    @staticmethod
    def _lin_expr(coefs: list[(str, float)]):
        return gp.LinExpr([
            (b, a) for a, b in coefs
        ])

    def _var(self, name, typ):
        assert typ in "RCIB", typ
        v = self.model.addVar(name=name, vtype=typ)
        return v

    def set_var_bounds(self, var, lb: float = None, ub: float = None):
        if lb is not None:
            var.setAttr("lb", lb)
        if lb is not None:
            var.setAttr("ub", ub)

    def add_constraint(self, coefs: list[(str, float)], lb=None, ub=None):
        expr = self._lin_expr(coefs)
        if lb is None or ub is None:
            if lb is not None:
                return self.model.addConstr(expr >= lb)
            if ub is not None:
                return self.model.addConstr(expr <= ub)
            raise ValueError("no lb and ub?")

        return (
            self.model.addConstr(expr >= lb),
            self.model.addConstr(expr <= ub),
        )

    def remove_constraint(self, c):
        return self.model.remove(c)

    def remove_constraints(self, cs):
        for c in cs:
            return self.model.remove(c)

    def set_objective(self, coefs):
        obj = self._lin_expr(coefs)
        if self.maximization:
            return self.model.setObjective(obj, GRB.MAXIMIZE)
        else:
            return self.model.setObjective(obj, GRB.MINIMIZE)

    def optimize(self, solution_limit=1, log=None, only_best=True):
        log = 1
        if not log:
            self.model.setParam("LogFile", "")
            self.model.setParam("LogToConsole", 0)
            self.model.setParam("OutputFlag", 0)
        else:
            self.model.setParam("OutputFlag", 1)
            self.model.setParam("LogToConsole", 1)

        if solution_limit <= 1:
            self.model.setParam("PoolSearchMode", 0)
        else:
            self.model.setParam("PoolSearchMode", 2)
            self.model.setParam("PoolSolutions", solution_limit)

        self.solutions = []
        self.model.optimize()
        status = self.model.Status
        if status == GRB.INTERRUPTED:
            raise KeyboardInterrupt("gurobi was interrupted")
        assert status in (GRB.OPTIMAL, GRB.INFEASIBLE), status
        if status == GRB.INFEASIBLE:
            return

        if self.maximization is None:
            obj = True
        else:
            obj = self.trunc(self.model.objVal)

        if solution_limit != 0:
            for i in range(min(solution_limit, self.model.SolCount)):
                self.model.setParam("SolutionNumber", i)

                solobj = self.model.PoolObjVal
                if obj is not True and solobj + self.EPS < obj and only_best:
                    continue

                vec = {v: self.trunc(v.Xn) for v in self.vars.values()}
                self.solutions.append(vec)
        return obj

    def write_lp(self, filename):
        assert filename.endswith(".lp")
        self.model.write(filename)
