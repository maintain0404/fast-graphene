from asyncio import sleep

import pytest

from fast_graphene import DependOn
from fast_graphene.dependencies import Dependency, DependencyChannel


async def dep1(parent, info):
    await sleep(1)
    return 1

async def dep2(parent, info):
    await sleep(2)
    return 2


async def add_deps1_deps2(parent, info, dep1 = DependOn(dep1), dep2 = DependOn(dep2)):
    return dep1 + dep2


async def add_deps1_again(parent, info, dep1 = DependOn(dep1), added = DependOn(add_deps1_deps2)):
    return dep1 + added


def test_dependency_channel():
    dependencies = [Dependency(func) for func in (dep1, dep2, add_deps1_deps2, add_deps1_again)]
    channel = DependencyChannel(
        dependencies,
        parent=None,
        info=None,
    )

    