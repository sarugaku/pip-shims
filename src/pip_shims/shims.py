# -*- coding=utf-8 -*-
from collections import namedtuple
from contextlib import contextmanager
import importlib
import os
import sys


class _shims(object):
    CURRENT_PIP_VERSION  = "18.1"
    BASE_IMPORT_PATH = os.environ.get("PIP_SHIMS_BASE_MODULE", "pip")
    path_info = namedtuple("PathInfo", "path start_version end_version")

    def __dir__(self):
        result = list(self._locations.keys()) + list(self.__dict__.keys())
        result.extend(('__file__', '__doc__', '__all__',
                       '__docformat__', '__name__', '__path__',
                       '__package__', '__version__'))
        return result

    @classmethod
    def _new(cls):
        return cls()

    @property
    def __all__(self):
        return list(self._locations.keys())

    def __init__(self):
        from .utils import _parse, get_package, STRING_TYPES
        self._parse = _parse
        self.get_package = get_package
        self.STRING_TYPES = STRING_TYPES
        self._modules = {}
        self._modules["pip"] = importlib.import_module("pip")
        self.pip_version = getattr(self._modules["pip"], "__version__")
        self.parsed_pip_version = self._parse(self.pip_version)
        self._contextmanagers = ("RequirementTracker",)
        self._moves = {
            "InstallRequirement": {
                "from_editable": "install_req_from_editable",
                "from_line": "install_req_from_line",
            }
        }
        self._locations = {
            "parse_version": ("index.parse_version", "7", "9999"),
            "_strip_extras": (
                ("req.req_install._strip_extras", "7", "18.0"),
                ("req.constructors._strip_extras", "18.1", "9999"),
            ),
            "cmdoptions": (
                ("cli.cmdoptions", "18.1", "9999"),
                ("cmdoptions", "7.0.0", "18.0")
            ),
            "Command": (
                ("cli.base_command.Command", "18.1", "9999"),
                ("basecommand.Command", "7.0.0", "18.0")
            ),
            "ConfigOptionParser": (
                ("cli.parser.ConfigOptionParser", "18.1", "9999"),
                ("baseparser.ConfigOptionParser", "7.0.0", "18.0")
            ),
            "DistributionNotFound": ("exceptions.DistributionNotFound", "7.0.0", "9999"),
            "FAVORITE_HASH": ("utils.hashes.FAVORITE_HASH", "7.0.0", "9999"),
            "FormatControl": (
                ("models.format_control.FormatControl", "18.1", "9999"),
                ("index.FormatControl", "7.0.0", "18.0"),
            ),
            "get_installed_distributions": (
                ("utils.misc.get_installed_distributions", "10", "9999"),
                ("utils.get_installed_distributions", "7", "9.0.3")
            ),
            "index_group": (
                ("cli.cmdoptions.index_group", "18.1", "9999"),
                ("cmdoptions.index_group", "7.0.0", "18.0")
            ),
            "InstallRequirement": ("req.req_install.InstallRequirement", "7.0.0", "9999"),
            "install_req_from_editable": (
                "req.constructors.install_req_from_editable", "7.0.0", "9999"
            ),
            "install_req_from_line": (
                "req.constructors.install_req_from_line", "7.0.0", "9999"
            ),
            "is_archive_file": ("download.is_archive_file", "7.0.0", "9999"),
            "is_file_url": ("download.is_file_url", "7.0.0", "9999"),
            "unpack_url": ("download.unpack_url", "7.0.0", "9999"),
            "is_installable_dir": (
                ("utils.misc.is_installable_dir", "10.0.0", "9999"),
                ("utils.is_installable_dir", "7.0.0", "9.0.3")
            ),
            "Link": ("index.Link", "7.0.0", "9999"),
            "make_abstract_dist": (
                ("operations.prepare.make_abstract_dist", "10.0.0", "9999"),
                ("req.req_set.make_abstract_dist", "7.0.0", "9.0.3")
            ),
            "make_option_group": (
                ("cli.cmdoptions.make_option_group", "18.1", "9999"),
                ("cmdoptions.make_option_group", "7.0.0", "18.0")
            ),
            "PackageFinder": ("index.PackageFinder", "7.0.0", "9999"),
            "parse_requirements": ("req.req_file.parse_requirements", "7.0.0", "9999"),
            "parse_version": ("index.parse_version", "7.0.0", "9999"),
            "path_to_url": ("download.path_to_url", "7.0.0", "9999"),
            "PipError": ("exceptions.PipError", "7.0.0", "9999"),
            "RequirementPreparer": ("operations.prepare.RequirementPreparer", "7", "9999"),
            "RequirementSet": ("req.req_set.RequirementSet", "7.0.0", "9999"),
            "RequirementTracker": ("req.req_tracker.RequirementTracker", "7.0.0", "9999"),
            "Resolver": ("resolve.Resolver", "7.0.0", "9999"),
            "SafeFileCache": ("download.SafeFileCache", "7.0.0", "9999"),
            "UninstallPathSet": ("req.req_uninstall.UninstallPathSet", "7.0.0", "9999"),
            "url_to_path": ("download.url_to_path", "7.0.0", "9999"),
            "USER_CACHE_DIR": ("locations.USER_CACHE_DIR", "7.0.0", "9999"),
            "VcsSupport": ("vcs.VcsSupport", "7.0.0", "9999"),
            "Wheel": ("wheel.Wheel", "7.0.0", "9999"),
            "WheelCache": (
                ("cache.WheelCache", "10.0.0", "9999"),
                ("wheel.WheelCache", "7", "9.0.3")
            ),
            "WheelBuilder": ("wheel.WheelBuilder", "7.0.0", "9999"),
        }

    def _ensure_method(self, cls, classname, method_name, function):
        if getattr(cls, method_name, None):
            return cls
        type_ = type(
            classname,
            (cls,),
            {method_name: function},
        )
        return type_

    def _get_module_paths(self, module, base_path=None):
        if not base_path:
            base_path = self.BASE_IMPORT_PATH
        module = self._locations[module]
        if not isinstance(next(iter(module)), (tuple, list)):
            module_paths = self.get_pathinfo(module)
        else:
            module_paths = [self.get_pathinfo(pth) for pth in self._locations[module]]
        return self.sort_paths(module_paths, base_path)

    def __getattr__(self, *args, **kwargs):
        locations = super(_shims, self).__getattribute__("_locations")
        contextmanagers = super(_shims, self).__getattribute__("_contextmanagers")
        moves = super(_shims, self).__getattribute__("_moves")
        if args[0] in locations:
            module_paths = self._get_module_paths(args[0])
            modules_with_packages = list(filter(
                None, [(m, pkg) for m, pkg in map(self.get_package, module_paths)]
            ))
            moved = [
                (base, package) for base, package in modules_with_packages
                if package in moves.keys()
            ]
            moved_package = None
            if moved:
                moved_package = moved[0]
            if moved_package:
                import vistir
                old_base, old_target = moved_package
                old_import = self._import(locations[old_target])
                mapped_imports = sorted(set([
                    (method, new_location) for method, new_location
                    in moves[old_target].items()
                ]))

                new_imports = list(filter(None, [
                    self._import(locations[new_location[1]])
                    for new_location in mapped_imports
                ]))
                imported = old_import
                for i, _import in enumerate(new_imports):
                    if getattr(old_import, "__class__", "") == type:
                        @classmethod
                        def _new_method(cls, name, **kwargs):
                            return _import(name, **kwargs)
                        imported = self._ensure_method(old_import, old_target, mapped_imports[i][0], _new_method)
                        self._modules[mapped_imports[i][1]] = imported
                if imported:
                    return imported
            else:
                imported = self._import(locations[args[0]])
                if not imported and args[0] in contextmanagers:
                    return self.nullcontext
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
        imports = [
            getattr(m, pkg, self.none_or_ctxmanager(pkg)) for pkg, m in modules
            if m is not None
        ]
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
        return self.path_info(module_path, self._parse(start_version), self._parse(end_version))


old_module = sys.modules[__name__] if __name__ in sys.modules else None
module = sys.modules[__name__] = _shims()
module.__dict__.update({
    '__file__': __file__,
    '__package__': __package__,
    '__doc__': __doc__,
    '__all__': module.__all__,
    '__name__': __name__
})
