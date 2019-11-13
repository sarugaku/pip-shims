# -*- coding=utf-8 -*-
import inspect
import sys
from functools import wraps

import packaging.version
import six

# format: off
six.add_move(six.MovedAttribute("Callable", "collections", "collections.abc"))  # noqa
from six.moves import Callable  # type: ignore  # noqa  # isort:skip

# format: on

STRING_TYPES = (str,)
if sys.version_info < (3, 0):
    STRING_TYPES = STRING_TYPES + (unicode,)  # noqa:F821


class BaseMethod(Callable):
    def __init__(self, func_base, name, *args, **kwargs):
        self.func = func_base
        self.__name__ = self.__qualname__ = name

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class BaseClassMethod(Callable):
    def __init__(self, func_base, name, *args, **kwargs):
        self.func = func_base
        self.__name__ = self.__qualname__ = name

    def __call__(self, cls, *args, **kwargs):
        return self.func(*args, **kwargs)


def make_method(fn):
    @wraps(fn)
    def method_creator(*args, **kwargs):
        return BaseMethod(fn, *args, **kwargs)

    return method_creator


def make_classmethod(fn):
    @wraps(fn)
    def classmethod_creator(*args, **kwargs):
        return classmethod(BaseClassMethod(fn, *args, **kwargs))

    return classmethod_creator


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


@memoize
def parse_version(version):
    if not isinstance(version, STRING_TYPES):
        raise TypeError("Can only derive versions from string, got {0!r}".format(version))
    return packaging.version.parse(version)


def split_package(module, subimport=None):
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


def overload_func_using_original(parent, func_name, new_func):
    original_func = getattr(parent, func_name, None)
    if original_func is not None:
        _, original_args = get_method_args(original_func)
        _, new_args = get_method_args(new_func)
        for property_name in ("__name__", "__qualname__", "__module__"):
            original_val = getattr(original_func, property_name, None)
            if original_val:
                setattr(new_func, property_name, original_val)
        set_default_kwargs(new_func, "base_func", original_func)


def set_default_kwargs(basecls, method, **default_kwargs):
    target_method = getattr(basecls, method, None)
    if target_method is None:
        return basecls
    target_func, inspected_args = get_method_args(target_method)
    pos_args = inspected_args.args
    # Spit back the base class if we can't find matching arguments
    # to put defaults in place of
    if not any(arg in pos_args for arg in list(default_kwargs.keys())):
        return basecls
    prepended_defaults = tuple()
    # iterate from the function's argument order to make sure we fill this
    # out in the correct order
    for arg in pos_args:
        if arg in default_kwargs:
            prepended_defaults = prepended_defaults + (default_kwargs[arg],)
    if not prepended_defaults:
        return basecls
    if six.PY2 and inspect.ismethod(target_method):
        new_defaults = prepended_defaults + target_func.__defaults__
        target_method.__func__.__defaults__ = new_defaults
    else:
        new_defaults = prepended_defaults + target_method.__defaults__
        target_method.__defaults__ = new_defaults
    setattr(basecls, method, target_method)
    return basecls


def fallback_is_file_url(link):
    return link.url.lower().startswith("file:")
