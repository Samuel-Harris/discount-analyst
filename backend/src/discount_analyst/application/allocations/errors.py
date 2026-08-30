"""Errors raised while assembling Curator input from completed lanes."""


class AllocationAssemblyError(ValueError):
    """Lane evidence and the current-position snapshot cannot be combined."""
