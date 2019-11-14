# -*- coding: utf-8 -*-

import collections
import contextlib
import functools
import importlib
import inspect
import operator
import sys
import types
import weakref

import packaging.version
import six

from . import backports
from .environment import BASE_IMPORT_PATH, MYPY_RUNNING, get_pip_version
from .utils import (
    BaseClassMethod,
    BaseMethod,
    fallback_is_file_url,
    get_method_args,
    make_classmethod,
    make_method,
    nullcontext,
    parse_version,
    set_default_kwargs,
    split_package,
)

# format: off
six.add_move(six.MovedAttribute("Callable", "collections", "collections.abc"))  # noqa
from six.moves import Callable  # type: ignore  # isort:skip  # noqa

# format: on


if MYPY_RUNNING:
    from typing import (  # noqa:F811
        Any,
        Callable,
        ContextManager,
        Dict,
        Iterable,
        List,
        Optional,
        Type,
        Union,
    )


PIP_VERSION_SET = {
    "7.0.0",
    "7.0.1",
    "7.0.2",
    "7.0.3",
    "7.1.0",
    "7.1.1",
    "7.1.2",
    "8.0.0",
    "8.0.1",
    "8.0.2",
    "8.0.3",
    "8.1.0",
    "8.1.1",
    "8.1.2",
    "9.0.0",
    "9.0.1",
    "9.0.2",
    "9.0.3",
    "10.0.0",
    "10.0.1",
    "18.0",
    "18.1",
    "19.0",
    "19.0.1",
    "19.0.2",
    "19.0.3",
    "19.1",
    "19.1.1",
    "19.2",
    "19.2.1",
    "19.2.2",
    "19.2.3",
    "19.3",
    "19.3.1",
}


ImportTypesBase = collections.namedtuple(
    "ImportTypes", ["FUNCTION", "CLASS", "MODULE", "CONTEXTMANAGER"]
)


class ImportTypes(ImportTypesBase):
    FUNCTION = 0
    CLASS = 1
    MODULE = 2
    CONTEXTMANAGER = 3
    METHOD = 4
    ATTRIBUTE = 5


class PipVersion(collections.Sequence):
    def __init__(
        self,
        version,
        round_prereleases_up=True,
        base_import_path=None,
        vendor_import_path="pip._vendor",
    ):
        # type: (str, bool, Optional[str], str) -> None
        self.version = version
        self.vendor_import_path = vendor_import_path
        self.round_prereleases_up = round_prereleases_up
        parsed_version = self._parse()
        if round_prereleases_up and parsed_version.is_prerelease:
            parsed_version._version = parsed_version._version._replace(dev=None, pre=None)
            self.version = str(parsed_version)
            parsed_version = self._parse()
        if base_import_path is None:
            if parsed_version >= parse_version("10.0.0"):
                base_import_path = "{0}._internal".format(BASE_IMPORT_PATH)
            else:
                base_import_path = "{0}".format(BASE_IMPORT_PATH)
        self.base_import_path = base_import_path
        self.parsed_version = parsed_version

    @property
    def version_tuple(self):
        return tuple(self.parsed_version._version)

    @property
    def version_key(self):
        return self.parsed_version._key

    def is_valid(self, compared_to):
        # type: (PipVersion) -> bool
        return self == compared_to

    def __len__(self):
        # type: () -> int
        return len(self.version_tuple)

    def __getitem__(self, item):
        return self.version_tuple[item]

    def _parse(self):
        # type: () -> packaging.version._BaseVersion
        return parse_version(self.version)

    def __hash__(self):
        # type: () -> int
        return hash(self.parsed_version)

    def __str__(self):
        # type: () -> str
        return "{0!s}".format(self.parsed_version)

    def __repr__(self):
        # type: () -> str
        return "<PipVersion {0!r}, Import Path: {1!r}, Vendor Import Path: {2!r}, Parsed Version: {3!r}>".format(
            self.version,
            self.base_import_path,
            self.vendor_import_path,
            self.parsed_version,
        )

    def __gt__(self, other):
        # type: (PipVersion) -> bool
        return self.parsed_version > other.parsed_version

    def __lt__(self, other):
        # type: (PipVersion) -> bool
        return self.parsed_version < other.parsed_version

    def __le__(self, other):
        # type: (PipVersion) -> bool
        return self.parsed_version <= other.parsed_version

    def __ge__(self, other):
        # type: (PipVersion) -> bool
        return self.parsed_version >= other.parsed_version

    def __ne__(self, other):
        # type: (PipVersion) -> bool
        return self.parsed_version != other.parsed_version

    def __eq__(self, other):
        # type: (PipVersion) -> bool
        return self.parsed_version == other.parsed_version


version_cache = weakref.WeakValueDictionary()
CURRENT_PIP_VERSION = None


def pip_version_lookup(version, *args, **kwargs):
    try:
        cached = version_cache.get(version)
    except KeyError:
        cached = None
    if cached is not None:
        return cached
    pip_version = PipVersion(version, *args, **kwargs)
    version_cache[version] = pip_version
    return pip_version


def lookup_current_pip_version():
    global CURRENT_PIP_VERSION
    if CURRENT_PIP_VERSION is not None:
        return CURRENT_PIP_VERSION
    CURRENT_PIP_VERSION = pip_version_lookup(get_pip_version())
    return CURRENT_PIP_VERSION


class PipVersionRange(collections.Sequence):
    def __init__(self, start, end):
        # type: (PipVersion, PipVersion) -> PipVersionRange
        if start > end:
            raise ValueError("Start version must come before end version")
        self._versions = (start, end)

    def __str__(self):
        return "{0!s} -> {1!s}".format(self._versions[0], self._versions[-1])

    @property
    def base_import_paths(self):
        return set([version.base_import_path for version in self._versions])

    @property
    def vendor_import_paths(self):
        return set([version.vendor_import_path for version in self._versions])

    def is_valid(self):
        return pip_version_lookup(get_pip_version()) in self

    def __contains__(self, item):
        if not isinstance(item, PipVersion):
            raise TypeError("Need a PipVersion instance to compare")
        return item >= self[0] and item <= self[-1]

    def __getitem__(self, item):
        return self._versions[item]

    def __len__(self):
        return len(self._versions)

    def __lt__(self, other):
        return (other.is_valid() and not self.is_valid()) or (
            not (self.is_valid() or other.is_valid())
            or (self.is_valid() and other.is_valid())
            and self._versions[-1] < other._versions[-1]
        )

    def __hash__(self):
        return hash(self._versions)


class ShimmedPath:
    __modules = {}

    def __init__(
        self,
        name,  # type: str
        import_target,  # type: str
        import_type,  # type: ImportTypes
        version_range,  # type: PipVersionRange
        provided_methods=None,  # type: Dict[str, Callable]
        provided_functions=None,  # type: Dict[str, Callable]
        provided_classmethods=None,  # type: Dict[str, Callable]
        provided_contextmanagers=None,  # type: Dict[str, Callable]
        provided_mixins=None,  # type: List[Type]
        default_args=None,  # type: Dict[str, List[List[Any], Dict[str, Any]]]
    ):
        # type: (...) -> None
        if provided_methods is None:
            provided_methods = {}
        if provided_classmethods is None:
            provided_classmethods = {}
        if provided_functions is None:
            provided_functions = {}
        if provided_contextmanagers is None:
            provided_contextmanagers = {}
        if provided_mixins is None:
            provided_mixins = []
        if default_args is None:
            default_args = {}
        self.version_range = version_range
        self.name = name
        self.full_import_path = import_target
        module_path, name_to_import = split_package(import_target)
        self.module_path = module_path
        self.name_to_import = name_to_import
        self.import_type = import_type
        self._imported = None
        self._provided = None
        self.provided_methods = provided_methods
        self.provided_functions = provided_functions
        self.provided_classmethods = provided_classmethods
        self.provided_contextmanagers = provided_contextmanagers
        self.provided_mixins = [m for m in provided_mixins if m is not None]
        self.default_args = default_args

    def _as_tuple(self):
        return (self.name, self.version_range, self.full_import_path, self.import_type)

    @staticmethod
    def _set_default_kwargs(parent, basecls, method, **default_kwargs):
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

    @staticmethod
    def _add_mixin(basecls, *mixins):
        if not any(mixins):
            return basecls
        base_dict = basecls.__dict__.copy()
        class_tuple = (basecls,)
        for mixin in mixins:
            if not mixin:
                continue
            mixin_dict = mixin.__dict__.copy()
            base_dict.update(mixin_dict)
            class_tuple = class_tuple + (mixin,)
        base_dict.update(basecls.__dict__)
        return type(basecls.__name__, class_tuple, base_dict)

    @classmethod
    def _import_module(cls, module):
        # type: (str) -> Optional[types.ModuleType]
        if module in ShimmedPath.__modules:
            result = ShimmedPath.__modules[module]
            if result is not None:
                return result
        try:
            imported = importlib.import_module(module)
        except ImportError:
            return None
        else:
            ShimmedPath.__modules[module] = imported
        return imported

    @classmethod
    def _parse_provides_dict(
        cls,
        provides,  # type: Dict[str, Callable]
        prepend_arg_to_callables=None,  # type: Optional[str]
    ):
        # type: (...) -> Dict[str, Callable]
        creating_methods = False
        creating_classmethods = False
        if prepend_arg_to_callables is not None:
            if prepend_arg_to_callables == "self":
                creating_methods = True
            elif prepend_arg_to_callables == "cls":
                creating_classmethods = True
        provides_map = {}
        for item_name, item_value in provides.items():
            if isinstance(item_value, ShimmedPath):
                item_value = item_value.shim()
            if inspect.isfunction(item_value):
                callable_args = inspect.getargs(item_value.__code__).args
                if "self" not in callable_args and creating_methods:
                    item_value = make_method(item_value)(item_name)
                elif "cls" not in callable_args and creating_classmethods:
                    item_value = make_classmethod(item_value)(item_name)
            elif isinstance(item_value, six.string_types):
                module_path, name = split_package(item_value)
                module = cls._import_module(module_path)
                item_value = getattr(module, name, None)
            provides_map[item_name] = item_value
        return provides_map

    def _ensure_function(self, parent, funcname, func):
        """Given a module, a function name, and a function
        object, attaches the given function to the module and
        ensures it is named properly according to the provided argument
        """
        qualname = funcname
        if parent is None:
            parent = __module__  # noqa:F821
        parent_is_module = inspect.ismodule(parent)
        parent_is_class = inspect.isclass(parent)
        module = None
        if parent_is_module:
            module = parent.__name__
        elif parent_is_class:
            qualname = "{0}.{1}".format(parent.__name__, qualname)
            module = getattr(parent, "__module__", None)
        else:
            module = getattr(parent, "__module__", None)
        try:
            func.__name__ = funcname
        except AttributeError:
            if getattr(func, "__func__", None) is not None:
                func = func.__func__
            func.__name__ = funcname
        func.__qualname__ = qualname

        func.__module__ = module
        return func

    def _update_default_kwargs(self, parent, provided):
        for func_name, defaults in self.default_args.items():
            default_args, default_kwargs = defaults
            provided = set_default_kwargs(provided, func_name, **default_kwargs)
        return parent, provided

    def _ensure_functions(self, provided):
        functions = self._parse_provides_dict(self.provided_functions)
        if provided is None:
            provided = __module__  # noqa:F821
        for funcname, func in functions.items():
            func = self._ensure_function(provided, funcname, func)
            setattr(provided, funcname, func)
        return provided

    def _ensure_methods(self, provided):
        """Given a base class, a new name, and any number of functions to
        attach, turns those functions into classmethods, attaches them,
        and returns an updated class object.
        """
        if not self.is_class:
            return provided
        if not inspect.isclass(provided):
            raise TypeError("Provided argument is not a class: {0!r}".format(provided))
        methods = self._parse_provides_dict(
            self.provided_methods, prepend_arg_to_callables="self"
        )
        classmethods = self._parse_provides_dict(
            self.provided_classmethods, prepend_arg_to_callables="cls"
        )
        if not methods and not classmethods:
            return provided
        new_functions = provided.__dict__.copy()
        if classmethods:
            new_functions.update(classmethods)
        if methods:
            new_functions.update(methods)
        classname = provided.__name__
        if six.PY2:
            classname = classname.encode(sys.getdefaultencoding())
        type_ = type(classname, (provided,), new_functions)
        return type_

    @property
    def is_class(self):
        return self.import_type == ImportTypes.CLASS

    @property
    def is_module(self):
        return self.import_type == ImportTypes.MODULE

    @property
    def is_method(self):
        return self.import_type == ImportTypes.METHOD

    @property
    def is_function(self):
        return self.import_type == ImportTypes.FUNCTION

    @property
    def is_contextmanager(self):
        return self.import_type == ImportTypes.CONTEXTMANAGER

    @property
    def is_attribute(self):
        return self.import_type == ImportTypes.ATTRIBUTE

    def __contains__(self, pip_version):
        # type: (str) -> bool
        return pip_version_lookup(pip_version) in self.version_range

    @property
    def is_valid(self):
        return self.version_range.is_valid()

    @property
    def sort_order(self):
        return 1 if self.is_valid else 0

    @classmethod
    def _shim_base(cls, imported, attribute_name):
        # type: (types.ModuleType, str) -> Any
        return getattr(imported, attribute_name, None)

    def shim_class(self, imported, attribute_name):
        # type: (types.ModuleType, str) -> Type
        result = self._shim_base(imported, attribute_name)
        if result is not None:
            imported, result = self._update_default_kwargs(imported, result)
            setattr(imported, attribute_name, result)
            result = self._ensure_methods(result)
            if self.provided_mixins:
                result = ShimmedPath._add_mixin(result, *self.provided_mixins)
            # setattr(imported, attribute_name, result)
            self._imported = imported
            self._provided = result
            # sys.modules[imported.__name__] = imported
            ShimmedPath.__modules[imported.__name__] = imported
        return result

    def shim_module(self, imported, attribute_name):
        # type: (types.ModuleType, str) -> types.ModuleType
        result = self._shim_base(imported, attribute_name)
        if result is not None:
            result = self._ensure_functions(result)
            imported, result = self._update_default_kwargs(imported, result)
            setattr(imported, attribute_name, result)
            self._imported = imported
            self._provided = result
            ShimmedPath.__modules[imported.__name__] = imported
        return result

    def shim_function(self, imported, attribute_name):
        # type: (types.ModuleType, str) -> Callable
        return self._shim_base(imported, attribute_name)

    def shim_attribute(self, imported, attribute_name):
        # type: (type.ModuleType, Any) -> Any
        return self._shim_base(imported, attribute_name)

    def shim_contextmanager(self, imported, attribute_name):
        # type: (types.ModuleType, str) -> Callable
        result = self._shim_base(imported, attribute_name)
        if result is None:
            result = nullcontext
        return result

    def shim(self):
        # type: (types.ModuleType) -> (Union[types.ModuleType, Callable, ContextManager, Type])
        imported = self._import()
        if self.is_class:
            return self.shim_class(imported, self.name_to_import)
        elif self.is_module:
            return self.shim_module(imported, self.name_to_import)
        elif self.is_contextmanager:
            return self.shim_contextmanager(imported, self.name_to_import)
        elif self.is_function:
            return self.shim_function(imported, self.name_to_import)
        elif self.is_attribute:
            return self.shim_attribute(imported, self.name_to_import)
        return self._shim_base(imported, self.name_to_import)

    def _import(self, prefix=None):
        # type: (Optional[str]) -> None
        # TODO: Decide whether to use _imported and _shimmed or to set the shimmed
        # always to _imported and never save the unshimmed module
        if self._imported is not None:
            return self._imported
        if prefix is None:
            current_pip = lookup_current_pip_version()
            prefix = current_pip.base_import_path
        return self._import_module(".".join([prefix, self.module_path]))

    def __hash__(self):
        # type: () -> int
        return hash(self._as_tuple())


class ShimmedPathCollection(object):

    __registry = {}

    def __init__(self, name, import_type, paths=None):
        # type: (str, str, ImportTypes, Optional[Iterable[ShimmedPath]])
        self.name = name
        self.import_type = import_type
        self.paths = set()
        if paths is not None:
            if isinstance(paths, six.string_types):
                self.paths.add(paths)
            else:
                self.paths.update(paths)
        self.top_path = None
        self._default = None
        self._default_args = {}  # type: Dict[str, List[List[Any], Dict[str, Any]]]
        self.provided_methods = {}
        self.provided_functions = {}
        self.provided_contextmanagers = {}
        self.provided_classmethods = {}
        self.provided_mixins = []
        self.register()

    def register(self):
        self.__registry[self.name] = self

    @classmethod
    def get_registry(cls):
        return cls.__registry.copy()

    def add_path(self, path):
        # type: (ShimmedPath) -> None
        self.paths.add(path)

    def set_default(self, default):
        # type: (Any) -> None
        if isinstance(default, (ShimmedPath, ShimmedPathCollection)):
            default = default.shim()
        try:
            default.__qualname__ = default.__name__ = self.name
        except AttributeError:
            pass
        self._default = default

    def set_default_args(self, callable_name, *args, **kwargs):
        # type: (str) -> None
        self._default_args.update({callable_name: [args, kwargs]})

    def provide_function(self, name, fn):
        # type: (str, Callable) -> None
        self.provided_functions[name] = fn

    def provide_method(self, name, fn):
        # type: (str, Callable) -> None
        if isinstance(fn, (ShimmedPath, ShimmedPathCollection)):
            fn = fn.shim()
        self.provided_methods[name] = fn

    def add_mixin(self, mixin):
        # type: (str, Optional[Union[Type, ShimmedPathCollection]]) -> None
        if isinstance(mixin, ShimmedPathCollection):
            mixin = mixin.shim()
        if mixin is not None:
            self.provided_mixins.append(mixin)

    def create_path(self, import_path, version_start, version_end=None):
        # type: (str, str, Optional[str]) -> None
        pip_version_start = pip_version_lookup(version_start)
        if version_end is None:
            version_end = "9999"
        pip_version_end = pip_version_lookup(version_end)
        version_range = PipVersionRange(pip_version_start, pip_version_end)
        new_path = ShimmedPath(
            self.name,
            import_path,
            self.import_type,
            version_range,
            self.provided_methods,
            self.provided_functions,
            self.provided_classmethods,
            self.provided_contextmanagers,
            self.provided_mixins,
            self._default_args,
        )
        self.add_path(new_path)

    def _sort_paths(self):
        return sorted(self.paths, key=operator.attrgetter("version_range"), reverse=True)

    def _get_top_path(self):
        return next(iter(self._sort_paths()), self._default)

    @classmethod
    def traverse(cls, shim):
        if isinstance(shim, (ShimmedPath, ShimmedPathCollection)):
            result = shim.shim()
            return result
        return shim

    def shim(self):
        top_path = self._get_top_path()
        result = self.traverse(top_path)
        if result == top_path.nullcontext and self._default is not None:
            default_result = self.traverse(self._default)
            if default_result:
                return default_result
        if result is not None:
            return result
        if self._default is not None:
            return self.traverse(self._default)


_strip_extras = ShimmedPathCollection("_strip_extras", ImportTypes.FUNCTION)
_strip_extras.create_path("req.req_install._strip_extras", "7.0.0", "18.0.0")
_strip_extras.create_path("req.constructors._strip_extras", "18.1.0")

cmdoptions = ShimmedPathCollection("cmdoptions", ImportTypes.MODULE)
cmdoptions.create_path("cli.cmdoptions", "18.1", "9999")
cmdoptions.create_path("cmdoptions", "7.0.0", "18.0")

SessionCommandMixin = ShimmedPathCollection("SessionCommandMixin", ImportTypes.CLASS)
SessionCommandMixin.create_path("cli.req_command.SessionCommandMixin", "19.3.0", "9999")

Command = ShimmedPathCollection("Command", ImportTypes.CLASS)
Command.set_default_args("__init__", name="PipCommand", summary="Default pip command.")
Command.add_mixin(SessionCommandMixin)
Command.create_path("cli.base_command.Command", "18.1", "9999")
Command.create_path("basecommand.Command", "7.0.0", "18.0")

ConfigOptionParser = ShimmedPathCollection("ConfigOptionParser", ImportTypes.CLASS)
ConfigOptionParser.create_path("cli.parser.ConfigOptionParser", "18.1", "9999")
ConfigOptionParser.create_path("baseparser.ConfigOptionParser", "7.0.0", "18.0")

InstallCommand = ShimmedPathCollection("InstallCommand", ImportTypes.CLASS)
InstallCommand.create_path("commands.install.InstallCommand", "7.0.0", "9999")

DistributionNotFound = ShimmedPathCollection("DistributionNotFound", ImportTypes.CLASS)
DistributionNotFound.create_path("exceptions.DistributionNotFound", "7.0.0", "9999")

FAVORITE_HASH = ShimmedPathCollection("FAVORITE_HASH", ImportTypes.ATTRIBUTE)
FAVORITE_HASH.create_path("utils.hashes.FAVORITE_HASH", "7.0.0", "9999")

FormatControl = ShimmedPathCollection("FormatControl", ImportTypes.CLASS)
FormatControl.create_path("models.format_control.FormatControl", "18.1", "9999")
FormatControl.create_path("index.FormatControl", "7.0.0", "18.0")

FrozenRequirement = ShimmedPathCollection("FrozenRequirement", ImportTypes.CLASS)
FrozenRequirement.create_path("FrozenRequirement", "7.0.0", "9.0.3")
FrozenRequirement.create_path("operations.freeze.FrozenRequirement", "10.0.0", "9999")

get_installed_distributions = ShimmedPathCollection(
    "get_installed_distributions", ImportTypes.FUNCTION
)
get_installed_distributions.create_path(
    "utils.misc.get_installed_distributions", "10", "9999"
)
get_installed_distributions.create_path("utils.get_installed_distributions", "7", "9.0.3")

get_supported = ShimmedPathCollection("get_supported", ImportTypes.FUNCTION)
get_supported.create_path("pep425tags.get_supported", "7.0.0", "9999")

get_tags = ShimmedPathCollection("get_tags", ImportTypes.FUNCTION)
get_tags.create_path("pep425tags.get_tags", "7.0.0", "9999")

index_group = ShimmedPathCollection("index_group", ImportTypes.FUNCTION)
index_group.create_path("cli.cmdoptions.index_group", "18.1", "9999")
index_group.create_path("cmdoptions.index_group", "7.0.0", "18.0")

InstallationError = ShimmedPathCollection("InstallationError", ImportTypes.CLASS)
InstallationError.create_path("exceptions.InstallationError", "7.0.0", "9999")

UninstallationError = ShimmedPathCollection("UninstallationError", ImportTypes.CLASS)
UninstallationError.create_path("exceptions.UninstallationError", "7.0.0", "9999")

DistributionNotFound = ShimmedPathCollection("DistributionNotFound", ImportTypes.CLASS)
DistributionNotFound.create_path("exceptions.DistributionNotFound", "7.0.0", "9999")

RequirementsFileParseError = ShimmedPathCollection(
    "RequirementsFileParseError", ImportTypes.CLASS
)
RequirementsFileParseError.create_path(
    "exceptions.RequirementsFileParseError", "7.0.0", "9999"
)

BestVersionAlreadyInstalled = ShimmedPathCollection(
    "BestVersionAlreadyInstalled", ImportTypes.CLASS
)
BestVersionAlreadyInstalled.create_path(
    "exceptions.BestVersionAlreadyInstalled", "7.0.0", "9999"
)

BadCommand = ShimmedPathCollection("BadCommand", ImportTypes.CLASS)
BadCommand.create_path("exceptions.BadCommand", "7.0.0", "9999")

CommandError = ShimmedPathCollection("CommandError", ImportTypes.CLASS)
CommandError.create_path("exceptions.CommandError", "7.0.0", "9999")

PreviousBuildDirError = ShimmedPathCollection("PreviousBuildDirError", ImportTypes.CLASS)
PreviousBuildDirError.create_path("exceptions.PreviousBuildDirError", "7.0.0", "9999")

install_req_from_editable = ShimmedPathCollection(
    "install_req_from_editable", ImportTypes.FUNCTION
)
install_req_from_editable.create_path(
    "req.constructors.install_req_from_editable", "18.1", "9999"
)
install_req_from_editable.create_path(
    "req.req_install.InstallRequirement.from_editable", "7.0.0", "18.0"
)

install_req_from_line = ShimmedPathCollection(
    "install_req_from_line", ImportTypes.FUNCTION
)
install_req_from_line.create_path(
    "req.constructors.install_req_from_line", "18.1", "9999"
)
install_req_from_line.create_path(
    "req.req_install.InstallRequirement.from_line", "7.0.0", "18.0"
)

install_req_from_req_string = ShimmedPathCollection(
    "install_req_from_req_string", ImportTypes.FUNCTION
)
install_req_from_req_string.create_path(
    "req.constructors.install_req_from_req_string", "19.0", "9999"
)

InstallRequirement = ShimmedPathCollection("InstallRequirement", ImportTypes.CLASS)
InstallRequirement.provide_method("from_line", install_req_from_line)
InstallRequirement.provide_method("from_editable", install_req_from_editable)
InstallRequirement.create_path("req.req_install.InstallRequirement", "7.0.0", "9999")

is_archive_file = ShimmedPathCollection("is_archive_file", ImportTypes.FUNCTION)
is_archive_file.create_path("req.constructors.is_archive_file", "19.3", "9999")
is_archive_file.create_path("download.is_archive_file", "7.0.0", "19.2.3")

is_file_url = ShimmedPathCollection("is_file_url", ImportTypes.FUNCTION)
is_file_url.set_default(fallback_is_file_url)
is_file_url.create_path("download.is_file_url", "7.0.0", "19.2.3")

unpack_url = ShimmedPathCollection("unpack_url", ImportTypes.FUNCTION)
unpack_url.create_path("download.unpack_url", "7.0.0", "19.3.9")
unpack_url.create_path("operations.prepare.unpack_url", "20.0", "9999")

is_installable_dir = ShimmedPathCollection("is_installable_dir", ImportTypes.FUNCTION)
is_installable_dir.create_path("utils.misc.is_installable_dir", "10.0.0", "9999")
is_installable_dir.create_path("utils.is_installable_dir", "7.0.0", "9.0.3")

Link = ShimmedPathCollection("Link", ImportTypes.CLASS)
Link.create_path("models.link.Link", "19.0.0", "9999")
Link.create_path("index.Link", "7.0.0", "18.1")

make_abstract_dist = ShimmedPathCollection("make_abstract_dist", ImportTypes.FUNCTION)
make_abstract_dist.create_path(
    "distributions.make_distribution_for_install_requirement", "19.1.2", "9999"
)
make_abstract_dist.create_path(
    "operations.prepare.make_abstract_dist", "10.0.0", "19.1.1"
)
make_abstract_dist.create_path("req.req_set.make_abstract_dist", "7.0.0", "9.0.3")

make_distribution_for_install_requirement = ShimmedPathCollection(
    "make_distribution_for_install_requirement", ImportTypes.CLASS
)
make_distribution_for_install_requirement.create_path(
    "distributions.make_distribution_for_install_requirement", "19.1.2", "9999"
)

make_option_group = ShimmedPathCollection("make_option_group", ImportTypes.FUNCTION)
make_option_group.create_path("cli.cmdoptions.make_option_group", "18.1", "9999")
make_option_group.create_path("cmdoptions.make_option_group", "7.0.0", "18.0")

PackageFinder = ShimmedPathCollection("PackageFinder", ImportTypes.CLASS)
PackageFinder.create_path("index.PackageFinder", "7.0.0", "19.9")
PackageFinder.create_path("index.package_finder.PackageFinder", "20.0", "9999")

CandidateEvaluator = ShimmedPathCollection("CandidateEvaluator", ImportTypes.CLASS)
CandidateEvaluator.set_default(backports.CandidateEvaluator)
CandidateEvaluator.create_path("index.CandidateEvaluator", "19.1.0", "19.3.9")
CandidateEvaluator.create_path("index.package_finder.CandidateEvaluator", "20.0", "9999")

CandidatePreferences = ShimmedPathCollection("CandidatePreferences", ImportTypes.CLASS)
CandidatePreferences.set_default(backports.CandidatePreferences)
CandidatePreferences.create_path("index.CandidatePreferences", "19.2.0", "19.9")
CandidatePreferences.create_path(
    "index.package_finder.CandidatePreferences", "20.0", "9999"
)

LinkCollector = ShimmedPathCollection("LinkCollector", ImportTypes.CLASS)
LinkCollector.set_default(backports.LinkCollector)
LinkCollector.create_path("collector.LinkCollector", "19.3.0", "19.9")
LinkCollector.create_path("index.collector.LinkCollector", "20.0", "9999")

LinkEvaluator = ShimmedPathCollection("LinkEvaluator", ImportTypes.CLASS)
LinkEvaluator.set_default(backports.LinkEvaluator)
LinkEvaluator.create_path("index.LinkEvaluator", "19.2.0", "19.9")
LinkEvaluator.create_path("index.package_finder.LinkEvaluator", "20.0", "9999")

TargetPython = ShimmedPathCollection("TargetPython", ImportTypes.CLASS)
backports.TargetPython.fallback_get_tags = get_tags
TargetPython.set_default(backports.TargetPython)
TargetPython.create_path("models.target_python.TargetPython", "19.2.0", "9999")

SearchScope = ShimmedPathCollection("SearchScope", ImportTypes.CLASS)
SearchScope.set_default(backports.SearchScope)
SearchScope.create_path("models.search_scope.SearchScope", "19.2.0", "9999")

SelectionPreferences = ShimmedPathCollection("SelectionPreferences", ImportTypes.CLASS)
SelectionPreferences.set_default(backports.SelectionPreferences)
SelectionPreferences.create_path(
    "models.selection_prefs.SelectionPreferences", "19.2.0", "9999"
)

parse_requirements = ShimmedPathCollection("parse_requirements", ImportTypes.FUNCTION)
parse_requirements.create_path("req.req_file.parse_requirements", "7.0.0", "9999")

path_to_url = ShimmedPathCollection("path_to_url", ImportTypes.FUNCTION)
path_to_url.create_path("download.path_to_url", "7.0.0", "19.2.3")
path_to_url.create_path("utils.urls.path_to_url", "19.3.0", "9999")

PipError = ShimmedPathCollection("PipError", ImportTypes.CLASS)
PipError.create_path("exceptions.PipError", "7.0.0", "9999")

RequirementPreparer = ShimmedPathCollection("RequirementPreparer", ImportTypes.CLASS)
RequirementPreparer.create_path("operations.prepare.RequirementPreparer", "7", "9999")

RequirementSet = ShimmedPathCollection("RequirementSet", ImportTypes.CLASS)
RequirementSet.create_path("req.req_set.RequirementSet", "7.0.0", "9999")

RequirementTracker = ShimmedPathCollection(
    "RequirementTracker", ImportTypes.CONTEXTMANAGER
)
RequirementTracker.create_path("req.req_tracker.RequirementTracker", "7.0.0", "9999")

TempDirectory = ShimmedPathCollection("TempDirectory", ImportTypes.CLASS)
TempDirectory.create_path("utils.temp_dir.TempDirectory", "7.0.0", "9999")

get_requirement_tracker = ShimmedPathCollection(
    "get_requirement_tracker", ImportTypes.CONTEXTMANAGER
)
get_requirement_tracker.set_default(
    lambda: backports.get_requirement_tracker(
        TempDirectory.shim(), RequirementTracker.shim()
    )
)
get_requirement_tracker.create_path(
    "req.req_tracker.get_requirement_tracker", "7.0.0", "9999"
)

Resolver = ShimmedPathCollection("Resolver", ImportTypes.CLASS)
Resolver.create_path("resolve.Resolver", "7.0.0", "19.1.1")
Resolver.create_path("legacy_resolve.Resolver", "19.1.2", "9999")

SafeFileCache = ShimmedPathCollection("SafeFileCache", ImportTypes.CLASS)
SafeFileCache.create_path("network.cache.SafeFileCache", "19.3.0", "9999")
SafeFileCache.create_path("download.SafeFileCache", "7.0.0", "19.2.3")

UninstallPathSet = ShimmedPathCollection("UninstallPathSet", ImportTypes.CLASS)
UninstallPathSet.create_path("req.req_uninstall.UninstallPathSet", "7.0.0", "9999")

url_to_path = ShimmedPathCollection("url_to_path", ImportTypes.FUNCTION)
url_to_path.create_path("download.url_to_path", "7.0.0", "19.2.3")
url_to_path.create_path("utils.urls.url_to_path", "19.3.0", "9999")

USER_CACHE_DIR = ShimmedPathCollection("USER_CACHE_DIR", ImportTypes.ATTRIBUTE)
USER_CACHE_DIR.create_path("locations.USER_CACHE_DIR", "7.0.0", "9999")

VcsSupport = ShimmedPathCollection("VcsSupport", ImportTypes.CLASS)
VcsSupport.create_path("vcs.VcsSupport", "7.0.0", "19.1.1")
VcsSupport.create_path("vcs.versioncontrol.VcsSupport", "19.2", "9999")

Wheel = ShimmedPathCollection("Wheel", ImportTypes.CLASS)
Wheel.create_path("wheel.Wheel", "7.0.0", "9999")

WheelCache = ShimmedPathCollection("WheelCache", ImportTypes.CLASS)
WheelCache.create_path("cache.WheelCache", "10.0.0", "9999")
WheelCache.create_path("wheel.WheelCache", "7", "9.0.3")

WheelBuilder = ShimmedPathCollection("WheelBuilder", ImportTypes.CLASS)
WheelBuilder.create_path("wheel.WheelBuilder", "7.0.0", "19.9")
WheelBuilder.create_path("wheel_builder.WheelBuilder", "20.0", "9999")

AbstractDistribution = ShimmedPathCollection("AbstractDistribution", ImportTypes.CLASS)
AbstractDistribution.create_path(
    "distributions.base.AbstractDistribution", "19.1.2", "9999"
)

InstalledDistribution = ShimmedPathCollection("InstalledDistribution", ImportTypes.CLASS)
InstalledDistribution.create_path(
    "distributions.installed.InstalledDistribution", "19.1.2", "9999"
)

SourceDistribution = ShimmedPathCollection("SourceDistribution", ImportTypes.CLASS)
SourceDistribution.create_path("req.req_set.IsSDist", "7.0.0", "9.0.3")
SourceDistribution.create_path("operations.prepare.IsSDist", "10.0.0", "19.1.1")
SourceDistribution.create_path(
    "distributions.source.SourceDistribution", "19.1.2", "19.2.3"
)
SourceDistribution.create_path(
    "distributions.source.legacy.SourceDistribution", "19.3.0", "19.9"
)
SourceDistribution.create_path("distributions.source.SourceDistribution", "20.0", "9999")

WheelDistribution = ShimmedPathCollection("WheelDistribution", ImportTypes.CLASS)
WheelDistribution.create_path("distributions.wheel.WheelDistribution", "19.1.2", "9999")

PyPI = ShimmedPathCollection("PyPI", ImportTypes.ATTRIBUTE)
PyPI.create_path("models.index.PyPI", "7.0.0", "9999")

stdlib_pkgs = ShimmedPathCollection("stdlib_pkgs", ImportTypes.ATTRIBUTE)
stdlib_pkgs.create_path("utils.compat.stdlib_pkgs", "18.1", "9999")
stdlib_pkgs.create_path("compat.stdlib_pkgs", "7", "18.0")

DEV_PKGS = ShimmedPathCollection("DEV_PKGS", ImportTypes.ATTRIBUTE)
DEV_PKGS.create_path("commands.freeze.DEV_PKGS", "9.0.0", "9999")
DEV_PKGS.set_default({"setuptools", "pip", "distribute", "wheel"})
