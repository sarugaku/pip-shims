===============================================================================
pip-shims: Shims for importing packages from pip's internals.
===============================================================================

.. image:: https://img.shields.io/pypi/v/pip-shims.svg
    :target: https://pypi.python.org/pypi/pip-shims

.. image:: https://img.shields.io/pypi/l/pip-shims.svg
    :target: https://pypi.python.org/pypi/pip-shims

.. image:: https://github.com/sarugaku/pip-shims/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/sarugaku/pip-shims/actions/workflows/ci.yml
    :alt: Build Status

.. image:: https://img.shields.io/pypi/pyversions/pip-shims.svg
    :target: https://pypi.python.org/pypi/pip-shims

.. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg
    :target: https://saythanks.io/to/techalchemy

.. image:: https://readthedocs.org/projects/pip-shims/badge/?version=latest
    :target: https://pip-shims.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Warning
********

.. warning::
   The authors of `pip`_ **do not condone** the use of this package. Relying on pip's
   internals is a **dangerous** idea for your software as they are broken intentionally
   and regularly.  This package may not always be completely updated up PyPI, so relying
   on it may break your code! User beware!

.. _pip: https://github.com/pypa/pip


Installation
*************

Install from `PyPI`_:

 .. code-block:: console

    $ pipenv install pip-shims

Install from `Github`_:

.. code-block:: console

    $ pipenv install -e git+https://github.com/sarugaku/pip-shims.git#egg=pip-shims


.. _PyPI: https://www.pypi.org/project/pip-shims
.. _Github: https://github.com/sarugaku/pip-shims


.. _`Summary`:

Summary
********

**pip-shims** is a set of compatibilty access shims to the `pip`_ internal API. **pip-shims**
provides compatibility across several pip releases.  The shims are provided using a lazy
import strategy by hacking a module by overloading a class instance's *getattr* method.
This library exists due to my constant writing of the same set of import shims across
many different libraries, including `pipenv`_, `pip-tools`_, `requirementslib`_, and
`passa`_.

.. _passa: https://github.com/sarugaku/passa
.. _pip: https://github.com/pypa/pip
.. _pipenv: https://github.com/pypa/pipenv
.. _pip-tools: https://github.com/jazzband/pip-tools
.. _requirementslib: https://github.com/sarugaku/requirementslib

Pip Compatibility
*****************

Due to the fact that pip has adopted `calver`_, this project provides shims for pip releases
up to 2 years. pip earlier than that period MAY work but the compatibility isn't guaranteed
by the continous integration. For example, the support for ``pip==20.0`` will be dropped at 1/1/2023.

.. _calver: https://calver.org/

.. _`Usage`:

Usage
******

Importing a shim
--------------------

You can use **pip-shims** to expose elements of **pip**'s internal API by importing them:

.. code-block:: pycon

    >>> from pip_shims import Wheel
    >>> mywheel = Wheel('/path/to/my/wheel.whl')


Resolving Dependencies
----------------------------

You can resolve the dependencies of a package using the shimmed resolver interface:

.. code-block:: pycon

    >>> from pip_shims.shims import resolve, InstallRequirement
    >>> ireq = InstallRequirement.from_line("requests>=2.20")
    >>> results = resolve(ireq)
    >>> for k, v in results.items():
    ...    print("{0}: {1!r}".format(k, v))
    requests: <InstallRequirement object: requests>=2.20 from https://files.pythonhosted.org/packages/51/bd/23c926cd341ea6b7dd0b2a00aba99ae0f828be89d72b2190f27c11d4b7fb/requests-2.22.0-py2.py3-none-any.whl#sha256=9cf5292fcd0f598c671cfc1e0d7d1a7f13bb8085e9a590f48c010551dc6c4b31 editable=False>
    idna: <InstallRequirement object: idna<2.9,>=2.5 from https://files.pythonhosted.org/packages/14/2c/cd551d81dbe15200be1cf41cd03869a46fe7226e7450af7a6545bfc474c9/idna-2.8-py2.py3-none-any.whl#sha256=ea8b7f6188e6fa117537c3df7da9fc686d485087abf6ac197f9c46432f7e4a3c (from requests>=2.20) editable=False>
    urllib3: <InstallRequirement object: urllib3!=1.25.0,!=1.25.1,<1.26,>=1.21.1 from https://files.pythonhosted.org/packages/b4/40/a9837291310ee1ccc242ceb6ebfd9eb21539649f193a7c8c86ba15b98539/urllib3-1.25.7-py2.py3-none-any.whl#sha256=a8a318824cc77d1fd4b2bec2ded92646630d7fe8619497b142c84a9e6f5a7293 (from requests>=2.20) editable=False>
    chardet: <InstallRequirement object: chardet<3.1.0,>=3.0.2 from https://files.pythonhosted.org/packages/bc/a9/01ffebfb562e4274b6487b4bb1ddec7ca55ec7510b22e4c51f14098443b8/chardet-3.0.4-py2.py3-none-any.whl#sha256=fc323ffcaeaed0e0a02bf4d117757b98aed530d9ed4531e3e15460124c106691 (from requests>=2.20) editable=False>
    certifi: <InstallRequirement object: certifi>=2017.4.17 from https://files.pythonhosted.org/packages/18/b0/8146a4f8dd402f60744fa380bc73ca47303cccf8b9190fd16a827281eac2/certifi-2019.9.11-py2.py3-none-any.whl#sha256=fd7c7c74727ddcf00e9acd26bba8da604ffec95bf1c2144e67aff7a8b50e6cef (from requests>=2.20) editable=False>



Available Shims
****************

**pip-shims** provides the following compatibility shims:

======================== ========================================== =======================================
Import Path               Import Name                                Former Path
======================== ========================================== =======================================
__version__               pip_version
<shimmed>                 build_wheel
<shimmed>                 get_package_finder
<shimmed>                 get_requirement_set
<shimmed>                 get_resolver
<shimmed>                 is_archive_file                            download
<shimmed>                 is_file_url                                download
<shimmed>                 make_preparer
<shimmed>                 resolve
<shimmed>                 shim_unpack
cache                     WheelCache                                 wheel
cli                       cmdoptions                                 cmdoptions
cli.base_command          Command                                    basecommand
cli.cmdoptions            index_group                                cmdoptions
cli.cmdoptions            make_option_group                          cmdoptions
cli.parser                ConfigOptionParser                         baseparser
cli.req_command           SessionCommandMixin
collector                 LinkCollector
commands                  commands_dict
commands.freeze           DEV_PKGS
commands.install          InstallCommand
distributions             make_distribution_for_install_requirement  operations.prepare.make_abstract_dist
distributions.base        AbstractDistribution
distributions.installed   InstalledDistribution
distributions.source      SourceDistribution
distributions.wheel       WheelDistribution
download                  path_to_url
download                  unpack_url
exceptions                BadCommand
exceptions                BestVersionAlreadyInstalled
exceptions                CommandError
exceptions                DistributionNotFound
exceptions                DistributionNotFound
exceptions                InstallationError
exceptions                PipError
exceptions                PreviousBuildDirError
exceptions                RequirementsFileParseError
exceptions                UninstallationError
index                     CandidateEvaluator
index                     CandidatePreferences
index                     LinkEvaluator
index                     PackageFinder
index                     parse_version
locations                 USER_CACHE_DIR
models                    FormatControl                              index
models.index              PyPI
models.link               Link                                       index
models.search_scope       SearchScope
models.selection_prefs    SelectionPreferences
models.target_python      TargetPython
network.cache             SafeFileCache                              download
operations.freeze         FrozenRequirement                          <`__init__`>
operations.prepare        Downloader
operations.prepare        make_abstract_dist                         req.req_set
operations.prepare        RequirementPreparer
pep425tags                get_supported
pep425tags                get_tags
req.constructors          _strip_extras                              req.req_install
req.constructors          install_req_from_editable                  req.req_install.InstallRequirement
req.constructors          install_req_from_line                      req.req_install.InstallRequirement
req.constructors          install_req_from_req_string
req.req_file              parse_requirements
req.req_install           InstallRequirement
req.req_set               RequirementSet
req.req_tracker           get_requirement_tracker
req.req_tracker           RequirementTracker
req.req_uninstall         UninstallPathSet
resolve                   Resolver
utils.compat              stdlib_pkgs                                compat
utils.hashes              FAVORITE_HASH
utils.misc                get_installed_distributions                utils
utils.misc                is_installable_dir                         utils
utils.temp_dir            global_tempdir_manager
utils.temp_dir            TempDirectory
utils.urls                url_to_path                                download
vcs.versioncontrol        VcsSupport                                 vcs.VcsSupport
wheel                     Wheel
wheel                     WheelBuilder
wheel_builder             build
wheel_builder             build_one
wheel_builder             build_one_inside_env
======================== ========================================== =======================================
