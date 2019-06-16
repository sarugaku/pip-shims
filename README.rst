===============================================================================
pip-shims: Shims for importing packages from pip's internals.
===============================================================================

.. image:: https://img.shields.io/pypi/v/pip-shims.svg
    :target: https://pypi.python.org/pypi/pip-shims

.. image:: https://img.shields.io/pypi/l/pip-shims.svg
    :target: https://pypi.python.org/pypi/pip-shims

.. image:: https://travis-ci.com/sarugaku/pip-shims.svg?branch=master
    :target: https://travis-ci.com/sarugaku/pip-shims

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

  ::

    $ pipenv install --pre pip-shims

Install from `Github`_:

  ::

    $ pipenv install -e git+https://github.com/sarugaku/pip-shims.git#egg=pip-shims


.. _PyPI: https://www.pypi.org/project/pip-shims
.. _Github: https://github.com/sarugaku/pip-shims


.. _`Summary`:

Summary
********

**pip-shims** is a set of compatibilty access shims to the `pip`_ internal API. **pip-shims**
provides compatibility with pip versions 8.0 through the current release (18.x).  The shims
are provided using a lazy import strategy by hacking a module by overloading a class instance's *getattr* method.
This library exists due to my constant writing of the same set of import shims across
many different libraries, including `pipenv`_, `pip-tools`_, `requirementslib`_, and
`passa`_.

.. _passa: https://github.com/sarugaku/passa
.. _pip: https://github.com/pypa/pip
.. _pipenv: https://github.com/pypa/pipenv
.. _pip-tools: https://github.com/jazzband/pip-tools
.. _requirementslib: https://github.com/sarugaku/requirementslib


.. _`Usage`:

Usage
******

Importing a shim
/////////////////

You can use **pip-shims** to expose elements of **pip**'s internal API by importing them:

  ::

    from pip_shims import Wheel
    mywheel = Wheel('/path/to/my/wheel.whl')


Available Shims
****************

**pip-shims** provides the following compatibility shims:

======================== ========================================== =======================================
Import Path               Import Name                                Former Path
======================== ========================================== =======================================
req.constructors          _strip_extras                              req.req_install
cli                       cmdoptions                                 cmdoptions
cli.base_command          Command                                    basecommand
cli.parser                ConfigOptionParser                         baseparser
commands.freeze           DEV_PKGS
exceptions                DistributionNotFound
utils.hashes              FAVORITE_HASH
models                    FormatControl                              index
utils.misc                get_installed_distributions                utils
utils.compat              stdlib_pkgs                                compat
cli.cmdoptions            index_group                                cmdoptions
req.req_install           InstallRequirement
req.constructors          install_req_from_line                      req.req_install.InstallRequirement
req.constructors          install_req_from_editable                  req.req_install.InstallRequirement
req.req_uninstall         UninstallPathSet
distributions             make_distribution_for_install_requirement  operations.prepare.make_abstract_dist
distributions.base        AbstractDistribution
distributions.source      SourceDistribution
distributions.installed   InstalledDistribution
distributions.wheel       WheelDistribution
download                  is_archive_file
download                  is_file_url
utils.misc                is_installable_dir                         utils
index                     Link
operations.prepare        make_abstract_dist                         req.req_set
cli.cmdoptions            make_option_group                          cmdoptions
index                     CandidateEvaluator
index                     PackageFinder
req.req_file              parse_requirements
index                     parse_version
download                  path_to_url
__version__               pip_version
exceptions                PipError
exceptions                InstallationError
exceptions                UninstallationError
exceptions                DistributionNotFound
exceptions                RequirementsFileParseError
exceptions                BestVersionAlreadyInstalled
exceptions                BadCommand
exceptions                CommandError
exceptions                PreviousBuildDirError
operations.prepare        RequirementPreparer
operations.freeze         FrozenRequirement                          <`__init__`>
req.req_set               RequirementSet
req.req_tracker           RequirementTracker
resolve                   Resolver
download                  SafeFileCache
download                  url_to_path
download                  unpack_url
locations                 USER_CACHE_DIR
vcs.versioncontrol        VcsSupport                                 vcs.VcsSupport
wheel                     Wheel
wheel                     WheelBuilder
cache                     WheelCache                                 wheel
======================== ========================================== =======================================
