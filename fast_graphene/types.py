from typing import (
    _CallableType,
    _GenericAlias,
    _SpecialForm,
    _TypedDictMeta,
    Any,
    Callable,
    GenericAlias,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union
)

Hint = Union[Type, GenericAlias]


Annotation = Union[
    type,
    _SpecialForm,  # Union, Any, Optional, List
    _CallableType,  # Callable
    TypeVar,
    _TypedDictMeta,  # TypedDict
    _GenericAlias,  # Tuple
]


GrapheneType = Any


class Context(TypedDict):
    function: Optional[
        Callable[
            [Annotation, List[Annotation], Optional["Context"]],
            Tuple[Annotation, List[Annotation]],
        ]
    ]
    type: Literal["argument", "return"]
