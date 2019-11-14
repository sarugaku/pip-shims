# -*- coding=utf-8 -*-
from __future__ import absolute_import

import importlib
import inspect
import os
import sys
import types
from collections import namedtuple
from contextlib import contextmanager

import six
from packaging.version import parse as parse_version

from .models import ShimmedPathCollection, import_pip, lookup_current_pip_version

# format: off
six.add_move(six.MovedAttribute("Callable", "collections", "collections.abc"))  # noqa
from six.moves import Callable  # type: ignore  # noqa  # isort:skip

# format: on


class _shims(types.ModuleType):
    CURRENT_PIP_VERSION = str(lookup_current_pip_version())

    @classmethod
    def parse_version(cls, version):
        return parse_version(version)

    def __dir__(self):
        result = list(self._locations.keys()) + list(self.__dict__.keys())
        result.extend(
            (
                "__file__",
                "__doc__",
                "__all__",
                "__docformat__",
                "__name__",
                "__path__",
                "__package__",
                "__version__",
            )
        )
        return result

    @classmethod
    def _new(cls):
        return cls()

    @property
    def __all__(self):
        return list(self._locations.keys())

    def __init__(self):
        self._locations = ShimmedPathCollection.get_registry()
        self.pip_version = str(lookup_current_pip_version())
        self.pip = import_pip()

    def __getattr__(self, *args, **kwargs):
        locations = super(_shims, self).__getattribute__("_locations")
        if args[0] in locations:
            return locations[args[0]].shim()
        return super(_shims, self).__getattribute__(*args, **kwargs)


old_module = sys.modules[__name__] if __name__ in sys.modules else None
module = sys.modules[__name__] = _shims()
module.__dict__.update(
    {
        "__file__": __file__,
        "__package__": __package__,
        "__doc__": __doc__,
        "__all__": module.__all__,
        "__name__": __name__,
    }
)
