# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import textwrap
from functools import partial

import pytest

from pip_shims import (
    FAVORITE_HASH,
    USER_CACHE_DIR,
    BadCommand,
    BestVersionAlreadyInstalled,
    CandidatePreferences,
    CommandError,
    ConfigOptionParser,
    DistributionNotFound,
    FormatControl,
    FrozenRequirement,
    InstallationError,
    InstallCommand,
    InstallRequirement,
    Link,
    LinkCollector,
    PackageFinder,
    PipError,
    PreviousBuildDirError,
    PyPI,
    RequirementSet,
    RequirementsFileParseError,
    SafeFileCache,
    SearchScope,
    SelectionPreferences,
    SourceDistribution,
    TargetPython,
    UninstallationError,
    VcsSupport,
    Wheel,
    _strip_extras,
    build_one,
    build_wheel,
    cmdoptions,
    get_installed_distributions,
    get_package_finder,
    get_resolver,
    global_tempdir_manager,
    index_group,
    install_req_from_editable,
    install_req_from_line,
    install_req_from_req_string,
    is_archive_file,
    is_file_url,
    is_installable_dir,
    make_abstract_dist,
    make_option_group,
    make_preparer,
    parse_version,
    path_to_url,
    pip_version,
    resolve,
    shim_unpack,
    url_to_path,
    wheel_cache,
)
from pip_shims.compat import ensure_resolution_dirs, get_session
from pip_shims.utils import call_function_with_correct_args

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
        fc = type(clsname, (FormatControl,), {})
    assert fc(None, None) == FormatControl(None, None)


@pytest.mark.skipif(
    parse_version(pip_version) >= parse_version("21.3"), reason="Removed in pip 21.3"
)
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
    prefix = "/{}".format(prefix) if prefix else ""
    url = "file://{}{}".format(prefix, path)
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
    if parse_version(pip_version) > parse_version("19.1.1"):
        index_urls = [pip_options.index_url] + pip_options.extra_index_urls
        search_scope = SearchScope.create(
            find_links=pip_options.find_links, index_urls=index_urls
        )
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
        if parse_version(pip_version) > parse_version("19.2.3"):
            link_collector = LinkCollector(session=session, search_scope=search_scope)
            finder_args = {"link_collector": link_collector}
        else:
            finder_args = {"search_scope": search_scope, "session": session}
        finder_args.update(
            {
                "candidate_prefs": candidate_prefs,
                "target_python": target_python,
                "allow_yanked": selection_prefs.allow_yanked,
                "format_control": selection_prefs.format_control,
                "ignore_requires_python": selection_prefs.ignore_requires_python,
            }
        )
    else:
        finder_args = {
            "find_links": pip_options.find_links,
            "index_urls": [pip_options.index_url],
            "trusted_hosts": pip_options.trusted_hosts,
            "session": session,
            "allow_all_prereleases": False,
        }
        if parse_version(pip_version) >= parse_version("22.0.0"):
            finder_args["use_deprecated_html5lib"] = False
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
                candidate.version for candidate in requests_candidates
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

    build_dir = tmpdir.mkdir("build_dir")
    source_dir = tmpdir.mkdir("source_dir")
    download_dir = tmpdir.mkdir("download_dir")
    results = None
    with wheel_cache(USER_CACHE_DIR, FormatControl(None, None)) as wheelcache:
        preparer_kwargs = {
            "build_dir": build_dir.strpath,
            "src_dir": source_dir.strpath,
            "download_dir": download_dir.strpath,
            "progress_bar": "off",
            "build_isolation": False,
            "finder": finder,
            "session": session,
            "require_hashes": False,
            "use_user_site": False,
        }
        resolver_kwargs = {
            "finder": finder,
            "upgrade_strategy": "to-satisfy-only",
            "force_reinstall": False,
            "ignore_dependencies": False,
            "ignore_requires_python": False,
            "ignore_installed": True,
            "use_user_site": False,
        }
        if (
            parse_version("19.3")
            <= parse_version(pip_version)
            <= parse_version("20.0.99999")
        ):
            make_install_req = partial(
                install_req_from_req_string,
                isolated=False,
                wheel_cache=wheelcache,
                # use_pep517=use_pep517,
            )
            resolver_kwargs["make_install_req"] = make_install_req
        else:
            resolver_kwargs["wheel_cache"] = wheelcache
            if parse_version(pip_version) >= parse_version("20.1"):
                make_install_req = partial(
                    install_req_from_req_string,
                    isolated=False,
                    use_pep517=True,
                )
                resolver_kwargs["make_install_req"] = make_install_req
            else:
                resolver_kwargs["isolated"] = False
        resolver = None
        with make_preparer(**preparer_kwargs) as preparer:
            resolver_kwargs["preparer"] = preparer
            reqset = RequirementSet()
            ireq.is_direct = True
            reqset.add_requirement(ireq)
            resolver = get_resolver(**resolver_kwargs)
            resolver.require_hashes = False
            if parse_version(pip_version) > parse_version("20.0.9999999"):
                resolver._populate_link(ireq)
            results = resolver._resolve_one(reqset, ireq)
            try:
                reqset.cleanup_files()
            except AttributeError:
                pass
    results = set(results)
    result_names = [r.name for r in results]
    assert "urllib3" in result_names


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
    with wheel_cache(USER_CACHE_DIR, fc) as w:
        assert w.__class__.__name__ == "WheelCache"


def test_vcs_support():
    vcs = VcsSupport()
    assert "git+https" in vcs.all_schemes


def test_wheel():
    w = Wheel("pytoml-0.1.18-cp36-none-any.whl")
    assert w.pyversions == ["cp36"]


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
        if parse_version(pip_version) > parse_version("19.2.3"):
            link_collector = LinkCollector(session=session, search_scope=search_scope)
            finder_args = {"link_collector": link_collector}
        else:
            finder_args = {"search_scope": search_scope, "session": session}
        finder_args.update(
            {
                "candidate_prefs": candidate_prefs,
                "target_python": target_python,
                "allow_yanked": selection_prefs.allow_yanked,
                "format_control": selection_prefs.format_control,
                "ignore_requires_python": selection_prefs.ignore_requires_python,
            }
        )
    else:
        finder_args = {
            "find_links": pip_options.find_links,
            "index_urls": [pip_options.index_url] + pip_options.extra_index_urls,
            "trusted_hosts": pip_options.trusted_hosts,
            "session": session,
            "allow_all_prereleases": False,
        }
        if parse_version(pip_version) >= parse_version("22.0.0"):
            finder_args["use_deprecated_html5lib"] = False
    finder = PackageFinder(**finder_args)
    build_dir = tmpdir.mkdir("build_dir")
    source_dir = tmpdir.mkdir("source_dir")
    download_dir = tmpdir.mkdir("download_dir")
    wheel_download_dir = CACHE_DIR.mkdir("wheels")
    with wheel_cache(USER_CACHE_DIR, FormatControl(None, None)) as wheelcache:
        kwargs = {
            "build_dir": build_dir.strpath,
            "src_dir": source_dir.strpath,
            "download_dir": download_dir.strpath,
            "wheel_download_dir": wheel_download_dir.strpath,
            "finder": finder,
            "require_hashes": False,
            "use_user_site": False,
            "progress_bar": "off",
            "build_isolation": False,
        }
        ireq = InstallRequirement.from_editable(
            "git+https://github.com/urllib3/urllib3@1.23#egg=urllib3"
        )
        if parse_version(pip_version) <= parse_version("20.0.9999999"):
            ireq.populate_link(finder, False, False)
        ireq.ensure_has_source_dir(kwargs["src_dir"])
        # Ensure the remote artifact is downloaded locally. For wheels, it is
        # enough to just download because we'll use them directly. For an sdist,
        # we need to unpack so we can build it.
        unpack_kwargs = {
            "session": session,
            "hashes": ireq.hashes(True),
            "link": ireq.link,
            "location": ireq.source_dir,
            "download_dir": kwargs["download_dir"],
        }
        if parse_version(pip_version) < parse_version("19.2.0"):
            unpack_kwargs["only_download"] = ireq.is_wheel
        if parse_version(pip_version) >= parse_version("10"):
            unpack_kwargs["progress_bar"] = "off"
        if not is_file_url(ireq.link):
            shim_unpack(**unpack_kwargs)
        output_file = None
        ireq.is_direct = True
        build_args = {
            "req": ireq,
            "output_dir": output_dir.strpath,
            "verify": False,
            "build_options": [],
            "global_options": [],
            "editable": False,
        }
        output_file = call_function_with_correct_args(build_one, **build_args)
    # XXX: skipping to here is functionally the same and should pass all tests
    # output_file = build_wheel(**build_wheel_kwargs)
    assert output_file, output_file


def test_get_packagefinder():
    install_cmd = InstallCommand()
    finder = get_package_finder(
        install_cmd, python_versions=("27", "35", "36", "37", "38"), implementation="cp"
    )
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
                candidate.version for candidate in requests_candidates
            )
        ],
        key=lambda c: c.version,
    )
    best_version = candidates[-1]
    location = getattr(best_version, "location", getattr(best_version, "link", None))
    assert "pythonhosted" in location.url


def test_resolve():
    install_cmd = InstallCommand()
    ireq = InstallRequirement.from_line("requests>=2.18,<2.25.0")
    result = resolve(ireq, install_command=install_cmd)
    assert set(result.keys()) == {"requests", "chardet", "idna", "urllib3", "certifi"}


def test_pypi():
    assert "pypi.org" in PyPI.url or "pypi.python.org" in PyPI.url


def test_dev_pkgs():
    from pip_shims.shims import DEV_PKGS

    assert "pip" in DEV_PKGS and "wheel" in DEV_PKGS


def test_stdlib_pkgs():
    from pip_shims.shims import stdlib_pkgs

    assert "argparse" in stdlib_pkgs


def test_get_session():
    cmd = InstallCommand()
    sess = get_session(install_cmd=cmd)
    assert type(sess).__base__.__name__ == "Session"


def test_build_wheel():
    ireq = InstallRequirement.from_line(
        "https://files.pythonhosted.org/packages/6e/40/7434b2d9fe24107ada25ec90a1fc646e97f346130a2c51aa6a2b1aba28de/requests-2.12.1.tar.gz#egg=requests"
    )
    with global_tempdir_manager(), ensure_resolution_dirs() as kwargs:
        ireq.ensure_has_source_dir(kwargs["src_dir"])
        cmd = InstallCommand()
        options, _ = cmd.parser.parse_args([])
        session = cmd._build_session(options)
        shim_unpack(
            download_dir=kwargs["download_dir"],
            ireq=ireq,
            location=ireq.source_dir,
            only_download=False,
            session=session,
        )
        wheel = next(iter(build_wheel(req=ireq, **kwargs)))
        assert os.path.exists(wheel)
