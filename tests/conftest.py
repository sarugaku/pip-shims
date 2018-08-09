# -*- coding=utf-8 -*-
from pip_shims import Command
import pytest


class _PipCommand(Command):
    name = "PipCommand"


@pytest.fixture
def PipCommand():
    return _PipCommand
