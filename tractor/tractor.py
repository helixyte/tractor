"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

import attachment
import factory
import ticket

__docformat__ = 'reStructuredText en'

__all__ = ['make_api',
           'make_api_from_config',
           'TicketWrapper',
           'AttachmentWrapper',
           'Base64Converter',
           'create_wrapper_for_ticket_creation']


make_api = factory.make_api
make_api_from_config = factory.make_api_from_config

TicketWrapper = ticket.TicketWrapper
AttachmentWrapper = attachment.AttachmentWrapper
Base64Converter = attachment.Base64Converter


def create_wrapper_for_ticket_creation(summary, description, **kw):
    """
    You can use this method to create a ticket wrapper that contains
    all data required for a trac ticket creation.

    The following keywords are optional:

        * cc
        * component
        * keywords
        * milestone
        * owner
        * priority
        * reporter
        * resolution
        * severity
        * status
        * type
        * version
    """
    return TicketWrapper(summary=summary,
                  description=description,
                  **kw)

def create_wrapper_for_ticket_update(ticket_id, **kw):
    """
    You can use this method to create a ticket wrapper that contains
    all data required for a trac ticket update.

    The following keywords are optional:

        * cc
        * component
        * description
        * keywords
        * milestone
        * owner
        * priority
        * reporter
        * resolution
        * severity
        * status
        * summary
        * type
        * version
    """
    return TicketWrapper(ticket_id=ticket_id, **kw)
