# -*- coding=utf-8 -*-
from __future__ import absolute_import

import contextlib
import functools
import inspect
import os
import sys

from packaging import specifiers

from .environment import MYPY_RUNNING
from .utils import get_method_args

try:
    from pip._vendor.contextlib2 import ExitStack
except ImportError:
    ExitStack = None

if MYPY_RUNNING:
    from optparse import Values
    from typing import Any, Callable, Iterator, List, Optional, Tuple, Type


class SearchScope(object):
    def __init__(self, find_links=None, index_urls=None):
        self.index_urls = index_urls if index_urls else []
        self.find_links = find_links

    @classmethod
    def create(cls, find_links=None, index_urls=None):
        if not index_urls:
            index_urls = ["https://pypi.org/simple"]
        return cls(find_links=find_links, index_urls=index_urls)


class SelectionPreferences(object):
    def __init__(
        self,
        allow_yanked=True,
        allow_all_prereleases=False,
        format_control=None,
        prefer_binary=False,
        ignore_requires_python=False,
    ):
        self.allow_yanked = allow_yanked
        self.allow_all_prereleases = allow_all_prereleases
        self.format_control = format_control
        self.prefer_binary = prefer_binary
        self.ignore_requires_python = ignore_requires_python


class TargetPython(object):
    fallback_get_tags = None  # type: Optional[Callable]

    def __init__(
        self,
        platform=None,  # type: Optional[str]
        py_version_info=None,  # type: Optional[Tuple[int, ...]]
        abi=None,  # type: Optional[str]
        implementation=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self._given_py_version_info = py_version_info
        if py_version_info is None:
            py_version_info = sys.version_info[:3]
        elif len(py_version_info) < 3:
            py_version_info += (3 - len(py_version_info)) * (0,)
        else:
            py_version_info = py_version_info[:3]
        py_version = ".".join(map(str, py_version_info[:2]))
        self.abi = abi
        self.implementation = implementation
        self.platform = platform
        self.py_version = py_version
        self.py_version_info = py_version_info
        self._valid_tags = None

    def get_tags(self):
        if self._valid_tags is None and self._fallback_get_tags:
            try:
                fallback_func = self._fallback_get_tags.shim()
            except AttributeError:
                fallback_func = self._fallback_get_tags
            versions = None
            if self._given_py_version_info:
                versions = ["".join(map(str, self._given_py_version_info[:2]))]
            self._valid_tags = fallback_func(
                versions=versions,
                platform=self.platform,
                abi=self.abi,
                impl=self.implementation,
            )
        return self._valid_tags


class CandidatePreferences(object):
    def __init__(self, prefer_binary=False, allow_all_prereleases=False):
        self.prefer_binary = prefer_binary
        self.allow_all_prereleases = allow_all_prereleases


class LinkCollector(object):
    def __init__(self, session=None, search_scope=None):
        self.session = session
        self.search_scope = search_scope


class CandidateEvaluator(object):
    @classmethod
    def create(
        cls,
        project_name,  # type: str
        target_python=None,  # type: Optional[TargetPython]
        prefer_binary=False,  # type: bool
        allow_all_prereleases=False,  # type: bool
        specifier=None,  # type: Optional[specifiers.BaseSpecifier]
        hashes=None,  # type: Optional[Any]
    ):
        if target_python is None:
            target_python = TargetPython()
        if specifier is None:
            specifier = specifiers.SpecifierSet()

        supported_tags = target_python.get_tags()

        return cls(
            project_name=project_name,
            supported_tags=supported_tags,
            specifier=specifier,
            prefer_binary=prefer_binary,
            allow_all_prereleases=allow_all_prereleases,
            hashes=hashes,
        )

    def __init__(
        self,
        project_name,  # type: str
        supported_tags,  # type: List[Any]
        specifier,  # type: specifiers.BaseSpecifier
        prefer_binary=False,  # type: bool
        allow_all_prereleases=False,  # type: bool
        hashes=None,  # type: Optional[Any]
    ):
        self._allow_all_prereleases = allow_all_prereleases
        self._hashes = hashes
        self._prefer_binary = prefer_binary
        self._project_name = project_name
        self._specifier = specifier
        self._supported_tags = supported_tags


class LinkEvaluator(object):
    def __init__(
        self,
        allow_yanked,
        project_name,
        canonical_name,
        formats,
        target_python,
        ignore_requires_python=False,
        ignore_compatibility=True,
    ):
        self._allow_yanked = allow_yanked
        self._canonical_name = canonical_name
        self._ignore_requires_python = ignore_requires_python
        self._formats = formats
        self._target_python = target_python
        self._ignore_compatibility = ignore_compatibility

        self.project_name = project_name


@contextlib.contextmanager
def temp_environ():
    """Allow the ability to set os.environ temporarily"""
    environ = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(environ)


@contextlib.contextmanager
def get_requirement_tracker(temp_directory_creator=None, req_tracker_creator=None):
    # type: () -> Iterator[Any]
    root = os.environ.get("PIP_REQ_TRACKER")
    if not req_tracker_creator:
        yield None
    else:
        _, req_tracker_args = get_method_args(req_tracker_creator.__init__)
        if not req_tracker_args or "root" not in req_tracker_args.args:
            with req_tracker_creator() as tracker:
                yield tracker
        else:
            with ExitStack() as ctx:
                if root is None:
                    root = ctx.enter_context(
                        temp_directory_creator(kind="req-tracker")
                    ).path
                    ctx.enter_context(temp_environ())
                    os.environ["PIP_REQ_TRACKER"] = root
                with req_tracker_creator(root) as tracker:
                    yield tracker


def partial_command(shimmed_path, cmd_mapping=None):
    # type: (Type, Optional[Any]) -> Any
    """
    Maps a default set of arguments across all members of a
    :class:`~pip_shims.models.ShimmedPath` instance, specifically for
    :class:`~pip._internal.command.Command` instances which need
    `summary` and `name` arguments.

    :param :class:`~pip_shims.models.ShimmedPath` shimmed_path:  A
        :class:`~pip_shims.models.ShimmedCollection` instance
    :param Any cmd_mapping: A reference to use for mapping against, e.g. an
        import that depends on pip also
    :return: A dictionary mapping new arguments to their default values
    :rtype: Dict[str, str]
    """
    basecls = shimmed_path.shim()
    if getattr(cmd_mapping, "shim"):
        resolved_cmd_mapping = cmd_mapping.shim()
    elif cmd_mapping is not None:
        resolved_cmd_mapping = cmd_mapping.copy()
    base_args = []
    for root_cls in basecls.mro():
        if root_cls.__name__ == "Command":
            _, root_init_args = get_method_args(root_cls.__init__)
            base_args = root_init_args.args
    needs_name_and_summary = any(arg in base_args for arg in ("name", "summary"))
    if not needs_name_and_summary:
        setattr(basecls, "name", shimmed_path.name)
        return basecls
    elif (
        not resolved_cmd_mapping
        and needs_name_and_summary
        and getattr(functools, "partialmethod", None)
    ):
        new_init = functools.partial(
            basecls.__init__, name=shimmed_path.name, summary="Summary"
        )
        setattr(basecls, "__init__", new_init)
    result = basecls
    for command_name, command_info in resolved_cmd_mapping.items():
        if getattr(command_info, "class_name", None) == shimmed_path.name:
            summary = getattr(command_info, "summary", "Command summary")
            result = functools.partial(basecls, command_name, summary)
            break
    return result


def get_package_finder(
    install_cmd,  # type: Callable
    options=None,  # type: Optional[Values]
    session=None,  # type: Optional[Any]
    platform=None,  # type: Optional[str]
    python_versions=None,  # type: Optional[Tuple[str, ...]]
    abi=None,  # type: Optional[str]
    implementation=None,  # type: Optional[str]
    target_python=None,  # type: Optional[Any]
    ignore_requires_python=None,  # type: Optional[bool]
    target_python_builder=None,  # type: Optional[Callable]
):
    # type: (...) -> Any
    """
    Build and return a :class:`~pip._internal.index.package_finder.PackageFinder`
    instance using the :class:`~pip._internal.commands.install.InstallCommand` helper
    method to construct the finder, shimmed with backports as needed for compatibility.

    :param install_cmd: A :class:`~pip._internal.commands.install.InstallCommand`
        instance which is used to generate the finder.
    :param optparse.Values options: An optional :class:`optparse.Values` instance
        generated by calling `install_cmd.parser.parse_args()` typically.
    :param session: An optional session instance, can be created by the `install_cmd`.
    :param Optional[str] platform: An optional platform string, e.g. linux_x86_64
    :param Optional[Tuple[str, ...]] python_versions: A tuple of 2-digit strings
        representing python versions, e.g. ("27", "35", "36", "37"...)
    :param Optional[str] abi: The target abi to support, e.g. "cp38"
    :param Optional[str] implementation: An optional implementation string for limiting
        searches to a specific implementation, e.g. "cp" or "py"
    :param target_python: A :class:`~pip._internal.models.target_python.TargetPython`
        instance (will be translated to alternate arguments if necessary on incompatible
        pip versions).
    :param Optional[bool] ignore_requires_python: Whether to ignore `requires_python`
        on resulting candidates, only valid after pip version 19.3.1
    :param target_python_builder: A 'TargetPython' builder (e.g. the class itself,
        uninstantiated)
    :return: A :class:`pip._internal.index.package_finder.PackageFinder` instance
    :rtype: :class:`pip._internal.index.package_finder.PackageFinder`
    """
    if options is None:
        options, _ = install_cmd.parser.parse_args([])
    if session is None:
        session = install_cmd._build_session(options)
    builder_args = inspect.getargs(install_cmd._build_package_finder.__code__)
    build_kwargs = {"options": options, "session": session}
    expects_targetpython = "target_python" in builder_args.args
    received_python = any(arg for arg in [platform, python_versions, abi, implementation])
    if expects_targetpython and received_python and not target_python:
        if target_python_builder is None:
            target_python_builder = TargetPython
        py_version_info = None
        if python_versions:
            py_version_info_python = max(python_versions)
            py_version_info = tuple([int(part) for part in py_version_info_python])
        target_python = target_python_builder(
            platform=platform,
            abi=abi,
            implementation=implementation,
            py_version_info=py_version_info,
        )
        build_kwargs["target_python"] = target_python
    elif any(
        arg in builder_args.args
        for arg in ["platform", "python_versions", "abi", "implementation"]
    ):
        if target_python and not received_python:
            tags = target_python.get_tags()
            version_impl = set([t[0] for t in tags])
            # impls = set([v[:2] for v in version_impl])
            # impls.remove("py")
            # impl = next(iter(impls), "py") if not target_python
            versions = set([v[2:] for v in version_impl])
            build_kwargs.update(
                {
                    "platform": target_python.platform,
                    "python_versions": versions,
                    "abi": target_python.abi,
                    "implementation": target_python.implementation,
                }
            )
    if (
        ignore_requires_python is not None
        and "ignore_requires_python" in builder_args.args
    ):
        build_kwargs["ignore_requires_python"] = ignore_requires_python
    return install_cmd._build_package_finder(**build_kwargs)
