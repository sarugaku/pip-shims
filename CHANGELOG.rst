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
