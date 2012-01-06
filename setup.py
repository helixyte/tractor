"""
This file is part of the everest project.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Package setup file.

Created on Nov 3, 2011.
"""

import os

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

setup_requirements = []

install_requirements = [
    ]

tests_requirements = install_requirements + [
    'nose>=1.1.0,<=1.1.99',
    'nosexcover>=1.0.4,<=1.0.99',
    'coverage==3.4',
    ]

setup(name='tractor',
      version='0.1',
      description=
        'A Python library to manipulate Trac tickets programmatically.',
      long_description=README,
      classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        ],
      author='Anna-Antonia Berger',
      author_email='berger@cenix.com',
      license="MIT",
      url='https://github.com/cenix/tractor',
      keywords='web trac',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      setup_requires=setup_requirements,
      install_requires=install_requirements,
      tests_require=tests_requirements,
      test_suite="tractor/tests",
      entry_points="""
      """
      )
