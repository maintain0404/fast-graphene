from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from inspect import isfunction
from typing import Callable, Dict, get_args, get_origin, List, Optional, Tuple, Union

from graphene import types as gpt

from .types import Annotation, Context, GrapheneType
from .utils import GrapheneTypeTreeNode
from .errors import FastGrapheneException


def compile_union(
    annotation: Annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> Tuple[GrapheneType, List[Annotation]]:
    try:
        nonetype_idx = args.index(type(None))
    except ValueError:
        try:
            nonetype_idx = args.index(None)
        except ValueError:
            nonetype_idx = None
    if nonetype_idx:
        if len(args) == 2:
            return gpt.NonNull, [args[(nonetype_idx + 1) % 2]]
        else:
            args_without_nonetype = tuple(
                *args[:nonetype_idx], args[nonetype_idx + 1 :]
            )
            return gpt.NonNull, [Union[args_without_nonetype]]
    else:
        return gpt.Union, args


def compile_list(
    annotation: Annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> Tuple[GrapheneType, List[Annotation]]:
    return gpt.List, args


def compile_object_type(
    annotation: Annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> Tuple[GrapheneType, List[Annotation]]:
    return annotation, []


def compile_enum(
    annotation: Annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> Tuple[GrapheneType, List[Annotation]]:
    return gpt.Enum.from_enum(annotation), []


DEFAULT_ANNOT_MAP = {
    Union: compile_union,
    List: compile_list,
    list: compile_list,
    int: gpt.Int,
    float: gpt.Float,
    str: gpt.String,
    Decimal: gpt.Decimal,
    date: gpt.Date,
    datetime: gpt.DateTime,
    bool: gpt.Boolean,
}


DEFAULT_SUBCLS_ANNOT_MAP = {
    gpt.ObjectType: compile_object_type,
    Enum: compile_enum,
}


class AnnotCompiler:
    def __init__(
        self,
        annot_map=None,
        subcls_annot_map=None,
    ):
        self.annot_map: Dict[
            Annotation,
            Union[
                Callable[
                    [Annotation, List[Annotation]],
                    Union[GrapheneType, Optional[List[Annotation]]],
                ],
                GrapheneType,
            ],
        ] = deepcopy(DEFAULT_ANNOT_MAP)
        if annot_map:
            self.annot_map.update(annot_map)
        self.subcls_annot_map: Dict[
            type,
            Union[
                Callable[
                    [Annotation, List[Annotation]],
                    Union[GrapheneType, Optional[List[Annotation]]],
                ],
                GrapheneType,
            ],
        ] = deepcopy(DEFAULT_SUBCLS_ANNOT_MAP)
        if annot_map:
            self.subcls_annot_map.update(subcls_annot_map)

    def _parent_class_finder(self, cls: type) -> type:
        if not isinstance(cls, type):
            raise FastGrapheneException
        for parent in self.subcls_annot_map.keys():
            if issubclass(cls, parent):
                return parent
        else:
            raise FastGrapheneException

    def compile_as_node(
        self,
        annotation: Annotation,
        args: List[Annotation],
        context: Optional[Context] = None,
    ) -> GrapheneTypeTreeNode:
        origin = get_origin(annotation) or annotation
        args_origin = get_args(annotation)

        compiler = self.annot_map.get(origin) or self.subcls_annot_map.get(
            self._parent_class_finder(origin)
        )

        if compiler is None:
            raise FastGrapheneException
        # Scalar case
        elif not isfunction(compiler) and isinstance(compiler, type):
            return GrapheneTypeTreeNode(compiler)

        graphene_type, args = compiler(origin, args_origin, context=context)
        node = GrapheneTypeTreeNode(
            graphene_type,
            [
                self.compile_as_node(
                    child_annot, get_args(child_annot), context=context
                )
                for child_annot in args
            ],
        )

        return node

    def compile(
        self, annotation: Annotation, context: Optional[Context] = None
    ) -> GrapheneType:
        node = self.compile_as_node(annotation, [], context=context)
        return node.compile()
