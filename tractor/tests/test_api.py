"""
This file is part of the tractor library. 
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from pkg_resources import resource_filename # pylint: disable=E0611
from tractor.api import make_api_from_config
from unittest import TestCase
from tractor.api import TractorApi


class TractorApiTestCase(TestCase):
    def test_create_from_config(self):
        fn = resource_filename('tractor', 'tests/test_simple.ini')
        api = make_api_from_config(fn)
        self.assertTrue(isinstance(api, TractorApi))

