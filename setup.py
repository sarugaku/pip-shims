import ast
import os

from setuptools import find_packages, setup

ROOT = os.path.dirname(__file__)

PACKAGE_NAME = "pip_shims"


# Put everything in setup.cfg, except those that don't actually work?
setup(
    # These really don't work.
    package_dir={"": "src"},
    packages=find_packages("src"),
    # I don't know how to specify an empty key in setup.cfg.
    package_data={"": ["LICENSE*", "README*"]},
    # I need this to be dynamic.
)
