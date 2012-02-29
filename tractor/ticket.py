"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""

__docformat__ = 'reStructuredText en'
__all__ = ['create_wrapper_for_ticket_creation',
           'create_wrapper_for_ticket_update',
           'TicketWrapper'
           'TicketAttribute',
           'TicketAttributeValues',
           'SummaryAttribute',
           'ReporterAttribute',
           'OwnerAttribute',
           'DescriptionAttribute',
           'TypeAttribute',
           'StatusAttribute',
           'PriorityAttribute',
           'MilestoneAttribute',
           'ComponentAttribute',
           'VersionAttribute',
           'SeverityAttribute',
           'ResolutionAttribute',
           'KeywordsAttribute',
           'CcAttribute',
           'ATTRIBUTE_NAMES',
           'ATTRIBUTE_OPTIONS']


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


class TicketWrapper(object):
    """
    Convenience class for ticket data.
    """

    def __init__(self, ticket_id=None,
                 summary=None,
                 description=None,
                 reporter=None,
                 owner=None,
                 cc=None,
                 type=None, #pylint: disable=W0622
                 status=None,
                 priority=None,
                 milestone=None,
                 component=None,
                 severity=None,
                 resolution=None,
                 version=None,
                 keywords=None,
                 time=None,
                 changetime=None,
                 attribute_names_lookup=None,
                 attribute_options_lookup=None):
        """
        Constructor for ticket wrappers. All arguments are optional.

        However, if you are going to create a new trac ticket for the trac, you
        must at least pass the following arguments:

            * summary
            * description

        If you are going to update an existing trac ticket, you have to pass
        at least the ticket ID.

        :param attribute_names_lookup and attribute_options_lookup:
            These lookup serve the association of attribute names with
            attribute classes and valid option classes. If you do not
            specify a lookup, the ticket object will use the default
            lookups (ATTRIBUTE_NAMES and ATTRIBUTE_OPTIONS) instead.
        """

        self.ticket_id = ticket_id

        self.summary = summary
        self.description = description

        self.reporter = reporter
        self.owner = owner
        self.cc = cc

        self.type = type
        self.status = status
        self.priority = priority
        self.severity = severity
        self.resolution = resolution

        self.milestone = milestone
        self.component = component
        self.keywords = keywords

        self.version = version
        self.time = time
        self.changetime = changetime

        if attribute_names_lookup is None:
            attribute_names_lookup = ATTRIBUTE_NAMES
        #: Used to find the ticket attribute classes for attribute names.
        self.__attribute_names_lookup = attribute_names_lookup

        if attribute_options_lookup is None:
            attribute_options_lookup = ATTRIBUTE_OPTIONS
        #: Used to find valid options for attributes with limited value ranges.
        self.__attribute_options_lookup = attribute_options_lookup

    @classmethod
    def create_from_trac_data(cls, trac_ticket_data):
        """
        Converts the trac ticket return value into a :class:`TicketWrapper` object.
        """
        ticket = TicketWrapper(ticket_id=trac_ticket_data[0],
                        time=trac_ticket_data[1],
                        changetime=trac_ticket_data[2])

        for attr_name, attr_value in trac_ticket_data[3].iteritems():
            if attr_value == '':
                attr_value = None
            setattr(ticket, attr_name, attr_value)

        return ticket

    def check_attribute_validity(self, attribute_name, value=None):
        """
        Checks whether a non-optional attribute is present and
        whether each value is a valid option (used before ticket creation
        and update).

        :raises AttributeError: In case of invalid attribute name.
        :raises ValueError: In case of an invalid value.
        """
        if value is None:
            value = getattr(self, attribute_name)
        attr_cls = self.__attribute_names_lookup[attribute_name]
        options = self.__attribute_options_lookup[attribute_name]

        if value is None:
            if not attr_cls.IS_OPTIONAL:
                if options is None:
                    msg = 'The value for a %s attribute must not be None!' \
                           % (attribute_name)
                    raise ValueError(msg)
                elif not value in options.ALL:
                    msg = 'Invalid value "%s" for attribute %s. Valid ' \
                          'options are: %s.' % (value, attribute_name,
                                                options.ALL)
                    raise ValueError(msg)

        else:
            if not options is None and not value in options.ALL:
                msg = 'Invalid value "%s" for attribute %s. Valid options ' \
                      'are: %s.' % (value, attribute_name, options.ALL)
                raise ValueError(msg)

    def get_value_map_for_ticket_creation(self):
        """
        Returns a value map for ticket creation - non-optional attribute
        with None value will be set to their DEFAULT_VALUE.
        """
        value_map = dict()

        for attr_name, attr_cls in self.__attribute_names_lookup.iteritems():
            value = getattr(self, attr_name)

            # Summary and description must be passed as extra arguments.
            if attr_name == SummaryAttribute.NAME or \
                                    attr_name == DescriptionAttribute.NAME:
                self.check_attribute_validity(attr_name)
                continue

            if value is None:
                if attr_cls.IS_OPTIONAL:
                    continue
                else:
                    value = attr_cls.DEFAULT_VALUE

            self.check_attribute_validity(attr_name, value)
            if not value is None:
                value_map[attr_name] = value

        return value_map

    def get_value_map_for_update(self):
        """
        Returns a value map containing the value for all set attributes.
        """
        value_map = dict()
        for attr_name in self.__attribute_names_lookup.keys():
            value = getattr(self, attr_name)
            if not value is None:
                self.check_attribute_validity(attr_name, value)
                value_map[attr_name] = value

        return value_map

    def __eq__(self, other):
        """
        Within one realm, tickets are equal if their ID is equal.
        """
        return isinstance(other, self.__class__) and \
                self.ticket_id == other.ticket_id

    def __ne__(self, other):
        """
        Within one realm, tickets are unequal if they have different IDs.
        """
        return not (self.__eq__(other))

    def __str__(self):
        return '%s' % (self.ticket_id)

    def __repr__(self):
        str_format = '<%s, id:%s, summary: %s>'
        params = (self.__class__.__name__, self.ticket_id, self.summary)
        return str_format % params


class TicketAttribute(object):
    """
    A superclass for ticket attributes
    """

    #: The name of the attribute.
    NAME = None
    #: The default value for the attribute.
    DEFAULT_VALUE = None
    #: Indicates whether the value must be set or whether it may be *None*.
    IS_OPTIONAL = False

    def __init__(self, value=None):
        """
        Constructor:

        :param value: The value for the attribute. If the value is *None*,
            the constructor will assign the attributes :attr:`DEFAULT_VALUE`.
        :type value: :class:`basestring`
        :default value: *None*
        """

        #: The value of the attribute.
        self.value = value
        if value is None:
            self.value = self.DEFAULT_VALUE

    @classmethod
    def create_by_name(cls, attribute_name, value, attribute_name_lookup=None):
        """
        Creates a ticket attribute object of the selected type.

        :param attribute_name_lookupibute_map: If you do not pass an lookup
            the method will use the default lookup instead. The lookup is
            used to find the class for the passed attribute name.
        """

        if attribute_name_lookup is None:
            attribute_name_lookup = ATTRIBUTE_NAMES

        attr_cls = attribute_name_lookup[attribute_name]
        return attr_cls(value=value)

    def __str__(self):
        return '%s:%s' % (self.NAME, self.value)

    def __repr__(self):
        str_format = '<%s, value: %s>'
        params = (self.__class__.__name__, self.value)
        return str_format % params


class TicketAttributeValues(object):
    """
    The subclasses of this abstract class collect valid options for particular
    ticket attribute types. The collections are registered in the the
    ATTRIBUTE_OPTIONS lookup. If you prefer other values you can overwrite
    the classes and the lookup.
    """
    ALL = None


class SummaryAttribute(TicketAttribute):
    """
    The summary is the ticket title.
    """
    NAME = 'summary'


class ReporterAttribute(TicketAttribute):
    """
    The reporter is the user who has created the ticket.
    """
    NAME = 'reporter'
    IS_OPTIONAL = True
    # The trac sets the username of the login as default.


class OwnerAttribute(TicketAttribute):
    """
    The owner is of the ticket.
    """
    NAME = 'owner'
    IS_OPTIONAL = True
    # The trac sets the username of the login as default.


class DescriptionAttribute(TicketAttribute):
    """
    The (extensive) description of the ticket (as opposed to the summary).
    """
    NAME = 'description'


class TYPE_ATTRIBUTE_VALUES(object):
    DEFECT = 'defect'
    ENHANCEMENT = 'enhancement'
    TASK = 'task'
    ALL = [DEFECT, ENHANCEMENT, TASK]

class TypeAttribute(TicketAttribute):
    """
    The type of the ticket.
    """
    NAME = 'type'
    DEFAULT_VALUE = TYPE_ATTRIBUTE_VALUES.TASK


class STATUS_ATTRIBUTE_VALUES(object):
    ASSIGNED = 'assigned'
    CLOSED = 'closed'
    NEW = 'new'
    REOPENED = 'reopened'
    ALL = [ASSIGNED, CLOSED, NEW, REOPENED]

class StatusAttribute(TicketAttribute):
    """
    Indicates the status of the ticket.
    """
    NAME = 'status'
    DEFAULT_VALUE = STATUS_ATTRIBUTE_VALUES.NEW
    IS_OPTIONAL = True


class PRIORITY_ATTRIBUTE_VALUES(object):
    HIGHEST = 'highest'
    HIGH = 'high'
    NORMAL = 'normal'
    LOW = 'low'
    LOWEST = 'lowest'
    ALL = [HIGHEST, HIGH, NORMAL, LOW, LOWEST]

class PriorityAttribute(TicketAttribute):
    """
    Indicates the priority of the ticket.
    """
    NAME = 'priority'
    DEFAULT_VALUE = PRIORITY_ATTRIBUTE_VALUES.NORMAL


class MilestoneAttribute(object):
    """
    This is the milestone for the ticket. In theory there should a dictionary
    with options, but this would be a rather huge list and it is unlikely
    to be used anyway.
    """
    NAME = 'milestone'
    IS_OPTIONAL = True


class ComponentAttribute(TicketAttribute):
    """
    This is the component the ticket is related to.
    """
    NAME = 'component'
    DEFAULT_VALUE = 'Other'


class VersionAttribute(TicketAttribute):
    """
    This attribute relates to the component's version.
    In theory there should a dictionary with options, but this would be a
    rather huge list and it is unlikely to be used anyway.
    """
    NAME = 'version'
    IS_OPTIONAL = True


class SEVERITY_ATTRIBUTE_VALUES(object):
    BLOCKER = 'blocker'
    CRITICAL = 'critical'
    MAJOR = 'major'
    NORMAL = 'normal'
    MINOR = 'minor'
    TRIVIAL = 'trivial'
    ALL = [BLOCKER, CRITICAL, MAJOR, NORMAL, MINOR, TRIVIAL]


class SeverityAttribute(TicketAttribute):
    """
    This attributes indicates the severity of the action requested in the
    ticket.
    """
    NAME = 'severity'
    DEFAULT_VALUE = SEVERITY_ATTRIBUTE_VALUES.NORMAL


class RESOLUTION_ATTRIBUTE_VALUES(object):
    FIXED = 'fixed'
    INVALID = 'invalid'
    WONTFIX = 'wontfix'
    DUPLICATE = 'duplicate'
    WORKSFORME = 'worksforme'
    NONE = None
    ALL = [FIXED, INVALID, WONTFIX, DUPLICATE, WORKSFORME, NONE]

class ResolutionAttribute(TicketAttribute):
    """
    This value is selected when you close a ticket.
    """
    NAME = 'resolution'
    OPTIONS = RESOLUTION_ATTRIBUTE_VALUES.ALL


class KeywordsAttribute(TicketAttribute):
    """
    These are keywords for ticket queries.
    """
    NAME = 'keywords'
    IS_OPTIONAL = True

class CcAttribute(TicketAttribute):
    """
    This is a list of users that shall be kept informed about the ticket
    (in addition to owner and reporter).
    """
    NAME = 'cc'
    IS_OPTIONAL = True


#: Map attribute classes onto NAMES of ticket attributes classes.
ATTRIBUTE_NAMES = \
       {SummaryAttribute.NAME : SummaryAttribute,
        ReporterAttribute.NAME: ReporterAttribute,
        OwnerAttribute.NAME : OwnerAttribute,
        DescriptionAttribute.NAME : DescriptionAttribute,
        TypeAttribute.NAME : TypeAttribute,
        StatusAttribute.NAME : StatusAttribute,
        PriorityAttribute.NAME : PriorityAttribute,
        MilestoneAttribute.NAME : MilestoneAttribute,
        ComponentAttribute.NAME : ComponentAttribute,
        VersionAttribute.NAME : VersionAttribute,
        SeverityAttribute.NAME : SeverityAttribute,
        ResolutionAttribute.NAME : ResolutionAttribute,
        KeywordsAttribute.NAME : KeywordsAttribute,
        CcAttribute.NAME : CcAttribute
        }

#: Maps valid attribute lists onto NAMES of ticket attributes classes.
ATTRIBUTE_OPTIONS = \
    {SummaryAttribute.NAME : None,
     ReporterAttribute.NAME : None,
     OwnerAttribute.NAME : None,
     DescriptionAttribute.NAME : None,
     TypeAttribute.NAME : TYPE_ATTRIBUTE_VALUES,
     StatusAttribute.NAME : STATUS_ATTRIBUTE_VALUES,
     PriorityAttribute.NAME : PRIORITY_ATTRIBUTE_VALUES,
     MilestoneAttribute.NAME : None,
     ComponentAttribute.NAME : None,
     VersionAttribute : None,
     SeverityAttribute.NAME : SEVERITY_ATTRIBUTE_VALUES,
     ResolutionAttribute.NAME : RESOLUTION_ATTRIBUTE_VALUES,
     KeywordsAttribute.NAME : None,
     CcAttribute.NAME : None}

