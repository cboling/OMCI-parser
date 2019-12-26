#
# Copyright (c) 2019 - present.  Boling Consulting Solutions (bcsw.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import yaml
from collections import OrderedDict


def represent_dictionary_order(self, dict_data):
    return self.represent_mapping('tag:yaml.org,2002:map', dict_data.items())


def setup_yaml():
    yaml.add_representer(OrderedDict, represent_dictionary_order)


class MetadataYAML(object):
    def __init__(self):
        self._class_ids = dict()

    def add_class(self, cid, name):
        if cid not in self._class_ids:
            self._class_ids[cid] = dict()

        if 'attributes' not in self._class_ids[cid]:
            self._class_ids[cid]['attributes'] = dict()

        self._class_ids[cid]['name'] = name

    def add_attribute(self, cid, index, attr_name, attr_type, attr_default, attr_constraint):
        assert cid in self._class_ids, 'Class {} not defined'.format(cid)
        attributes = self._class_ids[cid]['attributes']

        if index not in attributes:
            attributes[index] = {
                'index': index,
                'name': attr_name,
                'type': attr_type,
                'default': attr_default,
                'constraint': attr_constraint,
            }
        else:
            attribute = attributes[index]
            attribute['index'] = attribute.get('index', index)
            attribute['name'] = attribute.get('name', attr_name)
            attribute['type'] = attribute.get('type', attr_type)
            attribute['default'] = attribute.get('default', attr_default)
            attribute['constraint'] = attribute.get('constraint', attr_constraint)

    def save(self, filepath):
        try:
            # Load representer for an Ordered Dictionary
            setup_yaml()

            # Get class IDs in order
            class_ids = [k for k in self._class_ids.keys()]
            class_ids = sorted(class_ids)
            entries = list()
            for cid in class_ids:
                attributes = list()
                indexes = self._class_ids[cid]['attributes'].keys()
                indexes = sorted(indexes)
                for index in indexes:
                    attr = self._class_ids[cid]['attributes'][index]
                    value = OrderedDict([
                        ('index', attr['index']),
                        ('name', attr['name']),
                        ('type', attr['type'].name),
                        ('default', attr['default']),
                        ('constraint', attr['constraint'])
                    ])
                    attributes.append(value)

                entry = OrderedDict([
                    ('class_id', cid),
                    ('name', self._class_ids[cid]['name']),
                    ('attributes', attributes)
                ])
                entries.append(entry)

            output = {'managed_entities': entries}
            with open(filepath, 'w') as yaml_fd:
                yaml.dump(output, yaml_fd)

            with open(filepath, 'r') as original:
                data = original.read()

            with open(filepath, 'w') as modified:
                # YAML header/comments
                modified.write(self._yaml_header)
                modified.write(data)

        except Exception as _e:
            raise

    def load(self, filepath):
        try:
            from attributes import AttributeType
            with open(filepath, 'r') as fd:
                data = yaml.full_load(fd)
                metadata = data.get('managed_entities', dict())
                #
                # Meta Data is a list of simplified class data
                #
                if metadata is not None:
                    assert isinstance(metadata, list), 'Unexpected Format'
                    for item in metadata:
                        self._class_ids[item['class_id']] = {
                            'name': item['name'],
                            'attributes': dict(),
                        }
                        attributes = self._class_ids[item['class_id']]['attributes']
                        for attr in item['attributes']:
                            attr['type'] = AttributeType[attr.get('type', 'Unknown')]
                            attributes[attr['index']] = attr

        except Exception as _e:
            raise

    _yaml_header = """###############################################################################
#
# Copyright (c) 2019 - present.  Boling Consulting Solutions (bcsw.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
#
# G.988 Augmented Configuration File
#
#  The OMCI Parser is capable of parsing many Managed Entity attributes without too
#  much external support, but for a complete definition, the following areas of
#  parsing need some manual assistance:
#
#   o Attribute Type The parser can detect the basic type of attribute for most Managed
#                    Entities but a few may need a finer definition. See the 'Types'
#                    discussion below for more information.
#
#   o Default Value  The default value is used by all but read-by-create attributes
#                    to specify a default. For integer related values, this is a
#                    straightforward process. For octet-strings, the Base-64 value
#                    is provided. Note that some items (Vendor ID, Serial Number, ...)
#                    attributes will need to be further specified by the user of this
#                    library in order to specify a better default.
#
#    o Constraints   The constraints for write and read-by-create attributes allows the
#                    code generator to produce code that can check whether or not a
#                    value being assigned to a variable is valid. See the 'Constraint'
#                    section below for more information. These constraints are specific
#                    keywords/values that are type specific. A code generator has the
#                    responsibility for generating the constraint checker code that is
#                    appropriate for the giving programming language
#
#  This file can be specified during the second stage of parsing such that the final
#  fully parsed JSON (used by the code generator) is more complete.
#
#  Types:
#    Default Types:  These are assigned by the initial parser:
#      Octets           A series of zero or more 8-bit values that are not an integral 1, 2,
#                       4, or 8 bytes in length
#      UnsignedInteger  8-, 16-, 32-, and 64-bit unsigned values
#      Table            A table row (of Octets)
#
#    Custom Types:  These are specified in the metadata section below as appropriate:
#      String         Readable String
#      SignedInteger  Signed integer, often expressed as 2's complement
#      Pointer        Pointer to an instance of another Managed Entity
#      BitField       Bit field
#      Enumeration    Fixed number of values (Unsigned Integers)
#
#  Constraints:
#    If an attribute has a blank/missing constraint, all values are valid. For ONU read-only
#    values (registers, status, counter, computed, ...) there are no constraints since the ONU
#    sets these as needed.
#
#    Default Types:  Constraint definitions for default types are provided
#      Octets           len(<values>)[,<allowed-pattern>][,fill:<value>]
#      UnsignedInteger  <values>
#      Table            - see Octets above -
#
#    Custom Types:   These are specified in the metadata section below as appropriate:
#      String          len(<values>)[,re:<allowed-pattern>][,fill:<value>]
#      SignedInteger   <values>
#      Pointer         <16-bit values>
#      BitField        <bitmask>
#      Enumeration     <values>
#
#    where:
#
#     len()    is a function that checks a string/octets for a specific length and the
#              result should match one of the <values>
#
#     re:<allowed-pattern> is an optional regular expression that will check the values of
#                          the collection of octets.
#
#     fill:<value>  is an optional fill value to add to the end of a supplied string so that
#                   the entire string length is set to the maximum allowed. Typically this is
#                   either an ASCII space (0x20) or a null (0x00).
#
#     <values> is a pattern of one or more numbers as indicated below.
#              <value>                   a single numerical value
#              <min-value>..<max-value>  a range of values with the min/max spexified
#
#              Multiple value fields can be specified and are separated by commas
#              such as:      2, 4..16, 255
#
#     <bitmask>  is a numerical (often hexadecimal) value that specifies the valid bits
#                allowed for the bitmask
#
###############################################################################
# The Managed Entity data (arranged by Class ID)
#
"""