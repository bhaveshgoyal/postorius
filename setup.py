# Copyright (C) 2012-2014 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Postorius.  If not, see <http://www.gnu.org/licenses/>.

try:
    import setuptools
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()

from setuptools import setup, find_packages


setup(
    name="postorius",
    version='1.0.3',
    description="A web user interface for GNU Mailman",
    long_description=open('README.rst').read(),
    maintainer="The Mailman GSOC Coders",
    license='GPLv3',
    keywords='email mailman django',
    url="https://launchpad.net/postorius",
    classifiers=[
        "Programming Language :: Python",
        ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=['django>=1.6,<1.9',
                      'django-browserid',
                      'mailmanclient']
)
