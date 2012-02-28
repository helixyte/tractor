"""
This file is part of the tractor library.
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jan 06, 2012.
"""
from ConfigParser import ParsingError
from ConfigParser import SafeConfigParser
from StringIO import StringIO
from api import Tractor
from dummy import DummyTractor


__docformat__ = 'reStructuredText en'

__all__ = ['TractorConfig'
           'make_api_from_config',
           'make_api']


class TractorConfig(object):
    """
    Custom config parser for tractor configurations.
    """

    BASE_KEYS = ['realm', 'username', 'password']
    REQUIRED_KEYS = set(BASE_KEYS)
    KEYS = set(BASE_KEYS + ['load_dummy'])

    def __init__(self):
        self.settings = {}
        self.global_settings = {}

    def parse(self, text):
        """
        Parses the given configuration. Asserts that all required keys and
        no invalid keys were specified in the configuration.

        :param text: configuration to parse
        :type text: string or open file
        """
        if not hasattr(text, 'readline'):
            text = StringIO(text)
        ini_parser = SafeConfigParser()
        ini_parser.readfp(text)
        if 'DEFAULT' in ini_parser.sections():
            self.global_settings = dict(ini_parser.items('DEFAULT'))
        if 'tractor' in ini_parser.sections():
            found_req_keys = []
            invalid_keys = []
            for key, value in ini_parser.items('tractor'):
                if not key in self.KEYS:
                    invalid_keys.append(key)
                    continue
                if key in self.REQUIRED_KEYS:
                    found_req_keys.append(key)
                self.settings[key] = value
            #
            if invalid_keys:
                raise ParsingError('Found invalid keys in [tractor] '
                                   'config section: %s' % (invalid_keys,))
            diff = self.REQUIRED_KEYS.difference(found_req_keys)
            if diff:
                raise ParsingError('Not all required keys found in [tractor] '
                                   'config section (found: %s, missing: %s).'
                                    % (found_req_keys, list(diff)))


def make_api_from_config(config_file):
    """
    Creates a config file from the settings defined in a section named
    'tractor' in the given config file.

    :returns: :class:`TractorApi` instance
    """
    try:
        fp = open(config_file, 'r')
    except IOError:
        pass
    cnf = TractorConfig()
    cnf.parse(fp)
    return make_api(**cnf.settings)


def make_api(**settings):
    """
    Creates a new tractor API object from the given settings.

    :returns: :class:`TractorApi` instance
    """
    if settings.has_key('load_dummy'):
        load_dummy = settings['load_dummy']
        del settings['load_dummy']
    else:
        load_dummy = False

    if load_dummy:
        return DummyTractor(**settings)
    else:
        return Tractor(**settings)
