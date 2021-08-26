from .builder import Builder
from .param_collector import DependOn

_DEFAULT_BUILDER = Builder()

field = _DEFAULT_BUILDER.field
resolver = _DEFAULT_BUILDER.resolver
mutation = _DEFAULT_BUILDER.mutation

__all__ = [
    "Builder",
    "DependOn",
    "field",
    "resolver",
    "mutation",
]
