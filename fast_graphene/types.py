from enum import Enum
from typing import (
    Callable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
)

from graphene import types as gpt
from graphene.types.structures import Structure

GenericAlias = type(List[int])


# TODO: Define Annotation clearly without TypeVar
Annotation = TypeVar("Annotation")


ParamValue = TypeVar("ParamValue")  # Argument value, Dependency


GrapheneType = Union[
    Type[gpt.Scalar],
    Type[gpt.ObjectType],
    Type[gpt.NonNull],
    Type[Structure],  # gpt.NonNull, gpt.List
    Type[gpt.Union],
]


class ContextEnum(Enum):
    ARGUMENT = "argument"
    FIELD = "field"
    MUTATION = "mutation"
    INPUT_FIELD = "input_field"


AnnotCompileResult = Tuple[GrapheneType, List[Annotation]]


AnnotCompileFunc = Callable[
    [Annotation, List[Annotation], Optional["Context"]],
    AnnotCompileResult,
]


class Context(TypedDict):
    function: AnnotCompileFunc
    type: Union[Literal["argument", "return", "mutation", "input_field"], ContextEnum]
