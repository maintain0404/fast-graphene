from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import wraps
from inspect import signature, Signature
from typing import Any, Callable, Dict, Optional, Type, Union

from graphene import types as gpt

from .annot_compiler import AnnotCompiler
from .param_collector import collect_params
from .types import Annotation, GrapheneType
from .utils import SetDict

DEFAULT_SCALAR_MAP = {
    int: gpt.Int,
    float: gpt.Float,
    str: gpt.String,
    Decimal: gpt.Decimal,
    date: gpt.Date,
    datetime: gpt.DateTime,
    bool: gpt.Boolean,
}


class ContextEnum(Enum):
    RETURN = "return"
    ARGUMENT = "argument"


# TODO: This is not invalid. Fix with build_dependency_tree
class Builder:
    def __init__(
        self,
        # TODO: Add later
        # include_parent: bool = True,
        # include_info: bool = True,
        annot_map=None,
        subcls_annot_map=None,
    ):
        # TODO: Add later
        # self.include_parent: bool = include_parent
        # self.include_info: bool = include_info
        self.annot_compiler = AnnotCompiler(annot_map, subcls_annot_map)

    def compile_type_hint(self, hint, context=None):
        return self.annot_compiler.compile(hint, context=context)

    def field(
        self,
        func: Optional[Callable] = None,
        *,
        default_value: Optional[Any] = None,
        extra_args: Dict[str, gpt.Argument] = None,
        return_type: Union[None, Type[gpt.Scalar], Type[gpt.ObjectType]] = None,
        description: Optional[str] = None,
        deprecation_reason: Optional[str] = None,
    ):
        @wraps(func)
        def inner(func: Callable):
            # 시그니처 따기
            sig = signature(func)
            params = sig.parameters

            nonlocal default_value
            nonlocal extra_args
            extra_args = extra_args or {}
            args = SetDict()
            # TODO: Implement dependency.
            dependencies = set()

            # Set graphene Field type(=return_type).
            nonlocal return_type
            if not return_type:
                return_type = self._compile_return(func, sig)

            param_cnt = 0
            # Check with params.
            args, depend_ons, return_type = collect_params(func)

            args.update(extra_args)
            return gpt.Field(
                return_type,
                args=args,
                resolver=func,
                default_value=default_value,
                description=description,
                deprecation_reason=deprecation_reason,
            )

        if func:
            return inner(func)
        else:
            return inner
