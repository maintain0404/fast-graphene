from typing import (
    _GenericAlias,
    _SpecialForm,
    _TypedDictMeta,
    Any,
    Callable,
    List,
    Literal,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)
from enum import Enum


Annotation = Union[
    type,
    _SpecialForm,  # Union, Any, Optional, List
    TypeVar,
    _TypedDictMeta,  # TypedDict
    _GenericAlias,  # Tuple
]


GrapheneType = Any


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
