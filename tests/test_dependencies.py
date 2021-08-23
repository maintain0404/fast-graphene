from asyncio import sleep as asleep  # noqa
from asyncio import wait_for
from collections import defaultdict
from functools import reduce
from itertools import islice
from random import choice, randint

import pytest

from fast_graphene import DependOn  # noqa
from fast_graphene.dependencies import (
    build_dependency_tree,
    Dependency,
    DependencyChannel,
)

ARG_FORMAT = "{name} = DependOn({depend_name})"
FUNC_FORMAT = """
def {name}(p, i, {args}):
    print('{name}')
    return 1
"""
AFUNC_FORMAT = """
async def {name}(p, i, {args}):
    print('{name}')
    await asleep(0.1)
    return 1
"""
GEN_FORMAT = """
def {name}(p, i, {args}):
    n = 1
    print('{name}')
    yield 1
    n -= 1
"""
AGEN_FORMAT = """
async def {name}(p, i, {args}):
    await asleep(0.1)
    print('{name}')
    yield 1
    await asleep(0.1)
    print("END")
"""


@pytest.fixture(scope='session', params=[1, 2, 3, 5])
def valid_dependency_tree_func(request):
    depth = request.param
    dependency_by_depth = defaultdict(list)
    whole_funcs = []

    for i in range(depth, 0, -1): # depth
        available_depends = list(reduce(  # Choose random lower level dependencies
            lambda total, obj: total + obj,
            islice(dependency_by_depth.values(), depth - 1),
            [],
        ))

        # TODO: Support for async generator
        # Async generator dependency makes deadlock.
        # When it makes deadlock, its type is coroutine.
        # Figure out why, async generator's type is coroutine on runtime
        depfunc_format = choice((FUNC_FORMAT, AFUNC_FORMAT, GEN_FORMAT))
        for j in range(randint(1, 5)): # func per depth
            func_name = f'dep_{i}__num_{j}'
            args = ', '.join(
                [ARG_FORMAT.format(name=fn.__name__, depend_name=fn.__name__)
                for fn in available_depends]
            )
            exec(depfunc_format.format(name=func_name, args=args))
            dependency_by_depth[i].append(locals().get(func_name))
            whole_funcs.append(locals().get(func_name))
    
    args = ', '.join(
        [ARG_FORMAT.format(name=fn.__name__, depend_name=fn.__name__) 
        for fn in dependency_by_depth[1]]
    )
    exec(FUNC_FORMAT.format(name='root_func', args=args))

    return locals().get('root_func'), whole_funcs


@pytest.fixture(params=[1, 2, 3, 10])
def invalid_dependency_tree_func(request):
    depth = request.param
    dependency_by_depth = defaultdict(list)
    whole_funcs = []

    for i in range(depth, 0, -1): # depth
        available_depends = list(reduce(  # Choose random lower level dependencies
            lambda total, obj: total + obj,
            islice(dependency_by_depth.values(), depth - 1),
            [],
        ))

        depfunc_format = choice((FUNC_FORMAT, AFUNC_FORMAT, GEN_FORMAT, AGEN_FORMAT))
        for j in range(randint(1, 5)): # func per depth
            func_name = f'dep_{i}__num_{j}'
            args = ', '.join(
                [ARG_FORMAT.format(name=fn.__name__, depend_name=fn.__name__)
                for fn in available_depends]
            )
            exec(depfunc_format.format(name=func_name, args=args))
            dependency_by_depth[i].append(locals().get(func_name))
            whole_funcs.append(locals().get(func_name))
    
    args = ', '.join(
        [ARG_FORMAT.format(name=fn.__name__, depend_name=fn.__name__) 
        for fn in dependency_by_depth[1]]
    )
    exec(FUNC_FORMAT.format(name='root_func', args=args))

    return locals().get('root_func'), whole_funcs


def test_dependency_tree(valid_dependency_tree_func):
    func, depends = valid_dependency_tree_func

    result = build_dependency_tree(func)

    flated = result.flated_dependencies
    whole = set([Dependency(fn) for fn in depends])

    assert flated == whole


@pytest.mark.asyncio
async def test_dependency_channel():
    async def r1(p, i):
        return 1

    d = Dependency(r1)
    chan = DependencyChannel([d], None, info=None)

    assert 1 == await wait_for(chan.get(d), 1)



@pytest.fixture(scope='session')
def dependency_tree(valid_dependency_tree_func):
    func, _ = valid_dependency_tree_func
    return build_dependency_tree(func)


@pytest.mark.asyncio
async def test_dependency_channel_with_random_tree(dependency_tree):
    root, flated, _ = dependency_tree
    channel = DependencyChannel(
        flated,
        parent=None,
        info=None,
    )
    try:
        await wait_for(root(None, None, {}, channel), 10)
    except Exception:
        assert False
