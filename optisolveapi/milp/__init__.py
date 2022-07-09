from .base import MILP

# from .gurobi import has_gurobi
# from .scip import has_scip
# from .sage import has_sage
from .swiglpk import has_swiglpk
# from . import external

MILP.decide_default_solver()
