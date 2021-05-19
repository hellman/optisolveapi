from io import BytesIO
from tempfile import NamedTemporaryFile

from .base import CNF


@CNF.register("formula")
class Formula(CNF):
    def init_solver(self, solver):
        assert solver == "formula"
        self.clauses = []

    def add_clause(self, c):
        self.n_clauses += 1
        self.clauses.append(c)

    def add_clauses(self, cs):
        self.n_clauses += len(cs)
        self.clauses.extend(cs)

    def write_dimacs(self, filename, assumptions=(), extra_clauses=()):
        cnf = self._solver
        if assumptions or extra_clauses:
            cnf = self._solver.copy()
            if assumptions:
                for v in assumptions:
                    cnf.append([v])
            if extra_clauses:
                cnf.extend(extra_clauses)
        cnf.to_file(filename)

    def apply(self, inp, cnf):
        assert self.nvars == 1 + len(inp)
        assert self.clauses[0] == [-self.ZERO]
        for c in self.clauses[1:]:
            cnf.add_clause([inp[i-2] for i in c])


@CNF.register("writer")
class Writer(CNF):
    def init_solver(self, solver):
        self._file = BytesIO()
        # self._file.write(b"p cnf 0 0\n")
        self._solver = None

    def add_clause(self, c):
        self.n_clauses += 1
        self._file.write(b" ".join(b"%d" % v for v in c))
        self._file.write(b" 0\n")

    def add_clauses(self, cs):
        for c in cs:
            self.add_clause(c)

    def write_dimacs(self, filename, assumptions=(), extra_clauses=()):
        with open(filename, "wb") as f:
            n_clauses = self.n_clauses + len(assumptions) + len(extra_clauses)
            n_vars = self.n_vars
            f.write(b"p cnf %d %d\n" % (n_vars, n_clauses))

            f.write(self._file.getbuffer())

            if assumptions:
                for v in assumptions:
                    f.write(b"%d 0\n" % v)
            if extra_clauses:
                for c in extra_clauses:
                    f.write(b" ".join(b"%d" % v for v in c))
                    f.write(b" 0\n")

    def set_solver(self, solver):
        self._solver = solver

    def solve(self, assumptions=(), extra_clauses=(), log=True):
        assert self._solver, "solver not set"
        with NamedTemporaryFile() as f:
            self.write_dimacs(
                f.name,
                assumptions=assumptions,
                extra_clauses=extra_clauses,
            )
            return self._solver.solve_file(filename=f.name, log=log)
