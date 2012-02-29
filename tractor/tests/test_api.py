"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from pkg_resources import resource_filename # pylint: disable=E0611
from tractor.api import TractorApi
from tractor.tests.base import BaseTestCase
from tractor.ticket import ATTRIBUTE_NAMES
from tractor.ticket import OwnerAttribute
from tractor.ticket import RESOLUTION_ATTRIBUTE_VALUES
from tractor.ticket import ReporterAttribute
from tractor.ticket import STATUS_ATTRIBUTE_VALUES
from tractor.tractor import AttachmentWrapper
from tractor.tractor import Base64Converter
from tractor.tractor import TicketWrapper
from tractor.tractor import create_wrapper_for_ticket_creation
from tractor.tractor import create_wrapper_for_ticket_update
from tractor.tractor import make_api
from tractor.tractor import make_api_from_config
from xmlrpclib import Fault


class TractorApiTestCase(BaseTestCase):

    def test_create_from_config(self):
        fn = resource_filename('tractor', 'tests/test_simple.ini')
        api = make_api_from_config(fn)
        self.assertTrue(isinstance(api, TractorApi))

    def test_create_ticket(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        notify = False
        ticket_id = api.create_ticket(t_wrapper, notify)
        t_wrapper2 = self.__create_ticket_wrapper(summary='Test Ticket 2',
                                            description='Another Test Ticket.')
        ticket_id2 = api.create_ticket(t_wrapper2)
        self.assert_not_equal(ticket_id, ticket_id2)

    def create_ticket_with_minimum_user_input(self):
        t_wrapper = create_wrapper_for_ticket_creation(
                                summary='Test Ticket.',
                                description='A standard test ticket.')
        self.assert_equal(t_wrapper.summary, 'Test Ticket.')
        self.assert_equal(t_wrapper.description, 'A standard test ticket.')
        create_attrs = t_wrapper.get_value_map_for_ticket_creation()
        self.assert_is_not_none(create_attrs)
        api = self.__create_api()
        ticket_id = api.create_ticket(t_wrapper, False)
        self.assert_is_not_none(ticket_id)

    def test_get_ticket(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        get_ticket = api.get_ticket(ticket_id)
        self.assert_equal(get_ticket.ticket_id, ticket_id)
        self.assert_is_not_none(get_ticket.time)
        self.assert_equal(get_ticket.changetime, get_ticket.time)
        for attr_name, attr_cls in ATTRIBUTE_NAMES.iteritems():
            ori_value = getattr(t_wrapper, attr_name)
            get_value = getattr(get_ticket, attr_name)
            if attr_name == ReporterAttribute.NAME \
                                        or attr_name == OwnerAttribute.NAME:
                # are set by the trac automatically
                self.assert_is_not_none(get_value)
            elif not ori_value is None:
                self.assert_equal(ori_value, get_value)
            elif attr_cls.IS_OPTIONAL or attr_cls.DEFAULT_VALUE is None:
                self.assert_is_none(get_value)
            else:
                self.assert_equal(get_value, attr_cls.DEFAULT_VALUE)

    def test_update_ticket(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        self.assert_is_none(t_wrapper.milestone)
        update_wrapper = create_wrapper_for_ticket_update(ticket_id=ticket_id,
                                            milestone='milestone1')
        updated_ticket = api.update_ticket(update_wrapper)
        self.assert_equal(updated_ticket.milestone, 'milestone1')
        self.assert_is_not_none(updated_ticket.time)
        self.assert_is_not_none(updated_ticket.changetime)

    def test_assign_ticket(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        self.assert_is_none(t_wrapper.owner)
        other_user = 'another user'
        assigned_ticket = api.assign_ticket(ticket_id, other_user)
        self.assert_is_not_none(assigned_ticket.time)
        self.assert_is_not_none(assigned_ticket.changetime)
        self.assert_equal(assigned_ticket.owner, other_user)

    def test_close_ticket(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        self.assert_is_none(t_wrapper.resolution)
        self.assert_not_equal(t_wrapper.status, STATUS_ATTRIBUTE_VALUES.CLOSED)
        res_state = RESOLUTION_ATTRIBUTE_VALUES.WORKSFORME
        closed_ticket = api.close_ticket(ticket_id, res_state)
        self.assert_equal(closed_ticket.status, STATUS_ATTRIBUTE_VALUES.CLOSED)
        self.assert_equal(closed_ticket.resolution, res_state)

    def test_delete_ticket(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        self.assert_true(api.delete_ticket(ticket_id))
        self.assert_raises(Fault, api.get_ticket, ticket_id)

    def test_add_attachment(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        att = self.__create_attachment_wrapper()
        file_name1 = api.add_attachment(ticket_id, att, replace_existing=True)
        self.assert_equal(att.file_name, file_name1)
        file_name2 = api.add_attachment(ticket_id, att, replace_existing=True)
        self.assert_equal(file_name1, file_name2)
        file_name3 = api.add_attachment(ticket_id, att, replace_existing=False)
        self.assert_not_equal(file_name1, file_name3)

    def test_get_attachment(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        att = self.__create_attachment_wrapper()
        file_name = api.add_attachment(ticket_id, att)
        binary_content = api.get_attachment(ticket_id, file_name)
        self.assert_is_not_none(binary_content)
        content = Base64Converter.decode_to_string(binary_content)
        self.assert_equal(content, att.content)

    def test_get_all_attachments(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        att1 = self.__create_attachment_wrapper()
        fn1 = api.add_attachment(ticket_id, att1)
        att2 = self.__create_attachment_wrapper(file_name='other.txt',
                                             content='some content',
                                             description='Another attachment.')
        fn2 = api.add_attachment(ticket_id, att2)
        att_info = api.get_all_ticket_attachments(ticket_id)
        self.assert_equal(len(att_info), 2)
        for att in att_info:
            self.assert_is_not_none(att.author)
            self.assert_is_not_none(att.size)
            self.assert_is_not_none(att.time)
            self.assert_is_none(att.content)
            if att.file_name == fn2:
                self.assert_equal(att.description, 'Another attachment.')
            else:
                self.assert_equal(att.file_name, fn1)
                self.assert_equal(att.description, 'An arbitrary test file.')
        att_info2 = api.get_all_ticket_attachments(ticket_id,
                                                   fetch_content=True)
        self.assert_equal(len(att_info2), 2)
        for att in att_info2:
            self.assert_is_not_none(att.author)
            self.assert_is_not_none(att.size)
            self.assert_is_not_none(att.time)
            self.assert_is_not_none(att.content)
            if att.file_name == fn2:
                self.assert_equal(att.description, 'Another attachment.')
            else:
                self.assert_equal(att.file_name, 'test_file.txt')
                self.assert_equal(att.description, 'An arbitrary test file.')

    def delete_attachment(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        att = self.__create_attachment_wrapper()
        file_name = api.add_attachment(ticket_id, att)
        self.assert_true(api.delete_attachment(ticket_id, file_name))
        self.assert_raises(Fault, api.get_attachment,
                           *(ticket_id, file_name))

    def test_ticket_id_and_att_file_name_not_none(self):
        api = self.__create_api()
        t_wrapper = self.__create_ticket_wrapper()
        ticket_id = api.create_ticket(t_wrapper)
        self.assert_raises(ValueError, api.get_ticket, None)
        self.assert_raises(ValueError, api.update_ticket, TicketWrapper())
        self.assert_raises(ValueError, api.assign_ticket, *(None, 'user1'))
        self.assert_raises(ValueError, api.close_ticket, *(None, 'closed'))
        self.assert_raises(ValueError, api.delete_ticket, None)
        att = self.__create_attachment_wrapper()
        self.assert_raises(ValueError, api.add_attachment, *(None, att))
        fn = api.add_attachment(ticket_id, att)
        self.assert_raises(ValueError, api.get_attachment, *(None, fn))
        self.assert_raises(ValueError, api.get_all_ticket_attachments, None)
        self.assert_raises(ValueError, api.delete_attachment, *(None, fn))
        self.assert_raises(ValueError, api.get_attachment, *(ticket_id, None))
        self.assert_raises(ValueError, api.delete_attachment, *(ticket_id, None))

    def __create_api(self, **kw):
        if not 'username' in kw: kw['username'] = 'test_user'
        if not 'password' in kw: kw['password'] = 'password'
        if not 'realm' in kw:
            kw['realm'] = 'http://mycompany.com/mytrac/login/xmlrpc'
        if not 'load_dummy' in kw: kw['load_dummy'] = True
        return make_api(**kw)

    def __create_ticket_wrapper(self, **kw):
        if not 'summary' in kw:
            kw['summary'] = 'Test Ticket'
        if not 'description' in kw:
            kw['description'] = 'A standard Test Ticket.'
        return TicketWrapper(**kw)

    def __create_attachment_wrapper(self, **kw):
        if not 'content' in kw:
            kw['content'] = 'This is a test attachment.'
        if not 'file_name' in kw:
            kw['file_name'] = 'test_file.txt'
        if not 'description' in kw:
            kw['description'] = 'An arbitrary test file.'
        return AttachmentWrapper(**kw)
