# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 KuraLabs S.R.L
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Module implementating the Configurator class.
"""

from copy import deepcopy
from logging import getLogger
from collections import OrderedDict, namedtuple


log = getLogger(__name__)


class MissingOptions(AttributeError):
    def __init__(self, keys):
        super().__init__(
            'Missing mandatory configuration options {}'.format(keys)
        )
        self.keys = keys


class UnknownOptions(AttributeError):
    def __init__(self, keys):
        super().__init__(
            'Unknown configuration options {}'.format(keys)
        )
        self.keys = keys


class Configurator:
    """
    FIXME: Document.
    """

    def __init__(self):
        self._declared = OrderedDict()
        self._configitem = namedtuple(
            'configitem',
            ['key', 'value', 'is_secret']
        )
        self._configtype = None

    def add_option(
            self, key,
            default=None, optional=False, type=None, secret=False):
        if not key:
            raise ValueError('Missing configuration key')

        if not isinstance(optional, bool):
            raise ValueError('optional must be a boolean')

        if not isinstance(secret, bool):
            raise ValueError('secret must be a boolean')

        self._declared[key] = {
            'default': default,
            'optional': optional,
            'type': type,
            'secret': secret,
        }

    def validate(self, userconf):
        """
        FIXME: Document.
        """
        # Create configuration type for this declared configuration
        self._configtype = namedtuple('config', self._declared.keys())

        if not self._declared:
            return self._configtype()

        # All mandatory keys are present in user config
        mandatory = {
            key for key, info in self._declared.items()
            if not info['optional']
        }
        available = set(userconf.keys())

        if mandatory - available:
            raise MissingOptions(
                sorted(mandatory - available)
            )

        # Check for unknown configuration options
        declared = set(self._declared.keys())

        if available - declared:
            raise UnknownOptions(
                sorted(available - declared)
            )

        # Check datatypes of the options
        for key, info in self._declared.items():
            # FIXME: Implement type checking
            pass

        validated = deepcopy(userconf)
        validated.update({
            key: info['default']
            for key, info in self._declared.items()
            if key not in available
        })

        # Log configuration
        log_config = []
        for key, info in self._declared.items():
            if info['secret']:
                log_config.append('{} = {}'.format(key, '*' * 30))
                continue
            log_config.append('{} = {}'.format(key, validated[key]))

        log.info('Using configuration:\n    {}'.format(
            '\n    '.join(log_config)
        ))

        # Create inmutable configuration object
        return self._configtype(**{
            key: self._configitem(
                key=key,
                value=value,
                is_secret=self._declared[key]['secret']
            )
            for key, value in validated.items()
        })


__all__ = ['Configurator']
