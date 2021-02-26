#!/usr/bin/env python3

import os.path
from setuptools import setup, find_packages

my_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(my_dir, "README.md")) as f:
    long_description = f.read()

setup(
    name="django-cache-toolbox",
    description="Non-magical object caching for Django.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version='1.6.0',
    url="https://chris-lamb.co.uk/projects/django-cache-toolbox",
    author="Chris Lamb",
    author_email="chris@chris-lamb.co.uk",
    license="BSD",
    packages=find_packages(exclude=("tests",)),
    install_requires=("Django>=1.9",),
)
