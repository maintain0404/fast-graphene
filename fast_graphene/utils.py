from collections import UserDict
from copy import deepcopy
from typing import (
    AbstractSet,
    Any,
    Dict,
    Hashable,
    Iterable,
    List,
    Mapping,
    Optional,
    Type,
)


class SetDict(UserDict, AbstractSet):
    data: Dict

    def __init__(
        self, *mappings: List[Mapping[Hashable, Any]], **kwargs: Dict[Hashable, Any]
    ):
        super().__init__(**kwargs)
        self.update(*mappings)

    def __setitem__(self, key, value):
        if key in self.data:
            raise KeyError(f'Data with key "{key}"" aleady exists.')
        else:
            self.data[key] = value

    def update(
        self, *mappings: List[Mapping[Hashable, Any]], **kwargs: Dict[Hashable, Any]
    ):
        for mapping in mappings:
            for key, value in mapping.items():
                if key in self.data:
                    raise KeyError(f'Data with key "{key}"" aleady exists.')
                else:
                    self.data[key] = value
        for key, value in kwargs.items():
            if key in self.data:
                raise KeyError(f'Data with key "{key}"" aleady exists.')
            else:
                self.data[key] = value

    def __add__(self, other: Mapping):
        new_setdict = deepcopy(self)
        new_setdict.update(other)
        return new_setdict

    __radd__ = __add__


class GrapheneTypeTreeNode:
    def __init__(self, type_: Type, children: Optional[Iterable[Type]] = None):
        self.type_: Type = type_
        self.children: Iterable[GrapheneTypeTreeNode] = children or []

    def compile(self):
        if self.children:
            return self.type_(*(child.compile() for child in self.children))
        else:
            return self.type_
