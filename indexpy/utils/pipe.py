from itertools import chain
from functools import partial as _partial


class partial(_partial):
    def __call__(self, *args, **keywords):
        args_iter = iter(args)
        return self.func(
            *chain(
                (next(args_iter) if arg == ... else arg for arg in self.args),
                args_iter,
            ),
            **{**self.keywords, **keywords}
        )


class F(partial):
    def __ror__(self, other):
        return self(other)


class FF(partial):
    def __ror__(self, other):
        return self(*other)
