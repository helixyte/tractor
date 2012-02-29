"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

from .attachment import AttachmentWrapper
from .dummy import DummyConnection
from .dummy import GET_ONLY_USER
from .dummy import INVALID_REALM
from .dummy import INVALID_USER
from .ticket import OwnerAttribute
from .ticket import STATUS_ATTRIBUTE_VALUES
from .ticket import TicketWrapper
from xmlrpclib import ServerProxy

__docformat__ = 'reStructuredText en'
__all__ = ['TractorApi',
           'Tractor',
           'DummyTractor']


class TractorApi(object):

    def __init__(self, realm, username, password):
        self._realm = realm
        self._username = username
        self._password = password
        self._connection = None

    def _get_connection(self):
        """
        Returns a :class:`ServerProxy` object.
        """
        raise NotImplementedError('Abstract method.')

    def send_request(self, method_name, args):
        """
        Submits the request.
        """
        conn = self._get_connection()
        meth = conn
        for item in method_name.split('.'):
            meth = getattr(meth, item)
        return meth(*args)

    def create_ticket(self, ticket_wrapper, notify=True):
        """
        Creates a new ticket.

        :param ticket_wrapper: The wrapper for the ticket to be generated
            (without ticket ID).
        :type ticket_wrapper: :class:`tractor.ticket.TicketWrapper`

        :param notify: Shall the reporter receive an email notification?
        :type notify: :class:`bool`
        :default notify: *True*

        :return: The ID of the new ticket.
        """
        attributes = ticket_wrapper.get_value_map_for_ticket_creation()

        meth_name = 'ticket.create'
        args = (ticket_wrapper.summary, ticket_wrapper.description, attributes,
                notify)
        ticket_id = self.send_request(method_name=meth_name, args=args)

        return ticket_id

    def get_ticket(self, ticket_id):
        """
        Returns the ticket with the desired ID.
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')

        meth_name = 'ticket.get'
        args = (ticket_id,)
        ticket_data = self.send_request(method_name=meth_name, args=args)

        return TicketWrapper.create_from_trac_data(ticket_data)

    def update_ticket(self, ticket_wrapper, comment=None, notify=True):
        """
        Updates the ticket with the given ID.

        At this, the ticket will only update the attributes that have been
        set in the ticket wrapper. The wrapper may thus be incomplete.

        :param comment: If you do not specify a comment, the method will sent
            a default comment instead.

        :param notify: Shall the reporter, owner and cc receive an email
            notification?
        :type notify: :class:`bool`
        :default notify: *True*

        :return: The updated ticket.
        """
        if ticket_wrapper.ticket_id is None:
            raise ValueError('The ticket ID in the wrapper must not be None!')

        if comment is None:
            comment = 'Automated ticket update via Tractor.'
        attributes = ticket_wrapper.get_value_map_for_update()

        meth_name = 'ticket.update'
        args = (ticket_wrapper.ticket_id, comment, attributes, notify)
        ticket_data = self.send_request(method_name=meth_name, args=args)

        return TicketWrapper.create_from_trac_data(ticket_data)

    def assign_ticket(self, ticket_id, username, comment=None, notify=True):
        """
        Assigns a ticket to the passed user.

        :param comment: If you do not specify a comment, the method will sent
            a default comment instead.

        :param notify: Shall the reporter, owner and cc receive an email
            notification?
        :type notify: :class:`bool`
        :default notify: *True*

        :return: The updated ticket.
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')

        if comment is None:
            comment = 'Automated ticket assignment via Tractor.'
        attributes = {OwnerAttribute.NAME : username}

        meth_name = 'ticket.update'
        args = (ticket_id, comment, attributes, notify)
        ticket_data = self.send_request(method_name=meth_name, args=args)

        return TicketWrapper.create_from_trac_data(ticket_data)

    def close_ticket(self, ticket_id, resolution, comment=None, notify=True):
        """
        Closes the ticket.

        :param comment: If you do not specify a comment, the method will sent
            a default comment instead.

        :param notify: Shall the reporter, owner and cc receive an email
            notification?
        :type notify: :class:`bool`
        :default notify: *True*

        :return: The updated ticket.
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')

        if comment is None:
            comment = 'Automated ticket closing via Tractor.'

        ticket_wrapper = TicketWrapper(ticket_id=ticket_id,
                                       resolution=resolution,
                                       status=STATUS_ATTRIBUTE_VALUES.CLOSED)
        attributes = ticket_wrapper.get_value_map_for_update()

        meth_name = 'ticket.update'
        args = (ticket_id, comment, attributes, notify)
        ticket_data = self.send_request(method_name=meth_name, args=args)

        return TicketWrapper.create_from_trac_data(ticket_data)

    def delete_ticket(self, ticket_id):
        """
        Deletes the ticket with the given ID.

        :return: a boolean indicating success (True) or failure (False)
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')

        meth_name = 'ticket.delete'
        args = (ticket_id,)
        success = self.send_request(method_name=meth_name, args=args)

        if success == 0:
            return True
        else:
            return False

    def add_attachment(self, ticket_id, attachment, replace_existing=True):
        """
        Adds (or overwrites) an ticket attachment. The content of the attachment
        can be a string, a stream or file map. In case of a file map, the
        attachment will be converted into a zip archive, first. If you do not
        want the files to be converted into a zip file, call the method
        separately for each single file.

        :param attachment: :attr:`file_name`, :attr:`content` and
            :attr:`description` of the attachment must be set.

        :param replace_existing: Existing files with the same file names will be
            overwritten, if this is set to *True*. If overwriting is disabled,
            the Trac will extend the file name by a version number.
        :type replace_existing: :class:`bool`
        :default replace_existing: *True*

        :return: The file name of the attachment.
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')

        base64_data = attachment.get_base64_data_for_upload()

        meth_name = 'ticket.putAttachment'
        args = (ticket_id, attachment.file_name, attachment.description,
                base64_data, replace_existing)
        trac_file_name = self.send_request(method_name=meth_name, args=args)

        return trac_file_name

    def get_attachment(self, ticket_id, file_name):
        """
        Returns the content of the requested attachment as Binary -
        use the :class:`tractor.attachment.Base64Converter` to decode it.
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')
        if file_name is None:
            raise ValueError('The attachment file name must not be None.')

        meth_name = 'ticket.getAttachment'
        args = (ticket_id, file_name)
        binary_content = self.send_request(method_name=meth_name, args=args)

        return binary_content

    def get_all_ticket_attachments(self, ticket_id, fetch_content=False):
        """
        Returns information about all attachment of the given ticket.

        :param fetch_content: If set to *False* the returned list will
            only contain information about the attachments but not
            their content. Enabling content fetches requires several
            trac request and might hence increase the processing time and
            the transaction load.
        :type fetch_content: :class:`bool`
        :default fetch_content: *False*
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')

        meth_name = 'ticket.listAttachments'
        args = (ticket_id,)
        att_list = self.send_request(method_name=meth_name, args=args)

        attachments = []
        for att_data in att_list:
            att = AttachmentWrapper.create_from_trac_data(att_data)
            if fetch_content:
                content = self.get_attachment(ticket_id, att.file_name)
                att.content = content
            attachments.append(att)

        return attachments

    def delete_attachment(self, ticket_id, file_name):
        """
        Deletes the specified attachment.

        :return: a boolean indicating success (True) or failure (False)
        """
        if ticket_id is None:
            raise ValueError('The ticket ID must not be None!')
        if file_name is None:
            raise ValueError('The attachment file name must not be None.')

        meth_name = 'ticket.deleteAttachment'
        args = (ticket_id, file_name)
        success = self.send_request(method_name=meth_name, args=args)

        return success


class Tractor(TractorApi):

    def _get_connection(self):
        """
        Returns a :class:`ServerProxy` object.
        """
        if self._connection is None:
            url = 'http://%s:%s@%s' % (self._username, self._password,
                                       self._realm)
            self._connection = ServerProxy(url)
        return self._connection


class DummyTractor(TractorApi):

    def _get_connection(self):
        """
        Returns a dummy connection that acts like a real connection.
        """
        is_valid_connection = False
        get_only = True
        url = 'http://%s:%s@%s' % (self._username, self._password,
                                   self._realm)

        if not self._realm == INVALID_REALM and \
                                not self._username == INVALID_USER:
            is_valid_connection = True

        if not self._username == GET_ONLY_USER:
            get_only = False

        return DummyConnection(get_only=get_only,
                               is_valid_connection=is_valid_connection,
                               url=url)
