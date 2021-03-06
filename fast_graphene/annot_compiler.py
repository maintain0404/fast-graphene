from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from inspect import isfunction
from typing import Dict, get_args, get_origin, List, Optional, Type, Union

from graphene import types as gpt

from .types import (
    Annotation,
    AnnotCompileFunc,
    AnnotCompileResult,
    Context,
    GrapheneType,
)
from .utils import GrapheneTypeTreeNode


def compile_union(
    annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> AnnotCompileResult:
    filtered_args = tuple(filter(lambda obj: obj not in (None, type(None)), args))
    if filtered_args != args:
        if len(filtered_args) == 1:
            return gpt.NonNull, [filtered_args[0]]
        else:
            return gpt.NonNull, [Union[filtered_args]]  # type: ignore
    else:
        return gpt.Union, args


def compile_list(
    annotation: Annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> AnnotCompileResult:
    return gpt.List, args


def compile_object_type(
    annotation: Type[gpt.ObjectType],
    args: List[Annotation],
    context: Optional[Context] = None,
) -> AnnotCompileResult:
    return annotation, []


def compile_enum(
    annotation: Annotation,
    args: List[Annotation],
    context: Optional[Context] = None,
) -> AnnotCompileResult:
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
            Union[AnnotCompileFunc, GrapheneType],
        ] = deepcopy(DEFAULT_ANNOT_MAP)
        if annot_map:
            self.annot_map.update(annot_map)
        self.subcls_annot_map: Dict[
            type,
            Union[
                AnnotCompileFunc,
                Union[AnnotCompileFunc, GrapheneType],
            ],
        ] = deepcopy(DEFAULT_SUBCLS_ANNOT_MAP)
        if annot_map:
            self.subcls_annot_map.update(subcls_annot_map)

    def _parent_class_finder(self, cls: type) -> Optional[type]:
        for parent in self.subcls_annot_map.keys():
            if issubclass(cls, parent):
                return parent
        else:
            return None

    def compile_as_node(
        self,
        annotation: Annotation,
        args: List[Annotation],
        context: Optional[Context] = None,
    ) -> GrapheneTypeTreeNode:
        origin = get_origin(annotation) or annotation
        args_origin = get_args(annotation)
        compiler = None

        if isinstance(origin, type):
            compiler = self.subcls_annot_map.get(self._parent_class_finder(origin))
        if not compiler:
            compiler = self.annot_map.get(origin)

        if compiler is None:
            raise TypeError(
                f'Cannot compile "{annotation}". Use "annot_map" and "subcls_annot_map" option.'
            )
        # TODO: Change type to parent class of all graphene types.
        # Scalar case
        elif isinstance(compiler, type):
            node = GrapheneTypeTreeNode(compiler)
        elif isfunction(compiler):
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
