from collections import UserDict
from copy import deepcopy
from functools import singledispatch
from itertools import chain
from typing import (
    AbstractSet,
    Any,
    Dict,
    Hashable,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    overload,
    Tuple,
    Type,
    Union,
)

from fast_graphene.types import GrapheneType


class SetDict(UserDict, MutableMapping[Hashable, Any]):
    data: Dict

    def __init__(self, *mappings: MutableMapping[Hashable, Any], **kwargs: Any):
        super().__init__(**kwargs)
        for mapping in mappings:
            self.update(mapping)

    def __setitem__(self, key: Hashable, value):
        if key in self.data:
            raise KeyError(f'Data with key "{key}" aleady exists.')
        else:
            self.data[key] = value

    def update(  # type: ignore
        self,
        mapping: Union[MutableMapping[Hashable, Any], Iterable[Tuple[Hashable, Any]]],
        **kwargs: Any,
    ):
        ziped_tuple = (
            mapping.items() if isinstance(mapping, MutableMapping) else mapping
        )
        for key, value in chain(ziped_tuple, kwargs.items()):
            if key in self.data:
                raise KeyError(f'Data with key "{key}" aleady exists.')
            else:
                self.data[key] = value

    def __add__(self, other: MutableMapping):
        new_setdict = deepcopy(self)
        new_setdict.update(other)
        return new_setdict

    __radd__ = __add__


class GrapheneTypeTreeNode:
    def __init__(
        self,
        type_: GrapheneType,
        children: Optional[Iterable["GrapheneTypeTreeNode"]] = None,
    ):
        self.type_: GrapheneType = type_
        self.children: Iterable[GrapheneTypeTreeNode] = children or []

    def compile(self):
        if self.children:
            return self.type_(*(child.compile() for child in self.children))
        else:
            return self.type_
