# -*- coding=utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import sys
import textwrap
from functools import partial

import pytest
import six

from pip_shims import (
    FAVORITE_HASH,
    USER_CACHE_DIR,
    BadCommand,
    BestVersionAlreadyInstalled,
    CandidateEvaluator,
    CandidatePreferences,
    Command,
    CommandError,
    ConfigOptionParser,
    DistributionNotFound,
    FormatControl,
    FrozenRequirement,
    InstallationError,
    InstallRequirement,
    Link,
    LinkCollector,
    PackageFinder,
    PipError,
    PreviousBuildDirError,
    PyPI,
    RequirementPreparer,
    RequirementSet,
    RequirementsFileParseError,
    RequirementTracker,
    Resolver,
    SafeFileCache,
    SearchScope,
    SelectionPreferences,
    SourceDistribution,
    TargetPython,
    UninstallationError,
    VcsSupport,
    Wheel,
    WheelBuilder,
    WheelCache,
    _strip_extras,
    cmdoptions,
    get_installed_distributions,
    index_group,
    install_req_from_editable,
    install_req_from_line,
    install_req_from_req_string,
    is_archive_file,
    is_file_url,
    is_installable_dir,
    make_abstract_dist,
    make_option_group,
    parse_requirements,
    parse_version,
    path_to_url,
    pip_version,
    unpack_url,
    url_to_path,
)

STRING_TYPES = (str,)
if sys.version_info < (3, 0):
    STRING_TYPES = (str, basestring)


def test_strip_extras():
    assert _strip_extras("requests[security]") == ("requests", "[security]")


def test_cmdoptions():
    assert isinstance(cmdoptions.USER_CACHE_DIR, STRING_TYPES)


def test_command(PipCommand):
    pip_command = PipCommand()
    pip_command.parser.add_option(cmdoptions.no_binary())
    pip_command.parser.add_option(cmdoptions.only_binary())
    assert make_option_group
    assert index_group
    index_opts = cmdoptions.make_option_group(cmdoptions.index_group, pip_command.parser)
    pip_command.parser.insert_option_group(0, index_opts)
    assert "pypi" in pip_command.parser.option_groups[0].get_option("-i").default


def test_configparser(PipCommand):
    pip_command = PipCommand()
    config_parser = ConfigOptionParser(name="test_parser")
    config_parser.add_option_group(make_option_group(index_group, config_parser))
    assert "pypi" in config_parser.option_groups[0].get_option("-i").default


@pytest.mark.parametrize(
    "exceptionclass, baseclass",
    [
        (DistributionNotFound, Exception),
        (PipError, Exception),
        (InstallationError, Exception),
        (UninstallationError, Exception),
        (DistributionNotFound, Exception),
        (RequirementsFileParseError, Exception),
        (BestVersionAlreadyInstalled, Exception),
        (BadCommand, Exception),
        (CommandError, Exception),
        (PreviousBuildDirError, Exception),
    ],
)
def test_exceptions(exceptionclass, baseclass):
    assert issubclass(exceptionclass, baseclass)


def test_favorite_hash():
    assert FAVORITE_HASH == "sha256"


def test_format_control():
    from collections import namedtuple

    if issubclass(FormatControl, tuple):
        # through pip 18.0 this object was a named tuple
        fc = namedtuple("FormatControl", "no_binary, only_binary")
    else:
        # after pip 18.0 this has its own model
        clsname = "fc"
        if six.PY2:
            clsname = clsname.encode(sys.getdefaultencoding())
        fc = type(clsname, (FormatControl,), {})
    assert fc(None, None) == FormatControl(None, None)


def test_get_installed():
    dists = get_installed_distributions()
    assert "pip-shims" in [p.project_name for p in dists]


def test_link_and_ireq():
    url = "git+https://github.com/requests/requests.git@2.19.1#egg=requests"
    link = Link(url)
    ireq = InstallRequirement.from_editable(url)
    if install_req_from_editable:
        ireq2 = install_req_from_editable(url)
        assert ireq2.link == link
    assert ireq.link == link


def test_path_and_url():
    path = "/path/to/file"
    prefix, _ = os.path.splitdrive(os.getcwd())
    prefix = "/{0}".format(prefix) if prefix else ""
    url = "file://{0}{1}".format(prefix, path)
    assert is_file_url(Link(url))
    assert path_to_url(path) == url
    assert url_to_path(url) == os.path.realpath(path)


def test_cache_dir(PipCommand):
    pip_command = PipCommand()
    assert pip_command.parser.get_option("--cache-dir").default == USER_CACHE_DIR


def test_is_installable(tmpdir):
    temp_dir = tmpdir.mkdir("test_package")
    setup_py_loc = temp_dir.join("setup.py")
    setup_py_loc.write_text(
        textwrap.dedent(
            """
        from setuptools import setup
        setup(
            name="Test Project",
            version="0.0.0"
        )
    """
        ),
        encoding="utf-8",
    )
    assert is_installable_dir(temp_dir.strpath)


def test_parse_version():
    assert str(parse_version("0.0.1")) == "0.0.1"


def test_archive_file():
    assert is_archive_file("https://github.com/requests/requests/releases/2.19.1.zip")


def test_pip_version():
    assert str(parse_version(pip_version)) == pip_version


def test_resolution(tmpdir, PipCommand):
    pip_command = PipCommand()
    pip_command.parser.add_option_group(
        make_option_group(index_group, pip_command.parser)
    )
    pip_options, _ = pip_command.parser.parse_args([])
    CACHE_DIR = tmpdir.mkdir("CACHE_DIR")
    pip_options.cache_dir = CACHE_DIR.strpath
    session = pip_command._build_session(pip_options)
    assert session
    # finder_args = {
    #     "find_links": pip_options.find_links,
    #     "index_urls": [pip_options.index_url],
    #     "trusted_hosts": pip_options.trusted_hosts,
    #     "session": session,
    # }
    if parse_version(pip_version) > parse_version("19.1.1"):
        index_urls = [pip_options.index_url] + pip_options.extra_index_urls
        search_scope = SearchScope.create(
            find_links=pip_options.find_links, index_urls=index_urls
        )
        link_collector = LinkCollector(session=session, search_scope=search_scope)
        selection_prefs = SelectionPreferences(
            True,
            allow_all_prereleases=False,
            format_control=None,
            prefer_binary=False,
            ignore_requires_python=False,
        )
        target_python = TargetPython()
        candidate_prefs = CandidatePreferences(
            prefer_binary=selection_prefs.prefer_binary,
            allow_all_prereleases=selection_prefs.allow_all_prereleases,
        )
        finder_args = {
            "candidate_prefs": candidate_prefs,
            "link_collector": link_collector,
            "target_python": target_python,
            "allow_yanked": selection_prefs.allow_yanked,
            "format_control": selection_prefs.format_control,
            "ignore_requires_python": selection_prefs.ignore_requires_python,
        }
        # finder_args["candidate_evaluator"] = CandidateEvaluator.create(
        #     target_python=None,
        #     prefer_binary=False,
        #     allow_all_prereleases=False,
        #     ignore_requires_python=False,
        # )
    else:
        finder_args = {
            "find_links": pip_options.find_links,
            "index_urls": [pip_options.index_url],
            "trusted_hosts": pip_options.trusted_hosts,
            "session": session,
            "allow_all_prereleases": False,
        }
        # finder_args["allow_all_prereleases"] = False
    finder = PackageFinder(**finder_args)
    ireq = InstallRequirement.from_line("requests>=2.18")
    if install_req_from_line:
        ireq2 = install_req_from_line("requests>=2.18")
        assert str(ireq) == str(ireq2)
    requests_candidates = finder.find_all_candidates(ireq.name)
    candidates = sorted(
        [
            c
            for c in requests_candidates
            if c.version
            in ireq.specifier.filter(
                (candidate.version for candidate in requests_candidates)
            )
        ],
        key=lambda c: c.version,
    )
    best_version = candidates[-1]
    location = getattr(best_version, "location", getattr(best_version, "link", None))
    assert "pythonhosted" in location.url
    req_file = tmpdir.mkdir("req_dir").join("requirements.txt")
    req_file.write_text(
        textwrap.dedent(
            """
            requests>=2.18
        """
        ),
        encoding="utf-8",
    )
    parsed_ireq = parse_requirements(
        req_file.strpath, finder=finder, session=session, options=pip_options
    )

    build_dir = tmpdir.mkdir("build_dir")
    source_dir = tmpdir.mkdir("source_dir")
    download_dir = tmpdir.mkdir("download_dir")
    wheel_download_dir = CACHE_DIR.mkdir("wheels")
    pkg_download_dir = CACHE_DIR.mkdir("pkgs")
    results = None
    wheel_cache = WheelCache(USER_CACHE_DIR, FormatControl(None, None))
    if parse_version(pip_version) < parse_version("10.0"):
        reqset = RequirementSet(
            build_dir.strpath,
            source_dir.strpath,
            download_dir=download_dir.strpath,
            wheel_download_dir=wheel_download_dir.strpath,
            session=session,
            wheel_cache=wheel_cache,
        )
        results = reqset._prepare_file(finder, ireq)
    else:
        preparer_kwargs = {
            "build_dir": build_dir.strpath,
            "src_dir": source_dir.strpath,
            "download_dir": download_dir.strpath,
            "wheel_download_dir": wheel_download_dir.strpath,
            "progress_bar": "off",
            "build_isolation": False,
        }
        resolver_kwargs = {
            "finder": finder,
            "session": session,
            "upgrade_strategy": "to-satisfy-only",
            "force_reinstall": False,
            "ignore_dependencies": False,
            "ignore_requires_python": False,
            "ignore_installed": True,
            "use_user_site": False,
        }
        if parse_version(pip_version) > parse_version("19.1.1"):
            make_install_req = partial(
                install_req_from_req_string,
                isolated=False,
                wheel_cache=wheel_cache,
                # use_pep517=use_pep517,
            )
            resolver_kwargs["make_install_req"] = make_install_req
        else:
            resolver_kwargs.update(
                {"isolated": False, "wheel_cache": wheel_cache,}
            )
        resolver = None
        preparer = None
        with RequirementTracker() as req_tracker:
            # Pip 18 uses a requirement tracker to prevent fork bombs
            if req_tracker:
                preparer_kwargs["req_tracker"] = req_tracker
            preparer = RequirementPreparer(**preparer_kwargs)
            resolver_kwargs["preparer"] = preparer
            reqset = RequirementSet()
            ireq.is_direct = True
            reqset.add_requirement(ireq)
            resolver = Resolver(**resolver_kwargs)
            resolver.require_hashes = False
            results = resolver._resolve_one(reqset, ireq)
            reqset.cleanup_files()
    results = set(results)
    result_names = [r.name for r in results]
    assert "chardet" in result_names


def test_abstract_dist():
    ireq = InstallRequirement.from_editable(
        "git+https://github.com/requests/requests.git@2.19.1#egg=requests"
    )
    abs_dist = make_abstract_dist(ireq)
    assert abs_dist.__class__.__name__ == SourceDistribution.__name__


def test_safe_file_cache():
    sfc = SafeFileCache(directory=USER_CACHE_DIR)
    assert sfc.__class__.__name__ == "SafeFileCache"


def test_frozen_req():
    import pkg_resources

    req = pkg_resources.Requirement.parse("requests==2.19.1")
    fr = FrozenRequirement("requests", req, False)
    assert fr is not None


def test_wheel_cache():
    fc = FormatControl(None, None)
    w = WheelCache(USER_CACHE_DIR, fc)
    assert w.__class__.__name__ == "WheelCache"


def test_vcs_support():
    vcs = VcsSupport()
    assert "git+https" in vcs.all_schemes


def test_wheel():
    w = Wheel("pytoml-0.1.18-cp36-none-any.whl")
    assert w.pyversions == ["cp36"]


@pytest.mark.skipif(
    (sys.version_info > (3, 0) and sys.version_info < (3, 5)),
    reason="Can't build a wheel for six on python 3.5",
)
def test_wheelbuilder(tmpdir, PipCommand):
    output_dir = tmpdir.join("output")
    output_dir.mkdir()
    pip_command = PipCommand()
    pip_command.parser.add_option_group(
        make_option_group(index_group, pip_command.parser)
    )
    pip_options, _ = pip_command.parser.parse_args([])
    CACHE_DIR = tmpdir.mkdir("CACHE_DIR")
    pip_options.cache_dir = CACHE_DIR.strpath
    session = pip_command._build_session(pip_options)
    if parse_version(pip_version) > parse_version("19.1.1"):
        index_urls = [pip_options.index_url] + pip_options.extra_index_urls
        search_scope = SearchScope.create(
            find_links=pip_options.find_links, index_urls=index_urls
        )
        link_collector = LinkCollector(session=session, search_scope=search_scope)
        selection_prefs = SelectionPreferences(
            True,
            allow_all_prereleases=False,
            format_control=None,
            prefer_binary=False,
            ignore_requires_python=False,
        )
        target_python = TargetPython()
        candidate_prefs = CandidatePreferences(
            prefer_binary=selection_prefs.prefer_binary,
            allow_all_prereleases=selection_prefs.allow_all_prereleases,
        )
        finder_args = {
            "candidate_prefs": candidate_prefs,
            "link_collector": link_collector,
            "target_python": target_python,
            "allow_yanked": selection_prefs.allow_yanked,
            "format_control": selection_prefs.format_control,
            "ignore_requires_python": selection_prefs.ignore_requires_python,
        }
        # finder_args["candidate_evaluator"] = CandidateEvaluator.create(
        #     target_python=None,
        #     prefer_binary=False,
        #     allow_all_prereleases=False,
        #     ignore_requires_python=False,
        # )
    else:
        finder_args = {
            "find_links": pip_options.find_links,
            "index_urls": [pip_options.index_url] + pip_options.extra_index_urls,
            "trusted_hosts": pip_options.trusted_hosts,
            "session": session,
            "allow_all_prereleases": False,
        }
        # finder_args["allow_all_prereleases"] = False
    finder = PackageFinder(**finder_args)
    build_dir = tmpdir.mkdir("build_dir")
    source_dir = tmpdir.mkdir("source_dir")
    download_dir = tmpdir.mkdir("download_dir")
    wheel_download_dir = CACHE_DIR.mkdir("wheels")
    wheel_cache = WheelCache(USER_CACHE_DIR, FormatControl(None, None))
    kwargs = {
        "build_dir": build_dir.strpath,
        "src_dir": source_dir.strpath,
        "download_dir": download_dir.strpath,
        "wheel_download_dir": wheel_download_dir.strpath,
        "wheel_cache": wheel_cache,
    }
    ireq = InstallRequirement.from_editable(
        "git+https://github.com/urllib3/urllib3@1.23#egg=urllib3"
    )
    ireq.populate_link(finder, False, False)
    ireq.ensure_has_source_dir(kwargs["src_dir"])
    # Ensure the remote artifact is downloaded locally. For wheels, it is
    # enough to just download because we'll use them directly. For an sdist,
    # we need to unpack so we can build it.
    unpack_kwargs = {"session": session, "hashes": ireq.hashes(True)}
    if parse_version(pip_version) < parse_version("19.2.0"):
        unpack_kwargs["only_download"] = ireq.is_wheel
    if parse_version(pip_version) >= parse_version("10"):
        unpack_kwargs["progress_bar"] = False
    if not is_file_url(ireq.link):
        unpack_url(ireq.link, ireq.source_dir, kwargs["download_dir"], **unpack_kwargs)
    output_file = None
    if parse_version(pip_version) < parse_version("10"):
        kwargs["session"] = finder.session
        reqset = RequirementSet(**kwargs)
        ireq.is_direct = True
        builder = WheelBuilder(reqset, finder)
        output_file = builder._build_one(ireq, output_dir.strpath)
    else:
        kwargs.update({"progress_bar": "off", "build_isolation": False})
        wheel_cache = kwargs.pop("wheel_cache")
        with RequirementTracker() as req_tracker:
            # if req_tracker:
            #     kwargs["req_tracker"] = req_tracker
            preparer = RequirementPreparer(
                kwargs["build_dir"],
                kwargs["download_dir"],
                kwargs["src_dir"],
                kwargs["wheel_download_dir"],
                kwargs["progress_bar"],
                kwargs["build_isolation"],
                req_tracker,
            )
            builder_args = [preparer, wheel_cache]
            if parse_version(pip_version) < parse_version("19.3"):
                builder_args = [finder] + builder_args
            builder = WheelBuilder(*builder_args)
            output_file = builder._build_one(ireq, output_dir.strpath)
    assert output_file, output_file


def test_pypi():
    assert "pypi.org" in PyPI.url or "pypi.python.org" in PyPI.url


def test_dev_pkgs():
    from pip_shims.shims import DEV_PKGS

    assert "pip" in DEV_PKGS and "wheel" in DEV_PKGS


def test_stdlib_pkgs():
    from pip_shims.shims import stdlib_pkgs

    assert "argparse" in stdlib_pkgs
