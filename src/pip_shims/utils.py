# -*- coding=utf-8 -*-
import contextlib
import inspect
import sys
from functools import wraps

STRING_TYPES = (str,)
if sys.version_info < (3, 0):
    STRING_TYPES = STRING_TYPES + (unicode,)  # noqa:F821


def memoize(obj):
    cache = obj.cache = {}

    @wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


@memoize
def _parse(version):
    if isinstance(version, STRING_TYPES):
        return tuple((int(i) for i in version.split(".")))
    return version


def get_package(module, subimport=None):
    package = None
    if subimport:
        package = subimport
    else:
        module, _, package = module.rpartition(".")
    return module, package


def get_method_args(target_method):
    try:
        inspected_args = inspect.getargs(target_method.__code__)
    except AttributeError:
        target_func = getattr(target_method, "__func__", None)
        if target_func is not None:
            inspected_args = inspect.getargs(target_func.__code__)
    else:
        target_func = target_method
    return target_func, inspected_args


@contextlib.contextmanager
def nullcontext(*args, **kwargs):
    try:
        yield
    finally:
        pass
