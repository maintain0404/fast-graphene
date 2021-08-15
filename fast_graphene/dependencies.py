from typing import Callable, List, Optional, Tuple

from graphene import types as gpt

from .utils import FastGrapheneException, SetDict


class CircularDependencyException(FastGrapheneException):
    pass


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


class DependencyTreeVisitor:
    def __init__(self, root_depend: Dependency):
        self.root: Dependency = root_depend

    # TODO: self.dependencies를 확실하게 얻고 나서 실행되어야 함
    def traverse_depends(
        self, to_visit: Dependency, visited: List[Callable]
    ) -> Tuple[SetDict, List[CircularDependencyException]]:
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
                        dependency, visited + [to_visit.func]
                    )
                    arguments.update(sub_arguments)
                    error = sub_error
        except CircularDependencyException as err:
            error = err
        finally:
            return arguments, error

    def traverse(self) -> bool:
        self._arguments, self._error = self.traverse_depends(self.root, [])

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
