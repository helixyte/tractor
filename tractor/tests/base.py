"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from unittest import TestCase

__docformat__ = 'reStructuredText en'
__all__ = ['BaseTestCase']


class BaseTestCase(TestCase):
    """
    Base class for tests with PEP8 compliant method names.
    """

    assert_true = TestCase.assertTrue

    assert_false = TestCase.assertFalse

    assert_equal = TestCase.assertEqual

    assert_equals = TestCase.assertEquals

    assert_not_equal = TestCase.assertNotEqual

    assert_almost_equal = TestCase.assertAlmostEqual

    assert_not_almost_equal = TestCase.assertNotAlmostEqual

    assert_is_none = TestCase.assertIsNone

    assert_is_not_none = TestCase.assertIsNotNone

    assert_raises = TestCase.assertRaises

    def set_up(self):
        pass

    def tear_down(self):
        pass

    def setUp(self):
        self.set_up()

    def tearDown(self):
        self.tear_down()

