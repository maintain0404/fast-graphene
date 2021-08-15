from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import wraps
from inspect import Parameter, signature, Signature
from typing import Any, Callable, Dict, Optional, Type, Union

from graphene import types as gpt

from .annot_compiler import TypeCompiler
from .types import Annotation, GrapheneType
from .utils import FastGrapheneException, SetDict

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


class Builder:
    def __init__(
        self,
        include_parent: bool = True,
        include_info: bool = True,
        annot_map=None,
        subcls_annot_map=None,
    ):
        self.include_parent: bool = include_parent
        self.include_info: bool = include_info
        self.type_compiler = TypeCompiler(annot_map, subcls_annot_map)

    def compile_type_hint(self, hint, context=None):
        return self.type_compiler.compile(hint, context=context)

    def fast_graphene(
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

            # Check with params.
            for name, param in params.items():
                default = param.default
                annot = param.annotation
                if annot is Parameter.empty:
                    annot = Any
                # TODO: Check if argument instance is correct to hint.
                if default is not Parameter.empty:
                    args[name] = self._copile_argument_with_default(func, default)
                elif annot is not Any:
                    args[name] = self._compile_argument_with_annotation(func, annot)
                # TODO: Implement Dependency.
                else:
                    raise FastGrapheneException

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

    def _compile_return(
        self,
        func: Callable,
        sig: Signature,
    ) -> GrapheneType:
        if sig.return_annotation == Signature.empty:
            ret_annot = Any
        else:
            ret_annot = sig.return_annotation
        return self.type_compiler.compile(
            annotation=ret_annot, context={"function": func, "type": ContextEnum.RETURN}
        )

    def _copile_argument_with_default(
        self, func: Callable, default: Any
    ) -> gpt.Argument:
        if isinstance(default, gpt.Argument):
            return default
        else:
            gpt_type = self.type_compiler.compile(
                type(default),
                context={
                    "function": func,
                    "type": ContextEnum.ARGUMENT,
                },
            )
            return gpt.Argument(gpt_type, default_value=default)

    def _compile_argument_with_annotation(
        self,
        func: Callable,
        annotation: Annotation,
    ) -> gpt.Argument:
        gpt_type = self.type_compiler.compile(
            annotation,
            context={
                "function": func,
                "type": ContextEnum.ARGUMENT,
            },
        )
        return gpt.Argument(gpt_type)
