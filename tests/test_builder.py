from asyncio import wait_for

import pytest
from graphene import types as gpt

from fast_graphene.builder import Builder


@pytest.fixture
def builder():
    return Builder()


@pytest.fixture
def object_type(builder):
    class TestObjectType(gpt.ObjectType):
        @builder.field
        async def test(
            info,
            parent,
            string: str,
            num: int = 0,
        ) -> int:
            return 1

    return TestObjectType


def test_builder_build_success(object_type):
    args = list(object_type._meta.fields["test"].args.values())
    assert gpt.Argument(gpt.Int, 0) in args
    assert gpt.Argument(gpt.String) in args
    assert object_type._meta.fields["test"].type == gpt.Int


@pytest.fixture
def schema_with_builder(object_type):
    return gpt.Schema(object_type)


@pytest.mark.asyncio
async def test_builder_execute(schema_with_builder: gpt.Schema):
    try:
        result = await wait_for(
            schema_with_builder.execute_async("query Query { test }"), 5
        )
    except Exception:
        assert False
    assert not result.errors
    assert result.data["test"] == 1
