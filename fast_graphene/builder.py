from asyncio import create_task, gather, get_running_loop
from datetime import date, datetime
from decimal import Decimal
from functools import partial, wraps
from inspect import iscoroutinefunction, signature
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Type, Union

from graphene import types as gpt

from fast_graphene.dependencies import Dependency, DependencyChannel

from .annot_compiler import AnnotCompiler
from .param_collector import interpret_params, pick_used_params_only
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


def compile_func(
    func: Callable,
    used_arg_names: Iterable[str],
    used_dependency_names: Iterable[str],
    dependencies: Dict[str, Dependency],
):
    if not iscoroutinefunction(func):
        loop = get_running_loop()
        executor = partial(loop.run_in_executor, None, func)
    else:
        executor = func

    @wraps(func)
    async def compiled_func(parent: Any, info: gpt.ResolveInfo, **kwargs):
        channel = DependencyChannel(dependencies.values(), parent, info=info, **kwargs)
        args_to_use = pick_used_params_only(used_arg_names, kwargs)

        # To prevent leaf dependency called first.
        dependencies_to_use = pick_used_params_only(used_dependency_names, dependencies)

        # Execute Dependencies
        gatherd = await gather(
            *[
                dependency(
                    parent,
                    info,
                    pick_used_params_only(dependency.arguments.keys(), kwargs),
                    channel=channel,
                )
                for dependency in dependencies_to_use.values()
            ]
        )

        # Release generators.
        release = create_task(channel.release())
        resolved_dependencies = dict(zip(dependencies_to_use.keys(), gatherd))
        result = await executor(parent, info, **args_to_use, **resolved_dependencies)
        await release
        return result

    return compiled_func


class Builder:
    def __init__(
        self,
        annot_map=None,
        subcls_annot_map=None,
    ):
        self.annot_compiler = AnnotCompiler(annot_map, subcls_annot_map)

    def resolver(
        self,
        func: Optional[Callable] = None,
    ) -> Callable:
        def inner(func):
            compiled_func, _ = self._compile_func(func)
            return compiled_func

        if func:
            return inner(func)
        else:
            return inner

    mutation = resolver  # noqa

    def _compile_func(
        self, func: Callable, extra_args: Optional[Dict[str, gpt.Argument]] = None
    ) -> Tuple[Callable, Dict[str, gpt.Argument]]:
        extra_args = extra_args or {}

        args, depend_ons = interpret_params(func, annot_compiler=self.annot_compiler)
        compiled_func = compile_func(
            func, args.keys(), set(depend_ons.values()), depend_ons
        )
        args = SetDict(args)
        args.update(extra_args)

        return compiled_func, args

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

            compiled_func, args = self._compile_func(func, extra_args=extra_args)

            # Set graphene Field type(=return_type).
            nonlocal return_type
            if not return_type:
                return_type = self.annot_compiler.compile(
                    sig.return_annotation, ContextEnum.FIELD
                )

            return gpt.Field(
                return_type,
                args=args,
                resolver=compiled_func,
                default_value=default_value,
                description=description,
                deprecation_reason=deprecation_reason,
            )

        if func:
            return inner(func)
        else:
            return inner
