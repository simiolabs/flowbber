# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2018 KuraLabs S.R.L
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

Google Test
===========

This source parses the JUnit like results XML file generated by
`Google Test <https://github.com/google/googletest>`_.


**Data collected:**

.. code-block:: json

    {
        "failures": 1,
        "disabled": 1,
        "errors": 1,
        "tests": 1,
        "time": 10.555,
        "timestamp": "2017-09-13T00:51:51",
        "properties": {
            "<propname1>": "<propvalue1>"
        },
        "suites": {
            "<suitename1>": {
                "cases": {
                    "<casename1>": {
                        "status": "<PASS|FAIL|SKIP>",
                        "time": 0.05,
                        "properties": {
                            "<propname1>": "<propvalue1>"
                        }
                    },
                    "<casename2>": {
                        "status": "<PASS|FAIL|SKIP>",
                        "time": 0.05,
                        "properties": {
                            "<propname1>": "<propvalue1>"
                        }
                    }
                },
                "properties": {
                    "<propname1>": "<propvalue1>"
                },
                "failures": 1,
                "passed": 1,
                "disabled": 1,
                "errors": 1,
                "tests": 1,
                "time": 0.456
            }
        }
    }

In addition to the previous data structure, if status is ``FAIL`` an additional
key ``failures`` will be available with a list of failures found:

.. code-block:: python3

    {
        # ...
        'failures': [
            '/home/kuralabs/googletest-example/tests/test2.cpp:12\\n'
            'Expected: 0\\n'
            'To be equal to: 1',
        ]
    }


**Dependencies:**

.. code-block:: sh

    pip3 install flowbber[gtest]

**Usage:**

.. code-block:: toml

    [[sources]]
    type = "gtest"
    id = "..."

        [sources.config]
        xmlpath = "tests.xml"

.. code-block:: json

    {
        "sources": [
            {
                "type": "gtest",
                "id": "...",
                "config": {
                    "xmlpath": "tests.xml"
                }
            }
        ]
    }

xmlpath
-------

Path to the JUnit like XML results ``tests.xml`` file to be parsed.

- **Default**: ``N/A``
- **Optional**: ``False``
- **Schema**:

  .. code-block:: python3

     {
         'type': 'string',
         'empty': False,
     }

- **Secret**: ``False``

"""  # noqa

from pathlib import Path
from xml.etree import ElementTree
from collections import OrderedDict

from flowbber.components import Source


def trycast(value):
    """
    Try to cast a string attribute from an XML tag to an integer, then to a
    float. If both fails, return the original string.
    """
    for cast in (int, float):
        try:
            return cast(value)
        except ValueError:
            continue
    return value


def element_to_dict(element, spec):
    """
    Transform a XML element into a dictionary with its properties identified.
    """
    name = element.attrib.pop('name')

    data = {
        key: cast(element.attrib[key])
        for key, cast in spec
    }

    properties = set(element.attrib) - set(data)

    if properties:
        data.update({
            'properties': {
                key: trycast(value)
                for key, value in element.attrib.items()
                if key in properties
            }
        })

    return name, data


class GTestSource(Source):

    def declare_config(self, config):
        config.add_option(
            'xmlpath',
            schema={
                'type': 'string',
                'empty': False,
            },
        )

    def collect(self):
        # Check if file exists
        infile = Path(self.config.xmlpath.value)
        if not infile.is_file():
            raise FileNotFoundError(
                'No such file {}'.format(infile)
            )

        tree = ElementTree.parse(str(infile))
        root = tree.getroot()
        assert root.tag == 'testsuites', 'Malformed XML root element'

        # Create top level suites object
        _, data = element_to_dict(root, [
            ('tests', int),
            ('failures', int),
            ('disabled', int),
            ('errors', int),
            ('timestamp', str),
            ('time', float),
        ])
        data['passed'] = 0

        testsuites = OrderedDict()
        data['suites'] = testsuites

        # Add test suites
        for child in root:
            assert child.tag == 'testsuite', \
                'Malformed XML child element'

            suitename, testsuite = element_to_dict(child, [
                ('tests', int),
                ('failures', int),
                ('disabled', int),
                ('errors', int),
                ('time', float),
            ])

            testsuites[suitename] = testsuite

            testcases = OrderedDict()
            testsuite['cases'] = testcases

            # Count passed
            testsuite['passed'] = 0

            # Add test case
            for subchild in child:
                assert subchild.tag == 'testcase', \
                    'Malformed XML subchild element'

                # Pop classname, as it is redundant from testsuite name
                del subchild.attrib['classname']

                casename, testcase = element_to_dict(subchild, [
                    ('status', str),
                    ('time', float),
                ])

                # Fetch properties: the properties are no longer attributes
                # in the testcase. After the release of gtest v1.8.1 they
                # are saved in the format <property name='' value''> inside
                # 'properties' under each testcase.
                testcase.setdefault(
                    'properties', {
                        prop.get('name'): prop.get('value')
                        for caseroot in subchild
                        if 'properties' == caseroot.tag
                        for prop in caseroot.findall('property')
                    }
                )

                # Fetch failures
                failures = [
                    failure.text for failure in subchild
                    if failure.tag == 'failure'
                ]

                # Change the status
                if failures:
                    testcase['failures'] = failures
                    testcase['status'] = 'FAIL'

                elif casename.startswith('DISABLED_'):
                    casename = casename[len('DISABLED_'):]
                    testcase['status'] = 'SKIP'

                else:
                    testcase['status'] = 'PASS'
                    testsuite['passed'] += 1

                testcases[casename] = testcase

            data['passed'] += testsuite['passed']

        return data


__all__ = ['GTestSource']
