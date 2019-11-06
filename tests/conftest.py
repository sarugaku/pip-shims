# -*- coding=utf-8 -*-
import pytest

from pip_shims import Command


class _PipCommand(Command):
    name = "PipCommand"


@pytest.fixture
def PipCommand():
    return _PipCommand
