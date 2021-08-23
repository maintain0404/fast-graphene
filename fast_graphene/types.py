from enum import Enum
from typing import (
    _SpecialForm,
    Any,
    Callable,
    List,
    Literal,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    Type,
)

from graphene import types as gpt
from graphene.types.structures import Structure

GenericAlias = type(list[int])


# TODO: Define Annotation clearly without TypeVar
Annotation = TypeVar('Annotation')
# Annotation = Union[
#     None,
#     NoneType,
#     type,
#     _SpecialForm,  # Union, Any, Optional, List
#     TypeVar,
#     Union,
#     Any,
#     # TODO: Add these annotated.
#     # TypedDictMeta,  # TypedDict
#     # Type[GenericAlias],  # Tuple
#     # Type[NamedTuple]  # NamedTuple
# ]


GrapheneType = Union[
    Type[gpt.Scalar],
    Type[gpt.ObjectType],
    Type[gpt.NonNull],
    Type[Structure],  # gpt.NonNull, gpt.List
    Type[gpt.Union],
]
gpt.Union

class ContextType(Enum):
    ARGUMENT = "argument"
    FIELD = "field"
    MUTATION = "mutation"
    INPUT_FIELD = "input_field"


class Context(TypedDict):
    function: Optional[
        Callable[
            [Annotation, List[Annotation], Optional["Context"]],
            Tuple[Annotation, List[Annotation]],
        ]
    ]
    type: Literal["argument", "return"]
