from typing import Callable, List, Optional, Tuple, Any, Dict, Set

from graphene import types as gpt

from .utils import SetDict
from .errors import FastGrapheneException, CircularDependencyException


# Will be used later.
class Dependency:
    def __init__(
        self,
        func: Callable,
        dependencies: Optional[List["Dependency"]] = None,
        arguments: Optional[List[gpt.Argument]] = None,
    ):
        self.func: Callable = func
        # TODO: Let to collect params, dependencies and arguments at once.
        self.func = func
        self.dependencies = dependencies or []
        self.arguments = arguments or []

    def __hash__(self):
        return hash(self.func)


# Will be used later.
class DependencyTreeVisitor:
    def __init__(self, root_depend: Dependency):
        self.root: Dependency = root_depend
        self.all: Set[Dependency] = set()

    @classmethod
    def visit(cls, root_depend: Dependency) -> "DependencyTreeVisitor":
        return cls.__init__(root_depend)

    # TODO: self.dependencies를 확실하게 얻고 나서 실행되어야 함
    def traverse_depends(
        self, to_visit: Dependency, visited: Set[Callable]
    ) -> Tuple[Set[Dependency], SetDict, Optional[CircularDependencyException]]:
        arguments, error = SetDict(), None
        try:
            if to_visit.func in visited:
                raise CircularDependencyException(
                    f"Dependency function {to_visit.func.__name__}"
                    " is circular dependency."
                )
            elif not to_visit.dependencies:
                arguments.update(to_visit.arguments)
            else:
                for dependency in to_visit.dependencies:
                    sub_arguments, sub_error = self.traverse_depends(
                        dependency, visited + {to_visit.func}
                    )
                    arguments.update(sub_arguments)
                    error = sub_error
        except CircularDependencyException as err:
            error = err
        finally:
            return visited, arguments, error

    def traverse(self) -> bool:
        self.all, self._arguments, self._error = self.traverse_depends(
            self.root, [], set()
        )

    @property
    def is_circular(self) -> bool:
        if not getattr(self, "_error", None):
            self.traverse()
        else:
            if self._error:
                return True
            else:
                return False

    @property
    def error(self) -> FastGrapheneException:
        if not getattr(self, "_error", None):
            self.traverse()
        return self._error

    @property
    def arguments(self) -> List[gpt.Argument]:
        if not getattr(self, "_arguments"):
            self.traverse()
        return self._arguments


class DependentFunction:
    def __init__(
        self,
        func: Callable,
        dependencies: Optional[Set[Dependency]] = None
        # TODO: Add later
        # include_parent: bool = True,
        # include_info: bool = True,
    ):
        self.func = func
        self.dependencies = dependencies or set()
        # TODO: Add later
        # self.include_parent = include_parent
        # self.include_info = include_info

    def __call__(self, parent: Any, info: gpt.ResolveInfo, **kwargs):
        pass

    def collect_nested_dependencies(self, dependency: Dependency):
        pass

    def resolve_dependencies(
        self, parent: Any, info: gpt.ResolveInfo, **kwargs
    ) -> Dict[str, Any]:
        pass
