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
