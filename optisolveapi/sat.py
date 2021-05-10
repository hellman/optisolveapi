# https://github.com/pysathq/pysat
# pip install python-sat[pblib,aiger]
'''
Available ( https://pysathq.github.io/docs/html/api/solvers.html#list-of-classes ):
    Cadical : CaDiCaL SAT solver
    Glucose3 : Glucose 3 SAT solver
    Glucose4 : Glucose 4.1 SAT solver
    Lingeling : Lingeling SAT solver
    MapleChrono : MapleLCMDistChronoBT SAT solver
    MapleCM : MapleCM SAT solver
    Maplesat : MapleCOMSPS_LRB SAT solver
    Minicard : Minicard SAT solver
    Minisat22 : MiniSat 2.2 SAT solver
    MinisatGH : MiniSat SAT solver (version from github)
'''
from itertools import product
from random import shuffle

try:
    from pysat.solvers import Solver
    has_pysat = True
except ImportError:
    has_pysat = False

from .base import SolverBase
from .vector import Vector

_shuffle = shuffle


class CNF(SolverBase):
    def __init__(self, solver="pysat/cadical"):
        self.init_solver(solver)
        self._var_cnt = 0

        self.ZERO = self.var()
        self.ONE = self.var()
        self.add_clause([-self.ZERO])
        self.add_clause([self.ONE])

    def init_solver(self, solver):
        raise NotImplementedError()

    def solve(self, assumptions=()):
        raise NotImplementedError()

    def var(self):
        self._var_cnt += 1
        return self._var_cnt

    def vars(self, n):
        return Vector([self.var() for _ in range(n)])

    def add_clause(self, c):
        self._solver.add_clause(c)

    def constraint_unary(self, vec):
        for a, b in zip(vec, vec[1:]):
            self.add_clause([a, -b])

    def constraint_and(self, a, b, ab):
        # a=1 b=1 => ab=1
        self.add_clause([-a, -b, ab])
        # a=0 => ab=0
        self.add_clause([a, -ab])
        # b=0 => ab=0
        self.add_clause([b, -ab])

    def constraint_or(self, a, b, ab):
        # a=0 b=0 => ab=0
        self.add_clause([a, b, -ab])
        # a=1 => ab=1
        self.add_clause([-a, ab])
        # b=1 => ab=1
        self.add_clause([-b, ab])

    # def SeqInc(self, vec):
    #     return [self.ONE] + list(vec)

    # def SeqAddConst(self, vec, c):
    #     return [self.ONE] * c + list(vec)

    # def SeqAdd(self, vec1, vec2):
    #     n1 = len(vec1)
    #     n2 = len(vec2)
    #     vec3 = [self.var() for i in range(n1 + n2)]
    #     ands = {}

    #     # self.constraint_unary(vec1)  # optional
    #     # self.constraint_unary(vec2)  # optional
    #     self.constraint_unary(vec3)

    #     for i in range(n1):
    #         ands[i, -1] = vec1[i]
    #         for j in range(n2):
    #             ands[i, j] = self.var()
    #             self.constraint_and(vec1[i], vec2[j], ands[i, j])
    #             ands[-1, j] = vec2[j]

    #     for isum in range(1, n1+n2+1):
    #         clause0 = [-vec3[isum-1]]
    #         for i in range(min(isum + 1, n1 + 1)):
    #             vi = vec1[i-1] if i else 0
    #             j = isum - i
    #             if j > n2:
    #                 continue
    #             vj = vec2[j-1] if j else 0

    #             # vec1[i] = 1, vec2[j] = 1 => vec3[i][isum] = 1
    #             clause = [vec3[isum-1], -vi, -vj]

    #             clause = [c for c in clause if c]
    #             self.add_clause(clause)

    #             clause0.append(ands[i-1, j-1])

    #         # FORALL i, j vec1[i] & vec2[j] = 0 => vec3[i][isum] = 0
    #         clause0 = [c for c in clause0 if c]
    #         self.add_clause(clause0)
    #     return vec3

    # def SeqAddMany(self, *vecs):
    #     lst = list(vecs)
    #     while len(lst) >= 2:
    #         lst2 = []
    #         shuffle(lst)
    #         while len(lst) >= 2:
    #             lst2.append(self.SeqAdd(lst.pop(), lst.pop()))
    #         if lst:
    #             lst2.append(lst.pop())
    #         lst = lst2
    #     return lst[0]

    # def SeqEq(self, vec1, vec2):
    #     if len(vec1) < len(vec2):
    #         self.add_clause([-vec2[len(vec1)]])
    #     elif len(vec2) < len(vec1):
    #         self.add_clause([-vec1[len(vec2)]])
    #     for a, b in zip(vec1, vec2):
    #         self.add_clause([a, -b])
    #         self.add_clause([-a, b])

    # def SeqEqConst(self, vec, c):
    #     assert 0 <= c <= len(vec)
    #     if c == 0:
    #         self.add_clause([-vec[0]])
    #     elif c == len(vec):
    #         self.add_clause([vec[-1]])
    #     else:
    #         self.add_clause(vec[c-1])
    #         self.add_clause(-vec[c])

    def Cardinality(self, vec, lim=None, shuffle=False):
        """
        [Sinz2005]-like cardinality.
        """
        if lim is None:
            lim = len(vec)
        else:
            lim = min(lim, len(vec))

        assert vec
        if len(vec) == 1:
            return list(vec)

        if shuffle:
            vec = list(vec)
            _shuffle(vec)

        sub = self.Cardinality(vec[:-1], lim=lim, shuffle=False)
        res = [self.var() for _ in range(lim)]
        var = vec[-1]

        # res[i] = card >= i+1
        # res[0] = sub[0] | var
        self.constraint_or(sub[0], var, res[0])
        for i in range(1, lim):
            # res[i] = sub[i] | (sub[i-1] & var)
            if len(sub) >= i + 1:
                x0, x1, x2, x3 = sub[i], sub[i-1], var, res[i]

                # Sinz claims that if we encode Cardinality <= k
                # then clauses with -x3 can be dropped.
                # Indeed, this only would allow a bad assignment,
                # but a good one would still exist if and only if card <= k.
                # However, this seems to contradict with his claim
                # that LT_SEQ is decided by unit propagation.
                self.add_clause([x1, -x3])  # full is [x0, x1, -x3] but unarity gives x1 <= x0
                self.add_clause([x0, x2, -x3])
                self.add_clause([-x1, -x2, x3])
                self.add_clause([-x0, x3])
            else:
                assert i == lim - 1
                self.constraint_and(sub[i-1], var, res[i])
        return res

    # def SeqFloor(src, c):
    #     n = len(src)
    #     m = n // c
    #     dst = VarVec(m)
    #     for i in range(0, len(src), n):
    #         sub = src[i:i+c]
    #         if len(sub) != c:
    #             continue
    #         # dst = a & b & c

    #         # dst = 1 => a = 1
    #         # dst = 1 => b = 1
    #         vdst = dst[i//c]
    #         for vsrc in sub:
    #             S.add_clause([-vdst, vsrc])
    #         # dst = 0 => a = 0 v b = 0 v ...
    #         S.add_clause([vdst] + [-vsrc for vsrc in sub])
    #     return dst

    # def SeqCeil(src, c):
    #     n = len(src)
    #     m = (n + c - 1) // c
    #     dst = VarVec(m)
    #     for i in range(0, len(src), n):
    #         sub = src[i:i+c]
    #         # dst = a v b v c

    #         # dst = 0 => a = 0
    #         # dst = 0 => b = 0
    #         vdst = dst[i//c]
    #         for vsrc in sub:
    #             S.add_clause([vdst, -vsrc])
    #         # dst = 1 => a = 1 v b = 1 v ...
    #         S.add_clause([-vdst] + [vsrc for vsrc in sub])
    #     return dst

    # def SeqMultConst(self, src, c):
    #     res = []
    #     for v in src:
    #         res += [v] * c
    #     return res

    # def AlignPad(self, a, b):
    #     n = min(len(a), len(b)) + 1
    #     a = list(a) + [self.ZERO] * (n - len(a))
    #     b = list(b) + [self.ZERO] * (n - len(b))
    #     return a, b

    # def SeqLess(self, a, b):
    #     # 1 0
    #     # 0 0
    #     a, b = self.AlignPad(a, b)
    #     n = len(a)

    #     # Bad (equal):
    #     # 1 0
    #     # 1 0
    #     for i in range(n-1):
    #         self.add_clause([-a[i], -b[i], a[i+1], b[i+1]])

    #     # Bad (greater):
    #     # 1
    #     # 0
    #     for i in range(n):
    #         self.add_clause([-a[i], b[i]])

    # def SeqLessEqual(self, a, b):
    #     # 1 0
    #     # 0 0
    #     a, b = self.AlignPad(a, b)
    #     n = len(a)

    #     # Bad (greater):
    #     # 1
    #     # 0
    #     for i in range(n):
    #         self.add_clause([-a[i], b[i]])

    def constraint_remove_lower(self, x: list, mx: int):
        clause = []
        x = list(x)
        while x:
            xx = x.pop()
            if mx & 1 == 0:
                clause.append(xx)
            mx >>= 1
        assert not mx
        self.add_clause(clause)

    def constraint_remove_upper(self, x: list, mn: int):
        clause = []
        x = list(x)
        while x:
            xx = x.pop()
            if mn & 1 == 1:
                clause.append(-xx)
            mn >>= 1
        assert not mn
        self.add_clause(clause)

    def constraint_convex(self, xs, lb=None, ub=None):
        if lb:
            for mx in lb:
                self.constraint_remove_lower(xs, mx)
        if ub:
            for mn in ub:
                self.constraint_remove_upper(xs, mn)

    def Convex(self, xs, m=None, lb=None, ub=None):
        if m is None:
            m = len(xs)
        ys = self.vars(m)
        self.constraint_convex(Vector(xs).concat(ys), lb=lb, ub=ub)
        return ys

    def make_assumption(self, xs, values):
        return [x if bit else -x for x, bit in zip(xs, values)]


@CNF.register("pysat/cadical")  # CaDiCaL SAT solver
@CNF.register("pysat/glucose3")  # Glucose 3 SAT solver
@CNF.register("pysat/glucose4")  # Glucose 4.1 SAT solver
@CNF.register("pysat/lingeling")  # Lingeling SAT solver
@CNF.register("pysat/maplechrono")  # MapleLCMDistChronoBT SAT solver
@CNF.register("pysat/maplecm")  # MapleCM SAT solver
@CNF.register("pysat/maplesat")  # MapleCOMSPS_LRB SAT solver
@CNF.register("pysat/minicard")  # Minicard SAT solver
@CNF.register("pysat/minisat22")  # MiniSat 2.2 SAT solver
@CNF.register("pysat/minisatgh")  # MiniSat SAT solver (version from github)
class PySAT(CNF):
    def init_solver(self, solver):
        assert has_pysat
        assert solver.startswith("pysat/")
        solver = solver[len("pysat/"):]
        self._solver = Solver(name=solver)

    def model_to_sol(self, model):
        res = {(i+1): int(v > 0) for i, v in enumerate(model)}
        for i in range(len(model), self._var_cnt):
            res[i+1] = 0
        return res

    def model_to_sols(self, model):
        res = {(i+1): int(v > 0) for i, v in enumerate(model)}
        if self._var_cnt > len(res):
            for vals in product(range(2), repeat=self._var_cnt - len(model)):
                for i, v in zip(range(len(model), self._var_cnt), vals):
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

    def sol_eval(self, sol, vec):
        return tuple(sol[abs(v)] ^ (1 if v < 0 else 0) for v in vec)

    def __del__(self):
        self._solver.delete()
