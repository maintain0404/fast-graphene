import pytest
from graphene import types as gpt

from fast_graphene import Builder, DependOn


def test_args_builder(builder: Builder):
    @builder.field
    def func(parent, info, a: int, b: str = "hi") -> int:
        return 1

    func: gpt.Field
    assert func.args["a"] == gpt.Argument(gpt.Int)
    assert func.args["b"] == gpt.Argument(gpt.String, default_value="hi")


@pytest.mark.asyncio
async def test_dependency_builder(builder: Builder, valid_dependency_tree_func):
    dep_func, _ = valid_dependency_tree_func

    @builder.field
    def func(parent, args, dep=DependOn(dep_func)) -> int:
        return 1

    func: gpt.Field
    ext_result = await func.resolver(None, None)

    assert not func.args
    assert ext_result == 1
