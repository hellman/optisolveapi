import logging

log = logging.getLogger(__name__)


class classproperty(object):
    # https://stackoverflow.com/a/5192374
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)


class SolverBase:
    BY_SOLVER = NotImplemented  # to be defined in the collection class
    DEFAULT_PREFERENCE = ()
    _DEFAULT_SOLVER = None
    AVAILABLE = True

    @classproperty
    def DEFAULT_SOLVER(cls):
        if not cls._DEFAULT_SOLVER:
            for name in cls.DEFAULT_PREFERENCE:
                if name in cls.BY_SOLVER:
                    log.info(f"chose preferred solver {name}")
                    cls._DEFAULT_SOLVER = name
                    return name
                log.warning(f"missing preferred solver {name}")
        return cls._DEFAULT_SOLVER

    @classmethod
    def register(cls, name):
        def deco(subcls):
            if not subcls.AVAILABLE:
                log.warning(
                    f"skipping unavailable solver {name}({subcls.__name__}) in class {cls.__name__} "
                )
                return subcls
            if name in cls.BY_SOLVER:
                log.warning(
                    f"re-registering solver {name} in class {cls.__name__} with {subcls.__name__}"
                )
            cls.BY_SOLVER[name.lower()] = subcls
            return subcls
        return deco

    @classmethod
    def new(cls, *args, solver=None, **opts):
        if solver is None:
            solver = cls.DEFAULT_SOLVER
        if solver is None:
            raise RuntimeError(f"Default solver for {cls.__name__} is not specified.")
        return cls.BY_SOLVER[solver.lower()](
            *args,
            solver=solver,
            **opts
        )
