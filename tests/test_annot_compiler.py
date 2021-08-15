from enum import Enum
from typing import List, Optional

import pytest
from graphene import types as gpt

from fast_graphene.annot_compiler import TypeCompiler

type_compiler = TypeCompiler()


@pytest.mark.parametrize(
    'annotation', [
        (Optional[int], gpt.NonNull(gpt.Int)),
        (List[str], gpt.List(gpt.String)),
        (Optional[List[int]], gpt.NonNull(gpt.List(gpt.Int))),
        (Optional[List[Optional[int]]], gpt.NonNull(gpt.List(gpt.NonNull(gpt.Int)))),
    ]
)
def test_transfiler(annotation):
    origin, expected = annotation

    compiled = type_compiler.compile(origin)
    assert compiled == expected


class TestEnum(Enum):
    a = 1
    b = 2
    c = 3


@pytest.mark.parametrize(
    'annotation', [
        (TestEnum, gpt.Enum.from_enum(TestEnum))
    ]
)
def test_transfiler_enum(annotation):
    origin, expected = annotation

    transfiled = type_compiler.compile(origin)
    for name in transfiled._meta.enum.__members__.keys():
        assert getattr(expected, name, False)
