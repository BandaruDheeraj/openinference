import pytest


def test_wrapt_version():
    import wrapt
    assert wrapt.__version__ < '3.0.0'
