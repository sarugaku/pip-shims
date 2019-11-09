# -*- coding=utf-8 -*-
import importlib
import inspect
import os
import sys
import types
from collections import namedtuple
from contextlib import contextmanager
from functools import partial

import six

# format: off
six.add_move(six.MovedAttribute("Callable", "collections", "collections.abc"))  # noqa
from six.moves import Callable  # type: ignore  # noqa  # isort:skip

# format: on


class _shims(types.ModuleType):
    CURRENT_PIP_VERSION = "19.3.1"
    BASE_IMPORT_PATH = os.environ.get("PIP_SHIMS_BASE_MODULE", "pip")
    path_info = namedtuple("PathInfo", "path start_version end_version")

    @classmethod
    def parse_version(cls, version):
        pkging_version = importlib.import_module("pip._vendor.packaging.version")
        return pkging_version.parse(version)

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

    @staticmethod
    def _override_cls(basecls, method, **default_kwargs):
        target_method = getattr(basecls, method, None)
        if target_method is None:
            return basecls
        inspected_args = inspect.getargs(target_method.__code__)
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
            new_defaults = prepended_defaults + target_method.__func__.__defaults__
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

    @staticmethod
    def add_proxy_create(basecls):
        base_dict = basecls.__dict__.copy()
        if "create" not in base_dict:
            init = base_dict.get("__init__", None)

            def create(cls, *args, **kwargs):
                return cls(*args, **kwargs)

            if init:
                create.__module__ = init.__module__
                create.__qualname__ = init.__qualname__.replace("__init__", "create")
            base_dict["create"] = classmethod(create)
        return type(basecls.__name__, (basecls,), base_dict)

    @property
    def __all__(self):
        return list(self._locations.keys())

    def __init__(self):
        # from .utils import _parse, get_package, STRING_TYPES
        from . import utils

        self.utils = utils
        self._parse = utils._parse
        self.get_package = utils.get_package
        self.STRING_TYPES = utils.STRING_TYPES
        self._modules = {
            "pip": importlib.import_module(self.BASE_IMPORT_PATH),
            "pip_shims.utils": utils,
        }
        self.pip_version = getattr(self._modules["pip"], "__version__")
        version_types = ["post", "pre", "dev", "rc"]
        if any(post in self.pip_version.rsplit(".")[-1] for post in version_types):
            self.pip_version, _, _ = self.pip_version.rpartition(".")
        self.parsed_pip_version = self._parse(self.pip_version)
        self._contextmanagers = ("RequirementTracker",)
        self._class_updates = {
            "Command": {
                "_override_cls": [
                    "__init__",
                    {"name": "PipCommand", "summary": "The default pip command."},
                ],
                "_add_mixin": ["SessionCommandMixin",],  # noqa:E231
            },
        }
        self._moves = {
            "InstallRequirement": {
                "from_editable": "install_req_from_editable",
                "from_line": "install_req_from_line",
            },
        }
        self._shim_functions = {
            "is_file_url": lambda link: link.url.lower().startswith("file:")
        }
        self._locations = {
            "_strip_extras": (
                ("req.req_install._strip_extras", "7", "18.0"),
                ("req.constructors._strip_extras", "18.1", "9999"),
            ),
            "cmdoptions": (
                ("cli.cmdoptions", "18.1", "9999"),
                ("cmdoptions", "7.0.0", "18.0"),
            ),
            "SessionCommandMixin": (
                "cli.req_command.SessionCommandMixin",
                "19.3.0",
                "9999",
            ),
            "Command": (
                ("cli.base_command.Command", "18.1", "9999"),
                ("basecommand.Command", "7.0.0", "18.0"),
            ),
            "ConfigOptionParser": (
                ("cli.parser.ConfigOptionParser", "18.1", "9999"),
                ("baseparser.ConfigOptionParser", "7.0.0", "18.0"),
            ),
            "DistributionNotFound": ("exceptions.DistributionNotFound", "7.0.0", "9999"),
            "FAVORITE_HASH": ("utils.hashes.FAVORITE_HASH", "7.0.0", "9999"),
            "FormatControl": (
                ("models.format_control.FormatControl", "18.1", "9999"),
                ("index.FormatControl", "7.0.0", "18.0"),
            ),
            "FrozenRequirement": (
                ("FrozenRequirement", "7.0.0", "9.0.3"),
                ("operations.freeze.FrozenRequirement", "10.0.0", "9999"),
            ),
            "get_installed_distributions": (
                ("utils.misc.get_installed_distributions", "10", "9999"),
                ("utils.get_installed_distributions", "7", "9.0.3"),
            ),
            "index_group": (
                ("cli.cmdoptions.index_group", "18.1", "9999"),
                ("cmdoptions.index_group", "7.0.0", "18.0"),
            ),
            "InstallRequirement": ("req.req_install.InstallRequirement", "7.0.0", "9999"),
            "InstallationError": ("exceptions.InstallationError", "7.0.0", "9999"),
            "UninstallationError": ("exceptions.UninstallationError", "7.0.0", "9999"),
            "DistributionNotFound": ("exceptions.DistributionNotFound", "7.0.0", "9999"),
            "RequirementsFileParseError": (
                "exceptions.RequirementsFileParseError",
                "7.0.0",
                "9999",
            ),
            "BestVersionAlreadyInstalled": (
                "exceptions.BestVersionAlreadyInstalled",
                "7.0.0",
                "9999",
            ),
            "BadCommand": ("exceptions.BadCommand", "7.0.0", "9999"),
            "CommandError": ("exceptions.CommandError", "7.0.0", "9999"),
            "PreviousBuildDirError": (
                "exceptions.PreviousBuildDirError",
                "7.0.0",
                "9999",
            ),
            "install_req_from_editable": (
                ("req.constructors.install_req_from_editable", "18.1", "9999"),
                ("req.req_install.InstallRequirement.from_editable", "7.0.0", "18.0"),
            ),
            "install_req_from_line": (
                ("req.constructors.install_req_from_line", "18.1", "9999"),
                ("req.req_install.InstallRequirement.from_line", "7.0.0", "18.0"),
            ),
            "install_req_from_req_string": (
                "req.constructors.install_req_from_req_string",
                "19.0",
                "9999",
            ),
            "is_archive_file": (
                ("req.constructors.is_archive_file", "19.3", "9999"),
                ("download.is_archive_file", "7.0.0", "19.2.3"),
            ),
            "is_file_url": ("download.is_file_url", "7.0.0", "19.2.3",),
            "unpack_url": (
                ("download.unpack_url", "7.0.0", "19.3.9"),
                ("operations.prepare.unpack_url", "20.0", "9999"),
            ),
            "is_installable_dir": (
                ("utils.misc.is_installable_dir", "10.0.0", "9999"),
                ("utils.is_installable_dir", "7.0.0", "9.0.3"),
            ),
            "Link": (
                ("models.link.Link", "19.0.0", "9999"),
                ("index.Link", "7.0.0", "18.1"),
            ),
            "make_abstract_dist": (
                (
                    "distributions.make_distribution_for_install_requirement",
                    "19.1.2",
                    "9999",
                ),
                ("operations.prepare.make_abstract_dist", "10.0.0", "19.1.1"),
                ("req.req_set.make_abstract_dist", "7.0.0", "9.0.3"),
            ),
            "make_distribution_for_install_requirement": (
                "distributions.make_distribution_for_install_requirement",
                "19.1.2",
                "9999",
            ),
            "make_option_group": (
                ("cli.cmdoptions.make_option_group", "18.1", "9999"),
                ("cmdoptions.make_option_group", "7.0.0", "18.0"),
            ),
            "PackageFinder": (
                ("index.PackageFinder", "7.0.0", "19.9"),
                ("index.package_finder.PackageFinder", "20.0", "9999"),
            ),
            "CandidateEvaluator": (
                ("index.CandidateEvaluator", "19.1.0", "19.3.9"),
                ("index.package_finder.CandidateEvaluator", "20.0", "9999"),
            ),
            "CandidatePreferences": (
                ("index.CandidatePreferences", "19.2.0", "19.9"),
                ("index.package_finder.CandidatePreferences", "20.0", "9999"),
            ),
            "LinkCollector": (
                ("collector.LinkCollector", "19.3.0", "19.9"),
                ("index.collector.LinkCollector", "20.0", "9999"),
            ),
            "LinkEvaluator": (
                ("index.LinkEvaluator", "19.2.0", "19.9"),
                ("index.package_finder.LinkEvaluator", "20.0", "9999"),
            ),
            "TargetPython": ("models.target_python.TargetPython", "19.2.0", "9999"),
            "SearchScope": ("models.search_scope.SearchScope", "19.2.0", "9999"),
            "SelectionPreferences": (
                "models.selection_prefs.SelectionPreferences",
                "19.2.0",
                "9999",
            ),
            "parse_requirements": ("req.req_file.parse_requirements", "7.0.0", "9999"),
            "path_to_url": (
                ("download.path_to_url", "7.0.0", "19.2.3"),
                ("utils.urls.path_to_url", "19.3.0", "9999"),
            ),
            "PipError": ("exceptions.PipError", "7.0.0", "9999"),
            "RequirementPreparer": (
                "operations.prepare.RequirementPreparer",
                "7",
                "9999",
            ),
            "RequirementSet": ("req.req_set.RequirementSet", "7.0.0", "9999"),
            "RequirementTracker": ("req.req_tracker.RequirementTracker", "7.0.0", "9999"),
            "Resolver": (
                ("resolve.Resolver", "7.0.0", "19.1.1"),
                ("legacy_resolve.Resolver", "19.1.2", "9999"),
            ),
            "SafeFileCache": (
                ("network.cache.SafeFileCache", "19.3.0", "9999"),
                ("download.SafeFileCache", "7.0.0", "19.2.3"),
            ),
            "UninstallPathSet": ("req.req_uninstall.UninstallPathSet", "7.0.0", "9999"),
            "url_to_path": (
                ("download.url_to_path", "7.0.0", "19.2.3"),
                ("utils.urls.url_to_path", "19.3.0", "9999"),
            ),
            "USER_CACHE_DIR": ("locations.USER_CACHE_DIR", "7.0.0", "9999"),
            "VcsSupport": (
                ("vcs.VcsSupport", "7.0.0", "19.1.1"),
                ("vcs.versioncontrol.VcsSupport", "19.2", "9999"),
            ),
            "Wheel": ("wheel.Wheel", "7.0.0", "9999"),
            "WheelCache": (
                ("cache.WheelCache", "10.0.0", "9999"),
                ("wheel.WheelCache", "7", "9.0.3"),
            ),
            "WheelBuilder": (
                ("wheel.WheelBuilder", "7.0.0", "19.9"),
                ("wheel_builder.WheelBuilder", "20.0", "9999"),
            ),
            "AbstractDistribution": (
                "distributions.base.AbstractDistribution",
                "19.1.2",
                "9999",
            ),
            "InstalledDistribution": (
                "distributions.installed.InstalledDistribution",
                "19.1.2",
                "9999",
            ),
            "SourceDistribution": (
                ("req.req_set.IsSDist", "7.0.0", "9.0.3"),
                ("operations.prepare.IsSDist", "10.0.0", "19.1.1"),
                ("distributions.source.SourceDistribution", "19.1.2", "19.2.3"),
                ("distributions.source.legacy.SourceDistribution", "19.3.0", "19.9"),
                ("distributions.source.SourceDistribution", "20.0", "9999"),
            ),
            "WheelDistribution": (
                "distributions.wheel.WheelDistribution",
                "19.1.2",
                "9999",
            ),
            "PyPI": ("models.index.PyPI", "7.0.0", "9999"),
            "stdlib_pkgs": (
                ("utils.compat.stdlib_pkgs", "18.1", "9999"),
                ("compat.stdlib_pkgs", "7", "18.0"),
            ),
            "DEV_PKGS": (
                ("commands.freeze.DEV_PKGS", "9.0.0", "9999"),
                ({"setuptools", "pip", "distribute", "wheel"}, "7.0.0", "8.1.2"),
            ),
        }

    def _ensure_function(self, parent, funcname, func, is_prop=False, is_clsmethod=False):
        """Given a module, a function name, and a function
        object, attaches the given function to the module and
        ensures it is named properly according to the provided argument
        """
        qualname = funcname
        if parent is None:
            parent = self
        parent_is_module = inspect.ismodule(parent)
        parent_is_class = inspect.isclass(parent)
        module = None
        if parent_is_module:
            module = parent.__name__
        elif inspect.isclass(parent):
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
        if is_prop and parent_is_class:
            func = property(func)
        elif is_clsmethod and parent_is_class:
            func = classmethod(func)
        setattr(parent, funcname, func)
        # If function's direct parent is a module let's replace it
        # in our module cache and in the import cache
        if not parent_is_module and module is not None:
            if module in sys.modules:
                setattr(sys.modules[module], parent.__name__, parent)
            if module in self._modules:
                setattr(self._modules[module], parent.__name__, parent)
        else:
            self._modules[parent.__name__] = parent
            sys.modules[parent.__name__] = parent
        return parent, func

    def _ensure_methods(self, cls, classname, *methods):
        """Given a base class, a new name, and any number of functions to
        attach, turns those functions into classmethods, attaches them,
        and returns an updated class object.
        """
        method_names = [m[0] for m in methods]
        if all(getattr(cls, m, None) for m in method_names):
            return cls
        new_functions = {}

        class BaseFunc(Callable):
            def __init__(self, func_base, name, *args, **kwargs):
                self.func = func_base
                self.__name__ = self.__qualname__ = name

            def __call__(self, cls, *args, **kwargs):
                return self.func(*args, **kwargs)

        for method_name, fn in methods:
            new_functions[method_name] = classmethod(BaseFunc(fn, method_name))
        if six.PY2:
            classname = classname.encode(sys.getdefaultencoding())
        type_ = type(classname, (cls,), new_functions)
        return type_

    def _get_module_paths(self, module, base_path=None):
        """Given a module name and a base import path, provide
        a sorted list of possible unique import paths.

        :param str module: An package to import
        :param Optional[str] base_path: The base path to import, e.g. pip or 'fakepip'.
            This is mainly useful if you are vendoring pip.
        :returns: A list of import paths in order of import preference.
        """
        if not base_path:
            base_path = self.BASE_IMPORT_PATH
        module = self._locations[module]
        if not isinstance(next(iter(module)), (tuple, list)):
            module_paths = self.get_pathinfo(module)
        else:
            module_paths = [self.get_pathinfo(pth) for pth in module]
        return self.sort_paths(module_paths, base_path)

    def _get_remapped_methods(self, moved_package):
        """Given an import target, provide method mappings for any
        updated import paths.

        :param Tuple[str, str] moved_package: A 2-tuple of package location, import
            target.
        :returns: A pair of dictionaries mapping the old-to-new and new-to-old import
            path, including target, name, location, and modules.
        """
        original_base, original_target = moved_package
        original_import = self._import(self._locations[original_target])
        old_to_new = {}
        new_to_old = {}
        for method_name, new_method_name in self._moves.get(original_target, {}).items():
            module_paths = self._get_module_paths(new_method_name)
            target = next(
                iter(
                    sorted(set([tgt for mod, tgt in map(self.get_package, module_paths)]))
                ),
                None,
            )
            old_to_new[method_name] = {
                "target": target,
                "name": new_method_name,
                "location": self._locations[new_method_name],
                "module": self._import(self._locations[new_method_name]),
            }
            # XXX: If a move is indicated from e.g. CandidateEvaluator.__init__
            # XXX: to CandidateEvaluator.create (new), this will say the target
            # XXX: is 'CandidateEvaluator', the location is the module path,
            # XXX: the module itself is the originally imported module,
            # XXX: And we need to map 'create'
            new_to_old[new_method_name] = {
                "target": original_target,
                "name": method_name,
                "location": self._locations[original_target],
                "module": original_import,
            }
        return (old_to_new, new_to_old)

    def _import_moved_module(self, moved_package):
        """Given an import that has been moved over time, import it for the current
        version of pip and translate any requisite method or function locations.

        :param Tuple[str, str] moved_package: A 2-tuple describing the package and
            import path needed.
        :returns: An imported module.
        """
        old_to_new, new_to_old = self._get_remapped_methods(moved_package)
        imported = None
        method_map = []
        new_target = None
        for old_method, remapped in old_to_new.items():
            new_name = remapped["name"]
            new_target = new_to_old[new_name]["target"]
            if not imported:
                imported = self._modules[new_target] = new_to_old[new_name]["module"]
            method_map.append((old_method, remapped["module"]))
        if inspect.isclass(imported):
            imported = self._ensure_methods(imported, new_target, *method_map)
        self._modules[new_target] = imported
        if imported:
            return imported
        return

    def _check_moved_methods(self, search_pth, moves):
        """
        Given a search path and a dictionary mapping import locations (old and new),
        return the new location of the given import if it has been remapped.
        """
        module_paths = [
            self.get_package(pth) for pth in self._get_module_paths(search_pth)
        ]
        moved_methods = [
            (base, target_cls) for base, target_cls in module_paths if target_cls in moves
        ]
        return next(iter(moved_methods), None)

    def _import_with_override(self, target, imported):
        class_updates = super(_shims, self).__getattribute__("_class_updates")
        for update_method, method_args in class_updates[target].items():
            local_method = getattr(_shims, update_method)
            if update_method == "_override_cls":
                method, override_defaults = method_args
                imported = local_method(imported, method, **override_defaults)
            elif update_method == "_add_mixin":
                mixins = [getattr(self, arg) for arg in method_args]
                imported = local_method(imported, *mixins)
        return imported

    def __getattr__(self, *args, **kwargs):
        locations = super(_shims, self).__getattribute__("_locations")
        contextmanagers = super(_shims, self).__getattribute__("_contextmanagers")
        class_updates = super(_shims, self).__getattribute__("_class_updates")
        moves = super(_shims, self).__getattribute__("_moves")
        target = args[0]
        if target in locations:
            moved_package = self._check_moved_methods(target, moves)
            if moved_package:
                imported = self._import_moved_module(moved_package)
                if imported:
                    return imported
            else:
                imported = self._import(locations[target])
                if not imported and target in contextmanagers:
                    return self.nullcontext
                if inspect.isclass(imported) and target in class_updates:
                    imported = self._import_with_override(target, imported)
                return imported
        return super(_shims, self).__getattribute__(*args, **kwargs)

    def is_valid(self, path_info_tuple):
        if (
            path_info_tuple.start_version <= self.parsed_pip_version
            and path_info_tuple.end_version >= self.parsed_pip_version
        ):
            return 1
        return 0

    def sort_paths(self, module_paths, base_path):
        if not isinstance(module_paths, list):
            module_paths = [module_paths]
        prefix_order = [pth.format(base_path) for pth in ["{0}._internal", "{0}"]]
        # Pip 10 introduced the internal api division
        if self._parse(self.pip_version) < self._parse("10.0.0"):
            prefix_order = reversed(prefix_order)
        paths = sorted(module_paths, key=self.is_valid, reverse=True)
        search_order = [
            "{0}.{1}".format(p, pth.path)
            for p in prefix_order
            for pth in paths
            if pth is not None
        ]
        return search_order

    def import_module(self, module):
        if module in self._modules:
            return self._modules[module]
        if not isinstance(module, six.string_types):
            return module
        try:
            imported = importlib.import_module(module)
        except ImportError:
            imported = None
        else:
            self._modules[module] = imported
        return imported

    def none_or_ctxmanager(self, pkg_name):
        if pkg_name in self._contextmanagers:
            return self.nullcontext
        return None

    def get_package_from_modules(self, modules):
        modules = [
            (package_name, self.import_module(m))
            for m, package_name in map(self.get_package, modules)
        ]
        imports = []
        shim = None
        for pkg, m in modules:
            if pkg in self._shim_functions and shim is None:
                module, shim = self._ensure_function(m, pkg, self._shim_functions[pkg])
            if m is None:
                continue
            imported = getattr(m, pkg, self.none_or_ctxmanager(pkg))
            if imported is not None:
                imports.append(imported)
        if not imports and shim is not None:
            return shim
        return next(iter(imports), None)

    def _import(self, module_paths, base_path=None):
        if not base_path:
            base_path = self.BASE_IMPORT_PATH
        if not isinstance(next(iter(module_paths)), (tuple, list)):
            module_paths = self.get_pathinfo(module_paths)
        else:
            module_paths = [self.get_pathinfo(pth) for pth in module_paths]
        search_order = self.sort_paths(module_paths, base_path)
        return self.get_package_from_modules(search_order)

    def do_import(self, *args, **kwargs):
        return self._import(*args, **kwargs)

    @contextmanager
    def nullcontext(self, *args, **kwargs):
        try:
            yield
        finally:
            pass

    def get_pathinfo(self, module_path):
        assert isinstance(module_path, (list, tuple))
        module_path, start_version, end_version = module_path
        return self.path_info(
            module_path, self._parse(start_version), self._parse(end_version)
        )


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
