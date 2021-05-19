
from .simple import Formula


def ConvexFormula(lb=None, ub=None):
    C = Formula()
    C.constraint_convex(lb=lb, ub=ub)
    return C
