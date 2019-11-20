import ast
import os

# fmt: off
if os.environ.get("PIP_SHIMS_BASE_MODULE", None):
    os.environ.pop("PIP_SHIMS_BASE_MODULE")

# fmt: on

from setuptools import find_packages, setup  # isort:skip


ROOT = os.path.dirname(__file__)

PACKAGE_NAME = "pip_shims"

# Can't set this in setup.cfg because of the pip import hackery we do
VERSION = None

with open(os.path.join(ROOT, "src", PACKAGE_NAME, "__init__.py")) as f:
    for line in f:
        if line.startswith("__version__ = "):
            VERSION = ast.literal_eval(line[len("__version__ = ") :].strip())
            break
if VERSION is None:
    raise EnvironmentError("failed to read version")


# Put everything in setup.cfg, except those that don't actually work?
setup(
    # These really don't work.
    package_dir={"": "src"},
    packages=find_packages("src"),
    # I don't know how to specify an empty key in setup.cfg.
    package_data={"": ["LICENSE*", "README*"]},
    # I need this to be dynamic.
    version=VERSION,
)
