from .dependencies import Dependency


def _get_parent(parent, info, **kwargs):
    return parent


parent = Dependency(_get_parent)


def context(name: str) -> Dependency:
    def get_context(parent, info, **kwargs):
        info.context[name]

    return Dependency(get_context)
