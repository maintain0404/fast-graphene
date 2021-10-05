from inspect import Parameter, signature
from typing import Callable, Dict, Iterable, Optional, Tuple

from graphene import types as gpt

from .annot_compiler import AnnotCompiler
from .types import ParamValue


class DependOn:
    def __init__(self, func):
        self.func = func


def interpret_params(
    func: Callable,
    annot_compiler: Optional[AnnotCompiler] = None,
) -> Tuple[Dict[str, gpt.Argument], Dict[str, Callable]]:
    sig = signature(func)
    annot_compiler = annot_compiler or AnnotCompiler()

    args = {}
    depend_ons = {}
    param_cnt = 0
    for name, param in sig.parameters.items():
        if param_cnt < 2:
            param_cnt += 1
            continue

        default = param.default if param.default is not Parameter.empty else None
        annot = param.annotation if param.annotation is not Parameter.empty else None
        if isinstance(default, gpt.Argument):
            args[name] = default
        elif isinstance(default, DependOn):
            depend_ons[name] = default.func
        elif default or annot:
            # TODO: Check if default value is correct to annot
            type_ = annot or type(default)
            compiled = annot_compiler.compile(type_)
            args[name] = gpt.Argument(compiled, default_value=default)
        else:
            raise ValueError(
                f'Paramter "{name}" of function "{func}" doesn\'t have default value or annotaion.'
            )

    return args, depend_ons


def pick_used_params_only(
    used_arg_names: Iterable[str], args: Dict[str, ParamValue]
) -> Dict[str, ParamValue]:
    return {name: args[name] for name in used_arg_names}
