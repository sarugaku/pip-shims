Pip_Shims 0.7.3 (2022-07-07)
============================


Pip_Shims 0.7.2 (2022-06-29)
============================


Features
--------

- Resolve issue of ``build_tracker`` being ``None`` at runtime with ``pip>=22.1`` when using ``pip_shims``.  `#81 <https://github.com/sarugaku/pip-shims/issues/81>`_


Pip_Shims 0.7.2 (2022-06-29)
============================


Features
--------

- Resolve issue of ``build_tracker`` being ``None`` at runtime with ``pip>=22.1`` when using ``pip_shims``.  `#81 <https://github.com/sarugaku/pip-shims/issues/81>`_


Pip_Shims 0.7.1 (2022-06-29)
============================


Bug Fixes
---------

- Added support for new ``pip==22.1.x`` required ``make_preparer`` arg ``check_build_deps`` which defaults to ``False``.  `#80 <https://github.com/sarugaku/pip-shims/issues/80>`_


Pip_Shims 0.7.0 (2022-03-28)
============================


Features
--------

- This change gets ``pip-shims`` working with ``pip==22.x``, ``main`` branch, and also fixes linting build.  `#79 <https://github.com/sarugaku/pip-shims/issues/79>`_


Pip_Shims 0.6.0 (2021-11-03)
============================


Features
--------

- No longer guarantee compatibility for ``pip<20``. Add support for ``pip==21.3``.  `#77 <https://github.com/sarugaku/pip-shims/issues/77>`_
  

Removals and Deprecations
-------------------------

- Drop support for Python 2.7 and 3.5.  `#77 <https://github.com/sarugaku/pip-shims/issues/77>`_


0.5.3 (2020-08-08)
==================

Bug Fixes
---------

- Avoid overriding slot members when adding new methods to a class.  `#67 <https://github.com/sarugaku/pip-shims/issues/67>`_
  
- Call ``resolve()`` with correct arguments for pip 20.2.  `#68 <https://github.com/sarugaku/pip-shims/issues/68>`_


0.5.2 (2020-04-22)
==================

Features
--------

- Added support for ``pip==20.1``.
  - Added support for global temporary directory context management when generating wheel caches using the compatibility module;
  - Added wheel cache context management which now requires the temporary directory context in some cases;
  - Improved function argument introspection;
  - Updated test invocations to reflect shifting parameters.  `#65 <https://github.com/sarugaku/pip-shims/issues/65>`_


0.5.1 (2020-03-10)
==================

Bug Fixes
---------

- Fixed incorrect session creation via ``pip_shims.compat.get_session`` which inadvertently passed a tuple to pip when building a session instance.  `#56 <https://github.com/sarugaku/pip-shims/issues/56>`_
  
- Added ``wheel_cache`` context manager helper for managing global context when creating wheel wheel_cache instances.  `#58 <https://github.com/sarugaku/pip-shims/issues/58>`_
  
- Fixed resolution failures due to ``Resolver.resolve`` signature updates in ``pip@master``:
    - Automatically check for and pass ``check_supports_wheel`` argument to `Resolver.resolve()` when expected
    - Check whether ``Resolver.resolve()`` expects a ``RequirementSet`` or ``List[InstallRequirement]`` and pass the appropriate input  `#59 <https://github.com/sarugaku/pip-shims/issues/59>`_
  
- Fixed requirement build failures due to new ``autodelete: bool`` required argument in ``InstallRequirement.ensure_build_location``.  `#60 <https://github.com/sarugaku/pip-shims/issues/60>`_
  
- Updated ``Resolver`` import path to point at new location (``legacy_resolve`` -> ``resolution.legacy.resolver``).  `#61 <https://github.com/sarugaku/pip-shims/issues/61>`_
  
- Fixed ``AttributeError`` caused by failed ``RequirementSet.cleanup()`` calls after ``Resolver.resolve()`` which is no longer valid in ``pip>=20.1``.  `#62 <https://github.com/sarugaku/pip-shims/issues/62>`_


0.5.0 (2020-01-28)
==================

Features
--------

- Exposed ``build``, ``build_one``, and ``build_one_inside_env`` from ``wheel_builder`` module starting in ``pip>=20``.  `#49 <https://github.com/sarugaku/pip-shims/issues/49>`_
  
- Added a ``build_wheel`` shim function which can build either a single ``InstallRequirement`` or an iterable of ``InstallRequirement`` instances.  `#50 <https://github.com/sarugaku/pip-shims/issues/50>`_
  
- Exposed ``global_tempdir_manager`` for handling ``TempDirectory`` instance contexts.  `#51 <https://github.com/sarugaku/pip-shims/issues/51>`_
  

Bug Fixes
---------

- Added ``Downloader`` class which is now passed to ``shim_unpack`` implementation.  `#42 <https://github.com/sarugaku/pip-shims/issues/42>`_
  
- Updated references to the ``Downloader`` class to point at ``pip._internal.network.download.Downloader`` which is where it resides on pip master for ``pip>19.3.1``.  `#46 <https://github.com/sarugaku/pip-shims/issues/46>`_
  
- Added a compatibility shim to provide ongoing access to the ``Wheel`` class which is removed in ``pip>19.3.1``.  `#47 <https://github.com/sarugaku/pip-shims/issues/47>`_
  
- Added mapping for ``distributions.make_distribution_for_install`` to ``make_abstract_dist`` for ``pip>=20.0``.  `#52 <https://github.com/sarugaku/pip-shims/issues/52>`_


0.4.0 (2019-11-22)
==================

Features
--------

- Improved documentation and added fundamentally re-architected the library
- Added improved docstrings and example usages
- Included type annotations for many types and shims
- Fully reimplemented critical functionality to abstract logic while improving maintainability and ability to reason about the core operations
- Added numerous helper functions to reduce maintenance burden
- Added fully backward compatible library native shims to call ``pip`` functions:

 - ``populate_options``
 - ``get_requirement_set``
 - ``get_package_finder``
 - ``shim_unpack``
 - ``make_preparer``
 - ``get_resolver``
 - ``resolve``

- Added design drawings
- Implemented ``ShimmedPath`` and ``ShimmedPathCollection`` abstractions  `#37 <https://github.com/sarugaku/pip-shims/issues/37>`_


0.3.4 (2019-11-18)
==================

Features
--------

- Added ``SessionCommandMixin``, ``CandidateEvaluator``, ``CandidatePreferences``, ``LinkCollector``, ``LinkEvaluator``, ``TargetPython``, ``SearchScope``, and ``SelectionPreferences`` to exposed classes and ``install_req_from_req_string`` to exposed functions.  `#33 <https://github.com/sarugaku/pip-shims/issues/33>`_


Bug Fixes
---------

- Added override to the ``Command`` class to automatically fill in default values for ``name`` and ``summary`` which are now required in ``__init__``.
  - Added mixin to the Command class to continue supporting ``_build_session`` method.  `#32 <https://github.com/sarugaku/pip-shims/issues/32>`_

- Shimmed functions for ``is_file_url`` and ``is_archive_file``.  `#34 <https://github.com/sarugaku/pip-shims/issues/34>`_

- Updated the paths for the following moved items:
  - ``SafeFileCache`` -> ``network.cache``
  - ``Link`` -> ``models.link.Link``
  - ``path_to_url`` -> ``utils.url``
  - ``url_to_path`` -> ``utils.url``
  - ``SourceDistribution`` -> ``distributions.source.legacy``  `#35 <https://github.com/sarugaku/pip-shims/issues/35>`_


0.3.3 (2019-06-16)
==================

Features
--------

- Added ``commands.freeze.DEV_PKGS`` and ``utils.compat.stdlib_pkgs`` shims.  `#25 <https://github.com/sarugaku/pip-shims/issues/25>`_

- Updated ``PackageFinder`` test and added ``CandidateEvaluator`` import starting with ``pip>=19.1`` for finding prerelease candidates.  `#27 <https://github.com/sarugaku/pip-shims/issues/27>`_


Bug Fixes
---------

- Fixed import paths for ``VcsSupport`` on ``pip>19.1.1``.  `#28 <https://github.com/sarugaku/pip-shims/issues/28>`_


0.3.2 (2018-10-27)
=======================

Features
--------

- Added access to ``pip._internal.models.index.PyPI``.  `#21 <https://github.com/sarugaku/pip-shims/issues/21>`_


0.3.1 (2018-10-06)
==================

Features
--------

- Added shims for the following:
    * ``InstallationError``
    * ``UninstallationError``
    * ``DistributionNotFound``
    * ``RequirementsFileParseError``
    * ``BestVersionAlreadyInstalled``
    * ``BadCommand``
    * ``CommandError``
    * ``PreviousBuildDirError``  `#19 <https://github.com/sarugaku/pip-shims/issues/19>`_


0.3.0 (2018-10-06)
==================

Features
--------

- Added and exposed ``FrozenRequirement`` for consumption.  `#17 <https://github.com/sarugaku/pip-shims/issues/17>`_


Bug Fixes
---------

- Fixed a bug which caused usage of incorrect location for ``_strip_extras``.  `#13 <https://github.com/sarugaku/pip-shims/issues/13>`_

- Fixed a bug which caused ``FormatControl`` imports to fail in ``pip>=18.1``.  `#15 <https://github.com/sarugaku/pip-shims/issues/15>`_

- Fixed a bug which caused ``InstallRequirement.from_line`` and ``InstallRequirement.from_editable`` to fail in ``pip>=18.1``.  `#16 <https://github.com/sarugaku/pip-shims/issues/16>`_


0.2.0 (2018-10-05)
==================

Features
--------

- Added a shim for ``pip._internal.req.req_uninstall.UninstallPathSet``.  `#10 <https://github.com/sarugaku/pip-shims/issues/10>`_

- Made all module loading lazy by replacing modules dynamically at runtime.  `#9 <https://github.com/sarugaku/pip-shims/issues/9>`_


0.1.2 (2018-08-18)
==================

Features
--------

- Added ``WheelCache`` and ``unpack_url`` functionality.  `#4 <https://github.com/sarugaku/pip-shims/issues/4>`_


Bug Fixes
---------

- Fixed a bug which caused failures in the detection and import on pip version 9 and below when using modutils.  `#5 <https://github.com/sarugaku/pip-shims/issues/5>`_

- Fixed a bug with sort order logic which caused invalid import paths to be prioritized accidentally.  `#7 <https://github.com/sarugaku/pip-shims/issues/7>`_


0.1.1 (2018-08-14)
==================

Bug Fixes
---------

- Fixed tests failures for appveyor path comparisons.  `#2 <https://github.com/sarugaku/pip-shims/issues/2>`_


Documentation Updates
---------------------

- Added warning to documentation to discourage use of these shims for accessing the pip API.  `#1 <https://github.com/sarugaku/pip-shims/issues/1>`_


0.1.0 (2018-08-09)
==================

Features
--------

- Initial release of pip compatibility shims!  `#0 <https://github.com/sarugaku/pip-shims/issues/0>`_
