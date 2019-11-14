# -*- coding=utf-8 -*-
from __future__ import absolute_import

import importlib
import os


def get_base_import_path():
    base_import_path = os.environ.get("PIP_SHIMS_BASE_MODULE", "pip")
    return base_import_path


BASE_IMPORT_PATH = get_base_import_path()


def get_pip_version():
    pip = importlib.import_module(BASE_IMPORT_PATH)
    version = getattr(pip, "__version__", None)
    return version


def is_type_checking():
    try:
        from typing import TYPE_CHECKING
    except ImportError:
        return False
    return TYPE_CHECKING


MYPY_RUNNING = os.environ.get("MYPY_RUNNING", is_type_checking())
