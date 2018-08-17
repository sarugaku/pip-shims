# -*- coding=utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
from pip_shims import (
    _strip_extras,
    cmdoptions,
    Command,
    ConfigOptionParser,
    DistributionNotFound,
    FAVORITE_HASH,
    FormatControl,
    get_installed_distributions,
    index_group,
    InstallRequirement,
    is_archive_file,
    is_file_url,
    unpack_url,
    is_installable_dir,
    Link,
    make_abstract_dist,
    make_option_group,
    PackageFinder,
    parse_requirements,
    parse_version,
    path_to_url,
    pip_version,
    PipError,
    RequirementPreparer,
    RequirementSet,
    RequirementTracker,
    Resolver,
    SafeFileCache,
    url_to_path,
    USER_CACHE_DIR,
    VcsSupport,
    Wheel,
    WheelCache,
    WheelBuilder
)
import pytest
import sys
import textwrap

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
    index_opts = cmdoptions.make_option_group(
        cmdoptions.index_group, pip_command.parser
    )
    pip_command.parser.insert_option_group(0, index_opts)
    assert "pypi" in pip_command.parser.option_groups[0].get_option("-i").default


def test_configparser(PipCommand):
    pip_command = PipCommand()
    config_parser = ConfigOptionParser(name="test_parser")
    config_parser.add_option_group(make_option_group(index_group, config_parser))
    assert "pypi" in config_parser.option_groups[0].get_option("-i").default


@pytest.mark.parametrize(
    "exceptionclass, baseclass",
    [(DistributionNotFound, Exception), (PipError, Exception)],
)
def test_exceptions(exceptionclass, baseclass):
    assert issubclass(exceptionclass, baseclass)


def test_favorite_hash():
    assert FAVORITE_HASH == "sha256"


def test_format_control():
    from collections import namedtuple

    fc = namedtuple("FormatControl", "no_binary, only_binary")
    assert fc(None, None) == FormatControl(None, None)


def test_get_installed():
    dists = get_installed_distributions()
    assert "pip-shims" in [p.project_name for p in dists]


def test_link_and_ireq():
    url = "git+https://github.com/requests/requests.git@2.19.1#egg=requests"
    link = Link(url)
    ireq = InstallRequirement.from_editable(url)
    assert ireq.link == link


def test_path_and_url():
    path = "/path/to/file"
    prefix = "/C:" if os.name == "nt" else ""
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
    """),
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
    finder = PackageFinder(
        find_links=pip_options.find_links,
        index_urls=[pip_options.index_url],
        trusted_hosts=pip_options.trusted_hosts,
        allow_all_prereleases=False,
        session=session,
    )
    ireq = InstallRequirement.from_line("requests>=2.18")
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
    assert "pythonhosted" in best_version.location.url
    req_file = tmpdir.mkdir("req_dir").join("requirements.txt")
    req_file.write_text(
        textwrap.dedent("""
            requests>=2.18
        """),
        encoding="utf-8",
    )
    parsed_ireq = parse_requirements(
        req_file.strpath, finder=finder, session=finder.session, options=pip_options
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
            session=finder.session,
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
            "session": finder.session,
            "upgrade_strategy": "to-satisfy-only",
            "force_reinstall": False,
            "ignore_dependencies": False,
            "ignore_requires_python": False,
            "ignore_installed": True,
            "isolated": False,
            "wheel_cache": wheel_cache,
            "use_user_site": False,
        }
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
    assert abs_dist.__class__.__name__ == "IsSDist"


def test_safe_file_cache():
    sfc = SafeFileCache(directory=USER_CACHE_DIR)
    assert sfc.__class__.__name__ == "SafeFileCache"


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


def test_wheelbuilder(tmpdir, PipCommand):
    output_dir = tmpdir.join("output")
    output_dir.mkdir()
    reqset = RequirementSet()
    pip_command = PipCommand()
    pip_command.parser.add_option_group(
        make_option_group(index_group, pip_command.parser)
    )
    pip_options, _ = pip_command.parser.parse_args([])
    CACHE_DIR = tmpdir.mkdir("CACHE_DIR")
    pip_options.cache_dir = CACHE_DIR.strpath
    session = pip_command._build_session(pip_options)
    finder = PackageFinder(
        find_links=pip_options.find_links,
        index_urls=[pip_options.index_url],
        trusted_hosts=pip_options.trusted_hosts,
        allow_all_prereleases=False,
        session=session,
    )
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
    ireq = InstallRequirement.from_editable("git+https://github.com/benjaminp/six.git@1.11.0#egg=six")
    ireq.populate_link(finder, False, False)
    ireq.ensure_has_source_dir(kwargs["src_dir"])
    # Ensure the remote artifact is downloaded locally. For wheels, it is
    # enough to just download because we'll use them directly. For an sdist,
    # we need to unpack so we can build it.
    if not is_file_url(ireq.link):
        unpack_url(
            ireq.link, ireq.source_dir, kwargs["download_dir"],
            only_download=ireq.is_wheel, session=session,
            hashes=ireq.hashes(True), progress_bar=False,
        )
    output_file = None
    if parse_version(pip_version) < parse_version("10"):
        reqset = RequirementSet(**kwargs)
        ireq.is_direct = True
        reqset.add(ireq)
        builder = WheelBuilder(reqset, finder)
        output_file = builder._build_one(ireq, output_dir)
    else:
        kwargs.update({"progress_bar": "off", "build_isolation": False})
        wheel_cache = kwargs.pop("wheel_cache")
        with RequirementTracker() as req_tracker:
            if req_tracker:
                kwargs["req_tracker"] = req_tracker
            preparer = RequirementPreparer(**kwargs)
            builder = WheelBuilder(finder, preparer, wheel_cache)
            output_file = builder._build_one(ireq, output_dir)
    assert output_file, output_file
