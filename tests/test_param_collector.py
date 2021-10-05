from fast_graphene import DependOn
from fast_graphene.param_collector import interpret_params


def dep(parent, info):
    return 1


def resolver_to_test_dependon(parent, info, dep=DependOn(dep)) -> int:
    return 10


def resolver_to_fail():
    return 10


def test_collect_params():
    args, dep_funcs = interpret_params(resolver_to_test_dependon)

    assert sorted(args) == []
    assert dep_funcs == {"dep": dep}
