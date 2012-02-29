"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from StringIO import StringIO
from tractor.attachment import AttachmentWrapper
from tractor.dummy import DummyAttachment
from tractor.dummy import DummyTicket
from tractor.dummy import DummyTrac
from tractor.dummy import GET_ONLY_USER
from tractor.dummy import INVALID_PASSWORD
from tractor.dummy import INVALID_REALM
from tractor.dummy import INVALID_USER
from tractor.tests.base import BaseTestCase
from tractor.ticket import ATTRIBUTE_NAMES
from tractor.ticket import PRIORITY_ATTRIBUTE_VALUES
from tractor.ticket import SEVERITY_ATTRIBUTE_VALUES
from tractor.ticket import STATUS_ATTRIBUTE_VALUES
from tractor.ticket import TYPE_ATTRIBUTE_VALUES
from tractor.ticket import TicketWrapper
from xmlrpclib import Fault
from xmlrpclib import ProtocolError


class DummyAttachmentTestCase(BaseTestCase):

    def set_up(self):
        BaseTestCase.set_up(self)
        self.init_data = dict(content='dummy_attachment_test',
                              file_name='test_file.txt',
                              description='A dummy attachment.',
                              author='user1')

    def test_init(self):
        att = DummyAttachment(**self.init_data)
        self.init_data['size'] = len(att.content)
        for attr_name, exp_val in self.init_data.iteritems():
            self.assert_equal(getattr(att, attr_name), exp_val)
        self.assert_is_not_none(att.time)

    def test_get_trac_data_tuple(self):
        att = DummyAttachment(**self.init_data)
        exp_data = ('test_file.txt', 'A dummy attachment.', 21, att.time,
                    'user1')
        self.assert_equal(att.get_trac_data_tuple(), exp_data)


class DummyTicketTestCase(BaseTestCase):

    def set_up(self):
        BaseTestCase.set_up(self)
        self.init_data = dict(ticket_id=123,
                              summary='dummy test ticket',
                              description='This is a dummy test ticket.',
                              reporter='user1',
                              owner='user2',
                              cc='user3, user4',
                              type=TYPE_ATTRIBUTE_VALUES.ENHANCEMENT,
                              status=STATUS_ATTRIBUTE_VALUES.NEW,
                              priority=PRIORITY_ATTRIBUTE_VALUES.LOWEST,
                              severity=SEVERITY_ATTRIBUTE_VALUES.TRIVIAL,
                              milestone='1024 km',
                              component='None',
                              keywords='dummy, ticket, tractor')

    def __create_dummy_attachment(self, **kw):
        att_init_data = dict(content='dummy_attachment_test',
                              file_name='test_file.txt',
                              description='A dummy attachment.',
                              author='user1')
        for attr_name, value in kw.iteritems():
            att_init_data[attr_name] = value
        return DummyAttachment(**att_init_data)

    def test_init(self):
        ticket = DummyTicket(**self.init_data)
        self.assert_is_not_none(ticket.time)
        self.assert_equal(ticket.changetime, ticket.time)
        self.assert_equal(len(ticket.comments), 0)
        for attr_name, exp_val in self.init_data.iteritems():
            self.assert_equal(getattr(ticket, attr_name), exp_val)

    def test_add_attachment(self):
        ticket = DummyTicket(**self.init_data)
        self.assert_equal(len(ticket.comments), 0)
        att = self.__create_dummy_attachment()
        ticket.add_attachment(att, replace_existing=True)
        self.assert_equal(len(ticket.comments), 1)
        self.assert_equal(ticket.comments[0], att.description)

    def test_get_attachment(self):
        ticket = DummyTicket(**self.init_data)
        att = self.__create_dummy_attachment()
        ticket.add_attachment(att, replace_existing=True)
        att_fn = att.file_name
        ticket_att = ticket.get_attachment(att_fn)
        self.assert_equal(ticket_att.file_name, att_fn)
        self.assert_equal(ticket_att.content, 'dummy_attachment_test')
        self.assert_is_none(ticket.get_attachment('other file'))

    def test_get_all_attachments(self):
        ticket = DummyTicket(**self.init_data)
        list1 = ticket.get_all_attachments()
        self.assert_equal(len(list1), 0)
        att1 = self.__create_dummy_attachment(file_name='file1.txt')
        ticket.add_attachment(att1, replace_existing=False)
        att2 = self.__create_dummy_attachment(file_name='file2.txt')
        ticket.add_attachment(att2, replace_existing=False)
        exp_list = [att1.get_trac_data_tuple(), att2.get_trac_data_tuple()]
        list2 = ticket.get_all_attachments()
        self.assert_equal(list2, exp_list)

    def test_add_attachment_replacing(self):
        ticket = DummyTicket(**self.init_data)
        file_name = 'test_file.txt'
        att1 = self.__create_dummy_attachment(file_name=file_name)
        ticket.add_attachment(att1, replace_existing=True)
        list1 = ticket.get_all_attachments()
        self.assert_equal(len(list1), 1)
        att2 = self.__create_dummy_attachment(content='different content',
                                              file_name=file_name)
        ticket.add_attachment(att2, replace_existing=True)
        list2 = ticket.get_all_attachments()
        self.assert_equal(len(list2), 1)
        ticket_att1 = ticket.get_attachment(file_name)
        self.assert_not_equal(ticket_att1.content, att1.content)
        self.assert_equal(ticket_att1.content, att2.content)
        att3 = self.__create_dummy_attachment(content='content version 3',
                                              file_name=file_name)
        ticket.add_attachment(att3, replace_existing=False)
        list3 = ticket.get_all_attachments()
        self.assert_equal(len(list3), 2)
        ticket_att2 = ticket.get_attachment(file_name)
        self.assert_equal(ticket_att2.content, att2.content)
        self.assert_not_equal(ticket_att2.content, att3.content)
        new_name = '%s.2' % (file_name)
        self.assert_is_not_none(ticket.get_attachment(new_name))

    def test_get_trac_data_tuple(self):
        ticket = DummyTicket(**self.init_data)
        exp_attr = dict()
        for attr_name in ATTRIBUTE_NAMES.keys():
            value = getattr(ticket, attr_name)
            if value is None:
                value = ''
            exp_attr[attr_name] = value
        exp_data = (123, ticket.time, ticket.changetime, exp_attr)
        self.assert_equal(ticket.get_trac_data_tuple(), exp_data)


class DummyTracTestCase(BaseTestCase):

    def __create_ticket_wrapper(self, **kw):
        ticket_init_data = dict(summary='dummy test ticket',
                                description='This is a dummy test ticket.',
                                reporter='user1',
                                owner='user2',
                                cc='user3, user4',
                                type=TYPE_ATTRIBUTE_VALUES.ENHANCEMENT,
                                status=STATUS_ATTRIBUTE_VALUES.NEW,
                                priority=PRIORITY_ATTRIBUTE_VALUES.LOWEST,
                                severity=SEVERITY_ATTRIBUTE_VALUES.TRIVIAL,
                                milestone='1024 km',
                                component='None',
                                keywords='dummy, ticket, tractor')
        for attr_name, value in kw.iteritems():
            ticket_init_data[attr_name] = value
        return TicketWrapper(**ticket_init_data)

    def __create_attachment_wrapper(self, **kw):
        att_init_data = dict(content='dummy_attachment_test',
                             file_name='test_file.txt',
                             description='A dummy attachment.')
        for attr_name, value in kw.iteritems():
            att_init_data[attr_name] = value
        return AttachmentWrapper(**att_init_data)

    def __alter_to_trac_with_invalid_connection(self, trac=None):
        if trac is None:
            trac = DummyTrac()
        trac.is_valid_connection = False
        return trac

    def __alter_to_trac_with_get_only_permission(self, trac=None):
        if trac is None:
            trac = DummyTrac()
        trac.is_valid_connection = True
        trac.get_only = True
        url = 'http://%s:%s@%s' % (GET_ONLY_USER, INVALID_PASSWORD,
                                   INVALID_REALM)
        trac.url = url
        return trac

    def __alter_to_trac_with_all_permissions(self, trac=None):
        if trac is None:
            trac = DummyTrac()
        trac.is_valid_connection = True
        trac.get_only = False
        url = 'http://%s:%s@%s' % (INVALID_USER, INVALID_PASSWORD,
                                   INVALID_REALM)
        trac.url = url
        return trac

    def test_init(self):
        trac = DummyTrac()
        self.assert_is_none(trac.is_valid_connection)
        self.assert_is_none(trac.get_only)
        self.assert_equal(trac.ticket_counter, 0)

    def test_create(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection()
        self.assert_raises(ProtocolError, trac.create, *ticket_data)
        # invalid permission
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        self.assert_raises(ProtocolError, trac.create, *ticket_data)
        # success
        trac = self.__alter_to_trac_with_all_permissions(trac)
        self.assert_equal(trac.ticket_counter, 0)
        return_value = trac.create(*ticket_data)
        self.assert_equal(return_value, 1)
        self.assert_equal(trac.ticket_counter, 1)
        # invalid arguments
        ticket_data = (3, ticket.description, create_attrs, True)
        self.assert_raises(AttributeError, trac.create, *ticket_data)
        ticket_data = (None, ticket.description, create_attrs, True)
        self.assert_raises(TypeError, trac.create, *ticket_data)
        ticket_data = ([ticket.summary], ticket.description, create_attrs, True)
        self.assert_raises(Fault, trac.create, *ticket_data)
        ticket_data = (ticket.summary, None, create_attrs, True)
        self.assert_raises(TypeError, trac.create, *ticket_data)
        ticket_data = (ticket.summary, [ticket.description], create_attrs, True)
        self.assert_raises(Fault, trac.create, *ticket_data)
        ticket_data = (ticket.summary, ticket.description, 3, True)
        self.assert_raises(Fault, trac.create, *ticket_data)
        ticket_data = (ticket.summary, ticket.description, None, True)
        self.assert_raises(TypeError, trac.create, *ticket_data)
        ticket_data = (ticket.summary, ticket.description, create_attrs, None)
        self.assert_raises(TypeError, trac.create, *ticket_data)

    def test_get(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        trac = self.__alter_to_trac_with_all_permissions()
        ticket_id = trac.create(*ticket_data)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.get, ticket_id)
        # invalid permission = success
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        return_value = trac.get(ticket_id)
        self.assert_equal(len(return_value), 4)
        self.assert_equal(return_value[0], ticket_id)
        self.assert_is_not_none(return_value[1]) # time_created
        self.assert_equal(return_value[1], return_value[2]) # create & change
        attrs = return_value[3]
        for attr_name, value in attrs.iteritems():
            if value == '':
                value = None
            self.assert_equal(getattr(ticket, attr_name), value)
        # all permissions
        trac.get_only = False
        return_value = trac.get(ticket_id)
        self.assert_equal(len(return_value), 4)
        self.assert_equal(return_value[0], ticket_id)
        self.assert_is_not_none(return_value[1]) # time_created
        self.assert_equal(return_value[1], return_value[2]) # create & change
        attrs = return_value[3]
        for attr_name, value in attrs.iteritems():
            if value == '':
                value = None
            self.assert_equal(getattr(ticket, attr_name), value)
        # unknown ticket ID
        self.assert_raises(TypeError, trac.get, None)
        self.assert_raises(Fault, trac.get, 2)

    def test_update(self):
        ori_ticket = self.__create_ticket_wrapper()
        trac = self.__alter_to_trac_with_all_permissions()
        create_attrs = ori_ticket.get_value_map_for_ticket_creation()
        ticket_data = (ori_ticket.summary, ori_ticket.description,
                       create_attrs, True)
        ticket_id = trac.create(*ticket_data)
        self.assert_equal(trac.ticket_counter, 1)
        upd_ticket = TicketWrapper(description='changes in description',
                            owner='owner2')
        comment = 'A normal ticket update.'
        update_attrs = upd_ticket.get_value_map_for_update()
        update_data = (ticket_id, comment, update_attrs, True)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.update, *update_data)
        # invalid permission
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        self.assert_raises(ProtocolError, trac.update, *update_data)
        # success
        trac.get_only = False
        return_value = trac.update(*update_data)
        self.assert_equal(trac.ticket_counter, 1)
        self.assert_equal(len(return_value), 4)
        self.assert_equal(return_value[0], ticket_id)
        self.assert_is_not_none(return_value[1]) # created time
        self.assert_is_not_none(return_value[2]) # changetime
        self.assert_not_equal(return_value[1], return_value[2])
        attrs = return_value[3]
        for attr_name, value in attrs.iteritems():
            if update_attrs.has_key(attr_name):
                value_map = update_attrs
            elif create_attrs.has_key(attr_name):
                value_map = create_attrs
            else:
                value = getattr(ori_ticket, attr_name)
                if value == '':
                    value = None
                self.assert_equal(getattr(ori_ticket, attr_name), value)
                continue
            self.assert_equal(value_map[attr_name], value)
        get_ticket = trac.get(ticket_id)
        self.assert_equal(get_ticket, return_value)
        # invalid arguments
        update_data = ('123', comment, update_attrs, True)
        self.assert_raises(Fault, trac.update, *update_data)
        update_data = (None, comment, update_attrs, True)
        self.assert_raises(TypeError, trac.update, *update_data)
        update_data = (1, None, update_attrs, True)
        self.assert_raises(TypeError, trac.update, *update_data)
        update_data = (1, comment, None, True)
        self.assert_raises(TypeError, trac.update, *update_data)
        update_data = (1, comment, update_attrs.values(), True)
        self.assert_raises(Fault, trac.update, *update_data)
        update_data = (1, comment, update_attrs, None)
        self.assert_raises(TypeError, trac.update, *update_data)

    def test_delete(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        trac = self.__alter_to_trac_with_all_permissions()
        ticket_id = trac.create(*ticket_data)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.delete, ticket_id)
        # invalid permission
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        self.assert_raises(ProtocolError, trac.delete, ticket_id)
        # success
        trac = self.__alter_to_trac_with_all_permissions(trac)
        self.assert_equal(trac.delete(ticket_id), 0)
        # unknown ticket
        self.assert_raises(Fault, trac.delete, ticket_id)
        self.assert_raises(TypeError, trac.delete, None)

    def test_putAttachment(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        trac = self.__alter_to_trac_with_all_permissions()
        ticket_id = trac.create(*ticket_data)
        att = self.__create_attachment_wrapper()
        base64_data = att.get_base64_data_for_upload()
        att_data = (ticket_id, att.file_name, att.description, base64_data,
                    True)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.putAttachment, *att_data)
        # invalid permission
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        self.assert_raises(ProtocolError, trac.putAttachment, *att_data)
        # success
        trac = self.__alter_to_trac_with_all_permissions(trac)
        fn = trac.putAttachment(*att_data)
        self.assert_equal(fn, att.file_name)
        # success overwrite
        fn2 = trac.putAttachment(*att_data)
        self.assert_equal(fn, fn2)
        self.assert_equal(fn2, att.file_name)
        # success add
        fn3 = trac.putAttachment(ticket_id, att.file_name, att.description,
                                 base64_data, False)
        self.assert_not_equal(fn3, fn2)
        # invalid values
        att_data = (None, att.file_name, att.description, base64_data, True)
        self.assert_raises(TypeError, trac.putAttachment, *att_data)
        att_data = ('3', att.file_name, att.description, base64_data, True)
        self.assert_raises(Fault, trac.putAttachment, *att_data)
        att_data = (1, None, att.description, base64_data, True)
        self.assert_raises(TypeError, trac.putAttachment, *att_data)
        att_data = (1, 3, att.description, base64_data, True)
        self.assert_raises(Fault, trac.putAttachment, *att_data)
        att_data = (1, att.file_name, None, base64_data, True)
        self.assert_raises(TypeError, trac.putAttachment, *att_data)
        att_data = (1, att.file_name, att.description, None, True)
        self.assert_raises(TypeError, trac.putAttachment, *att_data)
        att_data = (1, att.file_name, att.description, StringIO(base64_data),
                    True)
        self.assert_raises(Fault, trac.putAttachment, *att_data)
        att_data = (1, att.file_name, att.description, base64_data, None)
        self.assert_raises(TypeError, trac.putAttachment, *att_data)

    def test_get_attachment(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        trac = self.__alter_to_trac_with_all_permissions()
        ticket_id = trac.create(*ticket_data)
        att = self.__create_attachment_wrapper()
        base64_data = att.get_base64_data_for_upload()
        file_name = trac.putAttachment(ticket_id, att.file_name, att.description,
                                       base64_data, True)
        att_info = (ticket_id, file_name)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.getAttachment, *att_info)
        # get permission only = success
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        ticket_base64 = trac.getAttachment(*att_info)
        self.assert_equal(base64_data, ticket_base64)
        # all permissions
        trac = self.__alter_to_trac_with_all_permissions(trac)
        ticket_base64 = trac.getAttachment(*att_info)
        self.assert_equal(base64_data, ticket_base64)
        # unknown ticket or file name
        self.assert_raises(Fault, trac.getAttachment, *(2, file_name))
        self.assert_raises(Fault, trac.getAttachment, *(ticket_id, 'inv'))
        self.assert_raises(TypeError, trac.getAttachment, *(None, file_name))
        self.assert_raises(TypeError, trac.getAttachment, *(ticket_id, None))

    def test_list_all_attachments(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        trac = self.__alter_to_trac_with_all_permissions()
        ticket_id = trac.create(*ticket_data)
        att = self.__create_attachment_wrapper()
        base64_data = att.get_base64_data_for_upload()
        file_name = trac.putAttachment(ticket_id, att.file_name,
                                       att.description, base64_data, True)
        att2 = self.__create_attachment_wrapper(file_name='file2.txt',
                                             content='Another test file.')
        base64_data2 = att2.get_base64_data_for_upload()
        file_name2 = trac.putAttachment(ticket_id, att2.file_name,
                                        att.description, base64_data2, True)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.listAttachments, ticket_id)
        # get permission only = success
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        trac_ticket_data = trac.listAttachments(ticket_id)
        self.assert_equal(len(trac_ticket_data), 2)
        for data_set in trac_ticket_data:
            self.assert_is_not_none(data_set[2]) # size
            self.assert_is_not_none(data_set[3]) # time
            self.assert_is_not_none(data_set[4]) # author
            if data_set[0] == file_name:
                self.assert_equal(data_set[1], att.description)
            else:
                self.assert_equal(data_set[0], file_name2)
                self.assert_equal(data_set[1], att2.description)
        # all permissions
        trac = self.__alter_to_trac_with_all_permissions(trac)
        trac_ticket_data = trac.listAttachments(ticket_id)
        self.assert_equal(len(trac_ticket_data), 2)
        for data_set in trac_ticket_data:
            self.assert_is_not_none(data_set[2]) # size
            self.assert_is_not_none(data_set[3]) # time
            self.assert_is_not_none(data_set[4]) # author
            if data_set[0] == file_name:
                self.assert_equal(data_set[1], att.description)
            else:
                self.assert_equal(data_set[0], file_name2)
                self.assert_equal(data_set[1], att2.description)
        # invalid arguments
        self.assert_raises(TypeError, trac.listAttachments, None)
        self.assert_raises(Fault, trac.listAttachments, 4)

    def test_delete_attachment(self):
        ticket = self.__create_ticket_wrapper()
        create_attrs = ticket.get_value_map_for_ticket_creation()
        ticket_data = (ticket.summary, ticket.description, create_attrs, True)
        trac = self.__alter_to_trac_with_all_permissions()
        ticket_id = trac.create(*ticket_data)
        att = self.__create_attachment_wrapper()
        base64_data = att.get_base64_data_for_upload()
        file_name = trac.putAttachment(ticket_id, att.file_name,
                                       att.description, base64_data, True)
        # invalid connection
        trac = self.__alter_to_trac_with_invalid_connection(trac)
        self.assert_raises(ProtocolError, trac.deleteAttachment,
                           *(ticket_id, file_name))
        # invalid permissions
        trac = self.__alter_to_trac_with_get_only_permission(trac)
        self.assert_raises(ProtocolError, trac.deleteAttachment,
                           *(ticket_id, file_name))
        # success
        trac = self.__alter_to_trac_with_all_permissions(trac)
        self.assert_true(trac.getAttachment(ticket_id, file_name))
        # invalid arguments
        self.assert_raises(TypeError, trac.deleteAttachment, *(None, file_name))
        self.assert_raises(TypeError, trac.deleteAttachment, *(ticket_id, None))
        self.assert_raises(Fault, trac.deleteAttachment, *(2, file_name))
        self.assert_raises(Fault, trac.deleteAttachment, *(1, 'fn'))

