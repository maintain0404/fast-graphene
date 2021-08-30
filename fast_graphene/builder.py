from asyncio import create_task, gather
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
from inspect import signature
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Set, Type, Union

from graphene import types as gpt
from graphql.execution.base import ResolveInfo

from fast_graphene.dependencies import (
    build_dependency_tree,
    Dependency,
    DependencyChannel,
)

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


def build_resolver(
    func: Callable,
    used_arg_names: Iterable[str],
    used_dependency_map: Mapping[str, Dependency],
    dependencies: Set[Dependency],
):
    @wraps(func)
    async def resolver(parent: Any, info: ResolveInfo, **kwargs):
        channel = DependencyChannel(dependencies, parent, info=info, **kwargs)
        args_to_use = pick_used_params_only(used_arg_names, kwargs)

        # execute dependencies
        dependency_results = await gather(
            *(
                dependency(
                    parent,
                    info,
                    pick_used_params_only(dependency.arguments, kwargs),
                    channel=channel,
                )
                for dependency in used_dependency_map.values()
            )
        )  # release generators.
        release_task = create_task(channel.release())
        resolved_dependencies = dict(
            zip(used_dependency_map.keys(), dependency_results)
        )
        result = func(parent, info, **args_to_use, **resolved_dependencies)
        await release_task
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
            sig = signature(func)

            nonlocal default_value
            nonlocal extra_args
            extra_args = extra_args or {}
            args = SetDict()
            # TODO: Implement dependency.
            direct_dependencies = dict()
            all_dependencies = set()

            # Set graphene Field type(=return_type).
            nonlocal return_type
            if not return_type:
                return_type = self.annot_compiler.compile(
                    sig.return_annotation, ContextEnum.FIELD
                )

            # Check with params.
            args, depend_ons, return_type = collect_params(
                func, annot_compiler=self.annot_compiler
            )
            used_arg_names = args.keys()
            for name, depend_on in depend_ons.items():
                build_result = build_dependency_tree(depend_on, self.annot_compiler)
                dependency_args, dependency, flatted_dependencies = (
                    build_result.flated_arguments,
                    build_result.dependency,
                    build_result.flated_dependencies,
                )

                args.update(dependency_args)
                all_dependencies = all_dependencies | flatted_dependencies
                direct_dependencies[name] = dependency

            resolver = build_resolver(
                func,
                used_arg_names=used_arg_names,
                used_dependency_map=direct_dependencies,
                dependencies=all_dependencies,
            )

            args.update(extra_args)
            return gpt.Field(
                return_type,
                args=args,
                resolver=resolver,
                default_value=default_value,
                description=description,
                deprecation_reason=deprecation_reason,
            )

        if func:
            return inner(func)
        else:
            return inner
