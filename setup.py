"""
The OntoFlow workflow builder.

This also include the triplestore subpackage, which provides a common
frontend to a set of different triplestores.
"""
import os
import re
from pathlib import Path

import setuptools

rootdir = Path(__file__).absolute().parent


# Read long description from README.md file replacing references to local
# files to github urls
BASE_URL = "https://raw.githubusercontent.com/EMMC-ASBL/OntoFlow/master/"
with open(rootdir / "README.md", "rt") as handle:
    long_description = re.sub(
        r"(\[[^]]+\])\(([^:)]+)\)", rf"\1({BASE_URL}\2)", handle.read()
    )

# Read requirements from requirements.txt file
with open(rootdir / "requirements.txt", "rt") as handle:
    REQUIREMENTS = [
        f"{line.strip()}"
        for line in handle.readlines()
        if not line.startswith("#") and "git+" not in line
    ]

# Retrieve package version
with open(os.path.join(rootdir, "ontoflow/__init__.py")) as handle:
    for line in handle:
        match = re.match(r"__version__ = ('|\")(?P<version>.*)('|\")", line)
        if match is not None:
            VERSION = match.group("version")
            break
    else:
        raise RuntimeError(f"Could not determine package version from {handle.name} !")


setuptools.setup(
    name="OntoFlow",
    version=VERSION,
    author="University of Bologna",
    author_email="alessandro.calvio@unibo.it",
    description="Workflow builder.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emmc-asbl/OntoFlow",
    license="MIT",
    python_requires="~=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=REQUIREMENTS,
    packages=setuptools.find_packages(),
    scripts=[],
    package_data={},
    # include_package_data=True,
    data_files=[
        ("share/OntoFlow", ["README.md", "LICENSE"]),
    ],
)
