from typing import Callable

from graphene.types import Field

from .collectors import collect_params
from .dependencies import DependencyTreeVisitor


def fast_graphene(type) -> Field:
    def inner(func: Callable):
        arguments, dependencies = collect_params(func)
        for name, depends in dependencies.items():
            visitor = DependencyTreeVisitor(depends)  # 한 단계 아래에서 순환 참조를 전부 잡을 수 있나?
            if visitor.is_circular:
                raise visitor.error
            arguments.update(visitor.arguments)
        return Field(type, resolver=func, **arguments)

    return inner
