"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from datetime import datetime
from tractor.tests.base import BaseTestCase
from tractor.ticket import ATTRIBUTE_NAMES
from tractor.ticket import ATTRIBUTE_OPTIONS
from tractor.ticket import DescriptionAttribute
from tractor.ticket import PRIORITY_ATTRIBUTE_VALUES
from tractor.ticket import PriorityAttribute
from tractor.ticket import SEVERITY_ATTRIBUTE_VALUES
from tractor.ticket import STATUS_ATTRIBUTE_VALUES
from tractor.ticket import SummaryAttribute
from tractor.ticket import TYPE_ATTRIBUTE_VALUES
from tractor.ticket import TicketAttribute
from tractor.ticket import TicketWrapper


class TicketAttributeTest(BaseTestCase):

    def set_up(self):
        BaseTestCase.set_up(self)
        self.summ_name = SummaryAttribute.NAME
        self.summ_value = 'Test TicketWrapper'
        self.prio_name = PriorityAttribute.NAME
        self.prio_value = PRIORITY_ATTRIBUTE_VALUES.LOW

    def test_create_by_name(self):
        summary_attr = TicketAttribute.create_by_name(self.summ_name,
                                                      self.summ_value)
        self.assert_true(isinstance(summary_attr, SummaryAttribute))
        self.assert_equal(summary_attr.value, self.summ_value)
        # Test lookup use
        test_lookup = {PriorityAttribute.NAME : PriorityAttribute}
        prio_attr = TicketAttribute.create_by_name(self.prio_name,
                                                   self.prio_value,
                                                   test_lookup)
        self.assert_true(isinstance(prio_attr, PriorityAttribute))
        self.assert_equal(prio_attr.value, self.prio_value)
        error_values = (self.summ_name, self.summ_value, test_lookup)
        self.assert_raises(KeyError, TicketAttribute.create_by_name,
                           *error_values)


class TicketTestCase(BaseTestCase):

    def set_up(self):
        BaseTestCase.set_up(self)
        self.init_data = dict(ticket_id=123,
                         summary='Test TicketWrapper',
                         description='This is a standard test ticket.',
                         reporter='user1',
                         owner='me',
                         cc='user2, user3',
                         type=TYPE_ATTRIBUTE_VALUES.ENHANCEMENT,
                         status=STATUS_ATTRIBUTE_VALUES.NEW,
                         priority=PRIORITY_ATTRIBUTE_VALUES.LOWEST,
                         severity=SEVERITY_ATTRIBUTE_VALUES.TRIVIAL,
                         milestone='1024 km',
                         component='default component',
                         resolution=None,
                         keywords='tractor, test, ticket')

    def test_init(self):
        # empty ticket
        ticket1 = TicketWrapper()
        self.assert_is_none(ticket1.ticket_id)
        for attr_name in ATTRIBUTE_NAMES:
            self.assert_is_none(getattr(ticket1, attr_name))
        # value setting
        ticket2 = TicketWrapper(**self.init_data)
        for attr_name, exp_value in self.init_data.iteritems():
            self.assert_equal(getattr(ticket2, attr_name), exp_value)

    def test_create_from_trac_data(self):
        ticket_id = 123
        time_created = datetime.now()
        time_changed = None
        del self.init_data['ticket_id']
        trac_data = (ticket_id, time_created, time_changed, self.init_data)
        ticket = TicketWrapper.create_from_trac_data(trac_data)
        self.assert_equal(ticket.ticket_id, ticket_id)
        self.assert_equal(ticket.time, time_created)
        self.assert_equal(ticket.changetime, time_changed)
        for attr_name, exp_value in self.init_data.iteritems():
            self.assert_equal(getattr(ticket, attr_name), exp_value)

    def test_attribute_validity(self):
        ticket = TicketWrapper(**self.init_data)
        # None for non-optional value
        ticket.check_attribute_validity(SummaryAttribute.NAME)
        ticket.summary = None
        self.assert_raises(ValueError, ticket.check_attribute_validity,
                           SummaryAttribute.NAME)
        ticket.check_attribute_validity(SummaryAttribute.NAME, 'ticket title')
        # Invalid option
        ticket.check_attribute_validity(PriorityAttribute.NAME)
        ticket.priority = TestAlternativePriorityOptions.UNREGISTERED
        self.assert_raises(ValueError, ticket.check_attribute_validity,
                           PriorityAttribute.NAME)
        ticket.check_attribute_validity(PriorityAttribute.NAME,
                                        PRIORITY_ATTRIBUTE_VALUES.LOW)
        # test lookup usage
        alt_lookup = ATTRIBUTE_OPTIONS
        alt_lookup[PriorityAttribute.NAME] = TestAlternativePriorityOptions
        alt_ticket = TicketWrapper(priority=\
                                TestAlternativePriorityOptions.UNREGISTERED,
                            attribute_options_lookup=alt_lookup)
        alt_ticket.check_attribute_validity(PriorityAttribute.NAME)

    def test_get_value_map_for_ticket_creation(self):
        # Priority should be replaced by a default value.
        self.init_data[PriorityAttribute.NAME] = None
        ticket = TicketWrapper(**self.init_data)
        value_map = ticket.get_value_map_for_ticket_creation()
        self.assert_false(value_map.has_key(SummaryAttribute.NAME))
        self.assert_false(value_map.has_key(DescriptionAttribute.NAME))
        for attr_name in ATTRIBUTE_NAMES.keys():
            if attr_name == SummaryAttribute.NAME or \
                    attr_name == DescriptionAttribute.NAME: continue
            if not value_map.has_key(attr_name):
                self.assert_is_none(getattr(ticket, attr_name))
                continue
            ticket.check_attribute_validity(attr_name, value_map[attr_name])
            if attr_name == PriorityAttribute.NAME:
                self.assert_equal(value_map[attr_name],
                                  PriorityAttribute.DEFAULT_VALUE)
            else:
                self.assert_equal(getattr(ticket, attr_name),
                                  self.init_data[attr_name])

    def get_value_map_for_update(self):
        # Empty ticket return empty maps.
        ticket = TicketWrapper(ticket_id=123)
        value_map1 = ticket.get_value_map_for_update()
        self.assert_equal(len(value_map1), 0)
        # Otherwise the map should contain all not None value.
        ticket.summary = 'Test TicketWrapper'
        ticket.priority = PRIORITY_ATTRIBUTE_VALUES.LOW
        value_map2 = ticket.get_value_map_for_update()
        self.assert_equal(len(value_map2), 2)
        self.assert_equal(value_map2[SummaryAttribute.NAME], 'Test TicketWrapper')
        self.assert_equal(value_map2[PriorityAttribute.NAME],
                          PRIORITY_ATTRIBUTE_VALUES.LOW)


class TestAlternativePriorityOptions(PRIORITY_ATTRIBUTE_VALUES):

    UNREGISTERED = 'unregistered value'
    ALL = PRIORITY_ATTRIBUTE_VALUES.ALL + [UNREGISTERED]
