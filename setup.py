#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-cache-toolbox',
    description="Non-magical object caching for Django.",
    version='0.2.4',
    url='https://chris-lamb.co.uk/projects/django-cache-toolbox',

    author='Chris Lamb',
    author_email='chris@chris-lamb.co.uk',
    license='BSD',

    packages=find_packages(exclude=('tests',)),

    install_requires=(
        "Django>=1.8",
    ),

    test_suite='tests',
)
