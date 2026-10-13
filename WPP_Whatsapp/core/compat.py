"""Flatten the old layer API onto a facade; services share an operation context."""


def install_compatibility(target, base):
    for layer in base.__mro__:
        if layer is object:
            continue
        for name, value in vars(layer).items():
            if name.startswith("__") or name in vars(target):
                continue
            if callable(value) or isinstance(value, (staticmethod, classmethod, property)):
                setattr(target, name, value)
