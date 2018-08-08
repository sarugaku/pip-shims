# -*- coding=utf-8 -*-
import sys

has_modutil = False
if sys.version_info[:2] >= (3, 7):
    try:
        import modutil
    except ImportError:
        has_modutil = False
    else:
        has_modutil = True


def get_package(module, subimport=None):
    package = None
    if subimport:
        package = subimport
    else:
        module, _, package = module.rpartition(".")
    return module, package


def do_import(module_path, subimport=None, old_path=None, base_path="pip"):
    old_path = old_path or module_path
    prefixes = [pth.format(base_path) for pth in ["{0}._internal", "{0}"]]
    paths = [module_path, old_path]
    search_order = ["{0}.{1}".format(p, pth) for p in prefixes for pth in paths if pth is not None]
    imported = None
    if has_modutil:
        pkgs = [get_package(pkg, subimport) for pkg in search_order]
        imports = [modutil.lazy_import(__name__, {to_import,}) for to_import, pkg in pkgs]
        imp_getattrs = [imp_getattr for mod, imp_getattr in imports]
        chained = modutil.chained___getattr__(__name__, *imp_getattrs)
        imported = None
        for to_import, pkg in pkgs:
            _, _, module_name = to_import.rpartition(".")
            try:
                imported = chained(module_name)
            except (modutil.ModuleAttributeError, ImportError):
                continue
            else:
                return getattr(imported, pkg)
        if not imported:
            return
        return imported
    for to_import in search_order:
        to_import, package = get_package(to_import, subimport)
        try:
            imported = importlib.import_module(to_import)
        except ImportError:
            continue
        else:
            return getattr(imported, package)
    return imported


_strip_extras = do_import("req.req_install", "_strip_extras")
cmdoptions = do_import("cli.cmdoptions", old_path="cmdoptions")
Command = do_import("cli.base_command", "Command", old_path="basecommand")
ConfigOptionParser = do_import("cli.parser", "ConfigOptionParser", old_path="baseparser")
DistributionNotFound = do_import("exceptions", "DistributionNotFound")
FAVORITE_HASH = do_import("utils.hashes", "FAVORITE_HASH")
FormatControl = do_import("index", "FormatControl")
get_installed_distributions = do_import('utils.misc', 'get_installed_distributions', old_path='utils')
index_group = do_import("cli.cmdoptions", "index_group", old_path="cmdoptions")
InstallRequirement = do_import("req.req_install", "InstallRequirement")
is_archive_file = do_import("download", "is_archive_file")
is_file_url = do_import("download", "is_file_url")
is_installable_dir = do_import("utils.misc", "is_installable_dir", old_path="utils")
Link = do_import("index", "Link")
make_abstract_dist = do_import("operations.prepare", "make_abstract_dist", old_path="req.req_set")
make_option_group = do_import("cli.cmdoptions", "make_option_group", old_path="cmdoptions")
PackageFinder = do_import("index", "PackageFinder")
parse_requirements = do_import("req.req_file", "parse_requirements")
parse_version = do_import("index", "parse_version")
path_to_url = do_import("download", "path_to_url")
pip_version = do_import("__version__")
PipError = do_import("exceptions", "PipError")
RequirementPreparer = do_import("operations.prepare", "RequirementPreparer")
RequirementSet = do_import("req.req_set", "RequirementSet")
RequirementTracker = do_import("req.req_tracker", "RequirementTracker")
Resolver = do_import("resolve", "Resolver")
SafeFileCache = do_import("download", "SafeFileCache")
url_to_path = do_import("download", "url_to_path")
USER_CACHE_DIR = do_import("locations", "USER_CACHE_DIR")
VcsSupport = do_import("vcs", "VcsSupport")
Wheel = do_import("wheel", "Wheel")
WheelCache = do_import("cache", "WheelCache")


if not RequirementTracker:
    @contextmanager
    def RequirementTracker():
        yield
