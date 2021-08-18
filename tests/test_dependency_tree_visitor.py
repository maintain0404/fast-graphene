from asyncio import sleep as asleep  # noqa
from collections import defaultdict
from functools import reduce
from itertools import islice
from random import choice, randint

import pytest

from fast_graphene import DependOn  # noqa
from fast_graphene.dependencies import Dependency, build_dependency_tree

ARG_FORMAT = "{name} = DependOn({depend_name})"
FUNC_FORMAT = """
def {name}(p, i, {args}):
    return 1
"""
AFUNC_FORMAT = """
async def {name}(p, i, {args}):
    await asleep(0.1)
    return 1
"""
GEN_FORMAT = """
def {name}(p, i, {args}):
    n = 1
    yield 1
    n -= 1
"""
AGEN_FORMAT = """
async def {name}(p, i, {args}):
    await asleep(0.1)
    yield
    await asleep(0.1)
"""


@pytest.fixture(params=[1, 2, 3, 10])
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

        depfunc_format = choice((FUNC_FORMAT, AFUNC_FORMAT, GEN_FORMAT, AGEN_FORMAT,))
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

        depfunc_format = choice((FUNC_FORMAT, AFUNC_FORMAT, GEN_FORMAT, AGEN_FORMAT,))
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
