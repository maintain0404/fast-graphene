from graphene.types import Argument
from graphene.types import Int

from fast_graphene import Dependency
from fast_graphene import fast_graphene

arg = Argument(Int)


def dp(parent, info, dp = arg):
    return 1


@fast_graphene(Int)
def testfunc(parent, info, dp = Dependency(dp)):
    return 1


def test_fast_graphene_decorator_arguments():
    arg = Argument(Int)
    @fast_graphene(Int)
    def testfunc(parent, info, dp = Argument(Int)):
        return 1

    assert testfunc.args['dp'] == arg
