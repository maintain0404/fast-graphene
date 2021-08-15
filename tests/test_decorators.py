import pytest
from graphene.types import Argument, Int

from fast_graphene import Dependency, fast_graphene

arg = Argument(Int)


def dp(parent, info, dp = arg):
    return 1


@fast_graphene(Int)
def testfunc(parent, info, dp = Dependency(dp)):
    return 1


@pytest.mark.skip
def test_fast_graphene_decorator_arguments():
    arg = Argument(Int)
    @fast_graphene(Int)
    def testfunc(parent, info, dp = Argument(Int)):
        return 1

    assert testfunc
