# -*- coding=utf-8 -*-
import sys

from packaging import specifiers

from .environment import BASE_IMPORT_PATH, MYPY_RUNNING, get_pip_version

if MYPY_RUNNING:
    from typing import Any, Callable, List, Optional, Tuple


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
