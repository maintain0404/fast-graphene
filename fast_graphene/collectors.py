import inspect
from typing import Callable
from typing import GenericAlias
from typing import List
from typing import Mapping
from typing import Tuple

from graphene.types import Argument

from .dependencies import Dependency


def type_hint_mapper(hint: GenericAlias):
    pass


def compile_type_hint(hint: GenericAlias):
    chain = []
    if hint.__origin__ is (list or List):
        pass


def collect_params(
    func: Callable,
) -> Tuple[Mapping[str, Argument], Mapping[str, Dependency]]:
    sig = inspect.signature(func)
    arguments = {}
    dependencies = {}
    for kw, param in sig.parameters.items():
        if isinstance(param.default, Argument):
            arguments[kw] = param.default
        elif isinstance(param.default, Dependency):
            dependencies[kw] = param.default
        # TODO: Collect Params with hint
    return arguments, dependencies
