import logging
from itertools import product

try:
    from pysat.solvers import Solver, SolverNames
    has_pysat = True
except ImportError:
    has_pysat = False

from .base import CNF

if has_pysat:
    class PySAT(CNF):
        log = logging.getLogger(f"{__name__}.PySAT")

        def __init__(self, solver):
            if not has_pysat:
                raise ImportError("PySAT not found")
            assert solver.startswith("pysat/")
            pysat_solver = solver[len("pysat/"):]
            self._solver = Solver(name=pysat_solver)

            super().__init__(solver=solver)

        def model_to_sol(self, model):
            res = {(i+1): int(v > 0) for i, v in enumerate(model)}
            added = self.n_vars - len(model)
            for i in range(len(model), self.n_vars):
                assert (i+1) not in res
                res[i+1] = 0
            if added:
                self.log.debug(f"set {added} free vars to 0")
            return res

        def model_to_sols(self, model):
            res = {(i+1): int(v > 0) for i, v in enumerate(model)}
            if self.n_vars > len(res):
                for vals in product(range(2), repeat=self.n_vars - len(model)):
                    for i, v in zip(range(len(model), self.n_vars), vals):
                        res[i+1] = v
                    yield res.copy()
            else:
                yield res

        def solve(self, assumptions=()):
            sol = self._solver.solve(assumptions=assumptions)
            if sol is None or sol is False:
                return False
            model = self._solver.get_model()
            return self.model_to_sol(model)

        def solve_all(self, assumptions=()):
            sol = self._solver.solve(assumptions=assumptions)
            if sol is None or sol is False:
                return
            for model in self._solver.enum_models():
                yield from self.model_to_sols(model)
            # pysat spoils the model after enum_models() ...
            # clear up to ensure no surprises
            self._solver.delete()
            del self._solver

        def __del__(self):
            if hasattr(self, "_solver") and self._solver:
                self._solver.delete()

    # seems pysat has no API for listing solvers
    # for now, getting them out manually
    for name, aliases in SolverNames.__dict__.items():
        if name[0] != "_":
            aliases_str = " ".join(f"pysat/{alias}" for alias in aliases)
            PySAT.log.debug(f"found solver {name} with aliases {aliases_str}")
            for alias in aliases:
                CNF.register(f"pysat/{alias}")(PySAT)

else:
    PySAT = None
