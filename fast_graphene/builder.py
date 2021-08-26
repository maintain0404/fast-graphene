from asyncio import create_task, gather
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
from inspect import signature
from typing import Any, Callable, Dict, Iterable, Optional, Type, Union

from graphene import types as gpt
from graphql.execution.base import ResolveInfo

from fast_graphene.dependencies import Dependency, DependencyChannel

from .annot_compiler import AnnotCompiler
from .param_collector import collect_params, pick_used_params_only
from .types import ContextEnum
from .utils import SetDict

DEFAULT_SCALAR_MAP = {
    int: gpt.Int,
    float: gpt.Float,
    str: gpt.String,
    Decimal: gpt.Decimal,
    date: gpt.Date,
    datetime: gpt.DateTime,
    bool: gpt.Boolean,
}


def resolver_builder(
    func: Callable,
    used_arg_names: Iterable[str],
    used_dependency_names: Iterable[str],
    dependencies: Dict[str, Dependency],
):
    @wraps(func)
    async def resolver(parent: Any, info: ResolveInfo, **kwargs):
        channel = DependencyChannel(dependencies.values(), parent, info, **kwargs)
        args_to_use = pick_used_params_only(used_arg_names, kwargs)

        # To prevent leaf dependency called first.
        dependencies_to_use = pick_used_params_only(used_dependency_names, dependencies)
        # 디펜던시 실행
        gatherd = await gather(
            (
                dependency(
                    parent,
                    info,
                    pick_used_params_only(dependency.arguments, kwargs),
                    channel=channel,
                )
                for dependency in dependencies_to_use.values()
            )
        )  # 제너레이터 해제
        release = create_task(channel.release())
        resolved_dependencies = dict(zip(dependencies_to_use.keys(), gatherd))
        result = func(parent, info, **args_to_use, **resolved_dependencies)
        await release
        return result

    return resolver


# TODO: This is not invalid. Fix with build_dependency_tree
class Builder:
    def __init__(
        self,
        # TODO: Add later
        # include_parent: bool = True,
        # include_info: bool = True,
        annot_map=None,
        subcls_annot_map=None,
    ):
        # TODO: Add later
        # self.include_parent: bool = include_parent
        # self.include_info: bool = include_info
        self.annot_compiler = AnnotCompiler(annot_map, subcls_annot_map)

    def compile_type_hint(self, hint, context=None):
        return self.annot_compiler.compile(hint, context=context)

    def field(
        self,
        func: Optional[Callable] = None,
        *,
        default_value: Optional[Any] = None,
        extra_args: Dict[str, gpt.Argument] = None,
        return_type: Union[None, Type[gpt.Scalar], Type[gpt.ObjectType]] = None,
        description: Optional[str] = None,
        deprecation_reason: Optional[str] = None,
    ):
        def inner(func: Callable):
            # 시그니처 따기
            sig = signature(func)
            params = sig.parameters

            nonlocal default_value
            nonlocal extra_args
            extra_args = extra_args or {}
            args = SetDict()
            # TODO: Implement dependency.
            dependencies = set()

            # Set graphene Field type(=return_type).
            nonlocal return_type
            if not return_type:
                return_type = self.annot_compiler.compile(
                    sig.return_annotation, ContextEnum.FIELD
                )

            param_cnt = 0
            # Check with params.
            args, depend_ons, return_type = collect_params(
                func, annot_compiler=self.annot_compiler
            )

            args.update(extra_args)
            return gpt.Field(
                return_type,
                args=args,
                resolver=func,
                default_value=default_value,
                description=description,
                deprecation_reason=deprecation_reason,
            )

        if func:
            return inner(func)
        else:
            return inner
