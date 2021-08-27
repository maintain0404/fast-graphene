import pytest

from fast_graphene import Builder


@pytest.fixture(scope="session")
def builder():
    return Builder()
