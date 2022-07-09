import logging

log = logging.getLogger(__name__)


class SolverBase:
    BY_SOLVER = NotImplemented  # to be defined in the collection class
    DEFAULT_PREFERENCE = ()
    DEFAULT_SOLVER = None

    @classmethod
    def decide_default_solver(cls):
        for name in cls.DEFAULT_PREFERENCE:
            if name in cls.BY_SOLVER:
                log.info(f"chose preferred solver {name}")
                cls.DEFAULT_SOLVER = name
                return name
            log.warning(f"missing preferred solver {name}")

    @classmethod
    def register(cls, name):
        def deco(subcls):
            if name in cls.BY_SOLVER:
                log.warning(
                    f"re-registering solver {name} in class {cls.__name__}"
                )
            cls.BY_SOLVER[name.lower()] = subcls
            return subcls
        return deco

    @classmethod
    def new(cls, *args, solver, **opts):
        return cls.BY_SOLVER[solver.lower()](
            *args,
            solver=solver,
            **opts
        )
