"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from .attachment import AttachmentWrapper
from .attachment import Base64Converter
from .ticket import ATTRIBUTE_NAMES
from .ticket import TicketWrapper
from datetime import datetime
from xmlrpclib import Fault
from xmlrpclib import ProtocolError

__docformat__ = 'reStructuredText en'
__all__ = ['DummyConnection',
           'DummyTrac',
           'DummyTicket',
           'DummyAttachment',
           'DUMMY_TRAC',
           'INVALID_USER',
           'GET_ONLY_USER',
           'INVALID_PASSWORD',
           'INVALID_REALM']


class DummyConnection(object):
    """
    A dummy connection for testing purposes.
    """

    def __init__(self, is_valid_connection, get_only, url):
        """
        Constructor.
        """
        self.ticket = DUMMY_TRAC
        self.ticket.get_only = get_only
        self.ticket.is_valid_connection = is_valid_connection
        self.ticket.url = url


class DummyTrac(object):
    """
    A dummy trac faking rturn values.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.ticket_counter = 0
        self.__ticket_map = dict()

        self.is_valid_connection = None # Is set by the connection
        self.get_only = None # Is set by the the connection
        self.url = None # Is set be the connection

    def __has_valid_connection(self, needs_extended_permissions=True):
        """
        Checks whether the connection is valid and whether the user
        has the required permissions.
        """
        if not self.is_valid_connection:
            raise ProtocolError(url=self.url, errcode=404, errmsg='Not found',
                                headers=None)

        if needs_extended_permissions and self.get_only:
            raise ProtocolError(url=self.url, errcode=401,
                                errmsg='Authorization Required.',
                                headers=None)

    def __raise_fault(self, meth_name, fault_string):
        """
        Helper method raising a fault.

        :Note: The fault messages are not exactly the same like in a
            real trac but more generalized.
        """
        msg = '\'%s\' while executing %s.' % (fault_string, meth_name)
        raise Fault(faultCode=2, faultString=msg)

    @property
    def user(self):
        """
        The user "logged in".
        """
        return self.url.split(':')[1][2:]

    def create(self, summary, description, attributes, notify):
        """
        Fake ticket creation.
        """
        self.__has_valid_connection(needs_extended_permissions=True)
        meth_name = 'ticket.create()'

        if summary is None or description is None or attributes is None \
                                                        or notify is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        elif isinstance(summary, list) or isinstance(summary, dict) or \
            isinstance(description, list) or isinstance(description, dict):
            self.__raise_fault(meth_name,
                               'Multi-values fields not supported yet')
        if not isinstance(attributes, dict):
            self.__raise_fault(meth_name, '\'%s\' has not attribute ' \
                            '\'iteritems()\'' % attributes.__class__.__name__)

        if not attributes.has_key('reporter'):
            attributes['reporter'] = self.user
        if not attributes.has_key('owner'):
            attributes['owner'] = self.user

        self.ticket_counter += 1
        ticket = DummyTicket(ticket_id=self.ticket_counter,
                             summary=summary,
                             description=description, **attributes)
        self.__ticket_map[ticket.ticket_id] = ticket
        return ticket.ticket_id

    def get(self, ticket_id):
        """
        Fake ticket getting.
        """
        self.__has_valid_connection(needs_extended_permissions=False)
        meth_name = 'ticket.get()'

        if ticket_id is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        elif not self.__ticket_map.has_key(ticket_id):
            self.__raise_fault(meth_name,
                               'Ticket %s does not exist.' % (ticket_id))

        ticket = self.__ticket_map[ticket_id]
        return ticket.get_trac_data_tuple()

    def update(self, ticket_id, comment, attributes, notify):
        """
        Fakes a ticket update.
        """
        self.__has_valid_connection(needs_extended_permissions=True)
        meth_name = 'ticket.update()'

        if ticket_id is None or comment is None or attributes is None \
                                                or notify is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        if not self.__ticket_map.has_key(ticket_id):
            self.__raise_fault(meth_name,
                               'Ticket %s does not exist.' % (ticket_id))
        if not isinstance(attributes, dict):
            self.__raise_fault(meth_name, '\'%s\' has not attribute ' \
                            '\'iteritems()\'' % attributes.__class__.__name__)

        ticket = self.__ticket_map[ticket_id]
        ticket.comments.append(comment)
        for attr_name, attr_value in attributes.iteritems():
            setattr(ticket, attr_name, attr_value)
        ticket.changetime = datetime.now()

        return ticket.get_trac_data_tuple()

    def delete(self, ticket_id):
        """
        Fakes a ticket delete.
        """
        self.__has_valid_connection(needs_extended_permissions=True)
        meth_name = 'ticket.delete()'

        if ticket_id is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        elif not self.__ticket_map.has_key(ticket_id):
            self.__raise_fault(meth_name,
                               'Ticket %s does not exist.' % (ticket_id))

        del self.__ticket_map[ticket_id]
        return 0

    def putAttachment(self, ticket_id, file_name, description, base64_data,
                      replace_existing):
        """
        Fakes an attachment addition.
        """
        self.__has_valid_connection(needs_extended_permissions=True)
        meth_name = 'ticket.putAttachment()'

        if ticket_id is None or file_name is None or description is None \
                        or base64_data is None or replace_existing is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        if not self.__ticket_map.has_key(ticket_id):
            self.__raise_fault(meth_name,
                               'Ticket %s does not exist.' % (ticket_id))
        if not isinstance(file_name, basestring):
            self.__raise_fault(meth_name, 'Invalid file name')

        try:
            content = Base64Converter.decode_to_string(base64_data)
        except AttributeError:
            self.__raise_fault(meth_name, '\'%s\' has not attribute \'data\'' \
                               % base64_data.__class__.__name__)

        attachment = DummyAttachment(file_name=file_name,
                                     description=description,
                                     content=content,
                                     author=self.user)
        ticket = self.__ticket_map[ticket_id]
        fn = ticket.add_attachment(attachment, replace_existing)
        return fn

    def getAttachment(self, ticket_id, file_name):
        """
        Fakes a get attachment operation.
        """
        self.__has_valid_connection(needs_extended_permissions=False)
        meth_name = 'ticket.getAttachment()'

        if ticket_id is None or file_name is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')

        if not isinstance(file_name, basestring):
            self.__raise_fault(meth_name, 'Invalid file name.')
        if self.__ticket_map.has_key(ticket_id):
            ticket = self.__ticket_map[ticket_id]
            att = ticket.get_attachment(file_name)
            if not att is None:
                return att.get_base64_data_for_upload()

        self.__raise_fault(meth_name,
                        ('AttachmentWrapper \'ticket:%s: %s\' does not exist.' \
                        % (ticket_id, file_name)))

    def listAttachments(self, ticket_id):
        """
        Fakes a request for all attachments of a ticket.
        """
        self.__has_valid_connection(needs_extended_permissions=False)
        meth_name = 'ticket.listAttachments()'

        if ticket_id is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        elif not self.__ticket_map.has_key(ticket_id):
            self.__raise_fault(meth_name,
                               'Ticket %s does not exist.' % (ticket_id))

        ticket = self.__ticket_map[ticket_id]
        return ticket.get_all_attachments()

    def deleteAttachment(self, ticket_id, file_name):
        """
        Fakes an attachment deletion.
        """
        self.__has_valid_connection(needs_extended_permissions=True)
        meth_name = 'ticket.deleteAttachment()'

        if ticket_id is None or file_name is None:
            raise TypeError('cannot marshal None unless allow_none is enabled')
        if not self.__ticket_map.has_key(ticket_id):
            self.__raise_fault(meth_name,
                               'Ticket %s does not exist.' % (ticket_id))
        if not isinstance(file_name, basestring):
            self.__raise_fault(meth_name, 'Invalid file name.')

        ticket = self.__ticket_map[ticket_id]
        success = ticket.delete_attachment(file_name)
        if not success:
            self.__raise_fault(meth_name,
                    ('AttachmentWrapper \'ticket:%s: %s\' does not exist.' \
                    % (ticket_id, file_name)))

        return success


class DummyTicket(TicketWrapper):
    """
    A dummy ticket for testing purposes.
    """

    def __init__(self, ticket_id, **kw):
        TicketWrapper.__init__(self, ticket_id=ticket_id, **kw)

        for attr_name, attr_value in kw.iteritems():
            attr_value = attr_value.strip()
            setattr(self, attr_name, attr_value)

        self.time = datetime.now()
        self.changetime = self.time

        self.comments = []
        self.__attachment_map = dict()
        self.__file_name_map = dict()

    def add_attachment(self, attachment, replace_existing):
        """
        Adds a dummy attachment.
        """
        fn = attachment.file_name
        if not self.__file_name_map.has_key(fn):
            self.__file_name_map[fn] = 1
        else:
            if not replace_existing:
                self.__file_name_map[fn] += 1
                new_fn = fn + '.%i' % (self.__file_name_map[fn])
                attachment.file_name = new_fn
                attachment.time = datetime.now()

        self.__attachment_map[attachment.file_name] = attachment
        self.comments.append(attachment.description)

        return attachment.file_name

    def get_attachment(self, file_name):
        """
        Returns a dummy attachment (if there is any).
        """
        if self.__attachment_map.has_key(file_name):
            return self.__attachment_map[file_name]
        else:
            return None

    def get_all_attachments(self):
        """
        Returns trac-like attachment info list.
        """
        attachments = []
        for att in self.__attachment_map.values():
            attachments.append(att.get_trac_data_tuple())
        return attachments

    def delete_attachment(self, file_name):
        """
        Deletes an attachment from the dummy ticket.
        """
        if not self.__attachment_map.has_key(file_name):
            return False

        del self.__attachment_map[file_name]
        return True

    def get_trac_data_tuple(self):
        """
        Returns trac-like ticket data.
        """

        attributes = dict()
        for attr_name in ATTRIBUTE_NAMES.keys():
            value = getattr(self, attr_name)
            if value is None:
                value = ''
            attributes[attr_name] = value
        return (self.ticket_id, self.time, self.changetime,
                attributes)


class DummyAttachment(AttachmentWrapper):

    def __init__(self, **kw):
        AttachmentWrapper.__init__(self, **kw)

        for attr_name, attr_value in kw.iteritems():
            setattr(self, attr_name, attr_value)
        self.time = datetime.now()
        if not self.content is None:
            self.size = len(self.content)

    def get_trac_data_tuple(self):
        """
        Returns trac-like attachment info.
        """
        return (self.file_name, self.description, self.size, self.time,
                self.author)


DUMMY_TRAC = DummyTrac()
INVALID_USER = 'unknown_user'
GET_ONLY_USER = 'user_get_only'
INVALID_PASSWORD = 'invalid_pw'
INVALID_REALM = 'http://company.com/invalidpath/login/xmlrpc'
