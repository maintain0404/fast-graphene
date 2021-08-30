from asyncio import wait_for

import pytest

from fast_graphene.dependencies import (
    build_dependency_tree,
    Dependency,
    DependencyChannel,
)


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


@pytest.fixture(scope="session")
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
