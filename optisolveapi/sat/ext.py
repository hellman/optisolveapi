import logging
import subprocess
import shutil

from .base import CNF

ARG_FLAGS = "<FLAGS>"
ARG_DIMACS = "<DIMACS>"


@CNF.register("ext")
class ExtSolver(CNF):
    BY_SOLVER = {}

    log = logging.getLogger(f"{__name__}:ExtSolver")

    CMD = NotImplemented

    def __init_subclass__(subcls):
        if subcls.CMD is not NotImplemented:
            if not shutil.which(subcls.CMD[0]):
                subcls.log.debug(f"skipping ext solver {subcls.__name__} since command {subcls.CMD[0]} is not available")
                subcls.AVAILABLE = False

    def __init__(self, flags=(), solver=None, command=None):
        if self.CMD is NotImplemented:
            if command is None:
                raise ValueError("command was not passed to ExtSolver")
            if isinstance(command, str):
                self.CMD = [command, ARG_FLAGS, ARG_DIMACS]
            else:
                self.CMD = list(command)

            if not shutil.which(self.CMD[0]):
                raise RuntimeError(f"command {self.CMD[0]} is not available")

        if solver is None:
            solver = f"ext/{self.CMD[0]}"

        self.flags = flags

        super().__init__(solver=solver)

    def solve_file(self, filename, log=True):
        cmd = [filename if v == ARG_DIMACS else v for v in self.CMD]
        pos = cmd.index(ARG_FLAGS)
        cmd[pos:pos+1] = list(self.flags)

        # self.log.info(f"command {cmd}")
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
        )
        ret = None
        sol = []
        while True:
            line = p.stdout.readline()
            if not line:
                break
            if not line.strip():
                continue

            if log:
                self.log.debug(line)
                # print(line)

            if line[:1] == b"s":
                res = line.split()[1]
                if res == b"SATISFIABLE":
                    # self.log.info("SAT")
                    ret = True
                elif res == b"UNSATISFIABLE":
                    # self.log.info("UNSAT")
                    ret = False
                else:
                    raise RuntimeError(f"unknown status {res}")
            elif line[:1] == b"v":
                sol.extend(map(int, line[1:].split()))
            elif line[:1] == b"c":
                pass
            else:
                self.log.warning(f"unknown line type {line[:1]}: {line} ")

        if ret is None:
            raise RuntimeError("Solver did not solve")
        # self.log.debug(f"ret {ret} sol {sol}")
        if ret is True:
            assert len(set(map(abs, sol))) == len(sol)
            assert ret is True
            return {abs(v): int(v > 0) for v in sol}
        return False


@CNF.register("ext/kissat")
class Kissat(ExtSolver):
    CMD = ["kissat", ARG_FLAGS, ARG_DIMACS]
