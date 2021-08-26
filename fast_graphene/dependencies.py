from asyncio import create_task, Event, gather, LifoQueue
from copy import copy
from inspect import (
    isasyncgenfunction,
    iscoroutinefunction,
    isfunction,
    isgeneratorfunction,
)
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Set

from graphene import types as gpt

from .annot_compiler import AnnotCompiler
from .errors import FastGrapheneException
from .param_collector import collect_params
from .utils import SetDict


class Empty:
    pass


# Will be used later.
class Dependency:
    def __init__(
        self,
        func: Callable,
        dependencies_map: Optional[Dict[str, "Dependency"]] = None,
        arguments: Optional[Dict[str, gpt.Argument]] = None,
        return_type: Optional[Any] = None,
    ):
        self.func: Callable = func
        # TODO: Let to collect params, dependencies and arguments at once.
        self.func = func
        self.is_async_func = iscoroutinefunction(func)
        self.is_async_gen = isasyncgenfunction(func)
        # TODO: Support for async generator
        # Async generator dependency makes deadlock.
        # When it makes deadlock, its type is coroutine.
        # Figure out why, async generator's type is coroutine on runtime
        if self.is_async_gen:
            raise ValueError("Async generator dependency is not supported currently.")
        self.is_sync_func = isfunction(func)
        self.is_generator = isgeneratorfunction(func)
        if not any(
            (
                self.is_async_func,
                self.is_async_func,
                self.is_sync_func,
                self.is_generator,
            )
        ):
            raise FastGrapheneException  # Invalidone
        self.dependencies_map = dependencies_map or {}
        self.dependencies = list(self.dependencies_map.values())
        self.arguments = arguments or {}
        self.return_type = return_type

    def __eq__(self, other) -> bool:
        if not isinstance(other, Dependency):
            return NotImplemented
        return self.func is other.func

    def __hash__(self):
        return hash(self.func)

    def __repr__(self):
        return f"<Dependency uses {self.func}>"

    def __call__(
        self,
        parent: Any,
        info: gpt.ResolveInfo,
        args: Dict[str, Any],
        channel: "DependencyChannel",
    ):
        return self._call(parent, info, args, channel)

    async def _call(
        self,
        parent: Any,
        info: gpt.ResolveInfo,
        args: Dict[str, Any],
        channel: "DependencyChannel",
    ):
        if self.dependencies:
            dep_results = await gather(
                *[channel.get(dep) for dep in self.dependencies], return_exceptions=True
            )
        else:
            dep_results = []

        result = self.func(
            parent, info, **args, **dict(zip(self.dependencies_map.keys(), dep_results))
        )
        if self.is_async_func or self.is_async_gen:
            return await result
        else:
            return result


class DependencyChannel:
    def __init__(
        self,
        dependencies: List[Dependency],
        parent: Optional[Any] = None,
        *,
        info: gpt.ResolveInfo,
        **kwargs,
    ):
        self.dependencies = dependencies
        self.results = {dependency: Empty for dependency in dependencies}
        self.events = {dependency: Event() for dependency in dependencies}
        self.generator_stack: LifoQueue = LifoQueue()
        self.parent = parent
        self.info = info
        self.kwargs = kwargs

    async def _execute(self, dependency: Dependency):
        if dependency.is_async_func:
            data = await dependency(self.parent, self.info, self.kwargs, self)
        elif dependency.is_async_gen:
            gen = dependency(self.parent, self.info, self.kwargs, self)
            data = await gen.__anext__()
            self.generator_stack.put(gen)
        elif dependency.is_sync_func:
            data = dependency(self.parent, self.info, self.kwargs, self)
        elif dependency.is_generator:
            gen = dependency(self.parent, self.info, self.kwargs, self)
            data = next(gen)
            self.generator_stack.put(gen)

        self.results[dependency] = data
        self.events[dependency].set()

    async def get(self, dependency: Dependency):
        if not self.events[dependency].is_set():
            task = create_task(self._execute(dependency))
            await self.events[dependency].wait()

            await task
            if exception := task.exception():
                raise exception

        return self.results[dependency]

    async def release(self):
        while not self.generator_stack.empty():
            gen = await self.generator_stack.get()
            if gen.is_async_gen:
                await gen
            else:
                next(gen)


class DependencyBuildResult(NamedTuple):
    dependency: Dependency
    flated_dependencies: Set[Dependency]
    flated_arguments: SetDict


def build_dependency_tree(
    root_depend: Callable, annot_compiler: Optional[AnnotCompiler] = None
) -> DependencyBuildResult:
    annot_compiler = annot_compiler or AnnotCompiler()
    flated_dependencies = set()
    flated_arguments = SetDict()  # TODO: Check if arugment used in duplicate.

    def traverse(func, accum_dependencies: set):
        args, dep_funcs, _ = collect_params(func)
        flated_arguments.update(args)

        dependencies_map = {}
        for name, dfn in dep_funcs.items():
            added_set = copy(accum_dependencies)
            added_set.add(dfn)
            dependency = traverse(dfn, added_set)
            dependencies_map[name] = dependency
            flated_dependencies.add(dependency)

        return Dependency(func, arguments=args, dependencies_map=dependencies_map)

    return DependencyBuildResult(
        dependency=traverse(root_depend, set()),
        flated_dependencies=flated_dependencies,
        flated_arguments=flated_arguments,
    )
