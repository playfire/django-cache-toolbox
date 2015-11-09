#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-cache-toolbox',
    description="Non-magical object caching for Django.",
    version='0.1',
    url='https://www.github.com/thread/django-cache-toolbox',

    author='Thread.com',
    author_email='tech@thread.com',
    license='BSD',

    packages=find_packages(exclude=('tests',)),

    install_requires=(
        "Django>=1.8",
    ),

    test_suite='tests',
)
