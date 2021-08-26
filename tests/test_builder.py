import pytest
from graphene import types as gpt

from fast_graphene.builder import Builder


@pytest.fixture
def builder():
    return Builder()


def test_builder_build_success(builder):
    class TestObjectType(gpt.ObjectType):
        @builder.field
        def test(
            info,
            parent,
            string: str,
            num: int = 0,
        ) -> int:
            return 1

    args = list(TestObjectType._meta.fields["test"].args.values())
    assert gpt.Argument(gpt.Int, 0) in args
    assert gpt.Argument(gpt.String) in args
    assert TestObjectType._meta.fields["test"].type == gpt.Int


@pytest.fixture
def schema_with_builder(builder):
    class TestObjectType(gpt.ObjectType):
        @builder.field
        def test(
            info,
            parent,
            string: str,
            num: int = 0,
        ) -> int:
            return 1

    return gpt.Schema(TestObjectType)


@pytest.mark.asyncio
async def test_builder_execute(schema_with_builder):
    result = await schema_with_builder.execute("query Query { test }")
    assert result["data"]["test"] == 1
