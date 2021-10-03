from typing import List, Optional, Type, TypeVar, Union

Annotation = TypeVar("Annotation", None, Type[None])
# Annotation = Union[None, Type[None]]


def test(args: List[Annotation]):
    try:
        nonetype_idx = args.index(None)
    except ValueError:
        try:
            nonetype_idx = args.index(type(None))
        except ValueError:
            nonetype_idx = None
