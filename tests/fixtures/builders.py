import pytest
from graphene import types as gpt

from fast_graphene import Builder


@pytest.fixture(scope="session")
def builder():
    return Builder()
