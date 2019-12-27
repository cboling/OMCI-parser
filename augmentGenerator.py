#!/usr/bin/env python
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
import argparse
import os
import base64
from parsed_json import ParsedJson
from parsed_yaml import MetadataYAML
from attributes import AttributeType

_class_ids_of_interest = [
    2, 5, 6, 7, 11, 24, 45, 46, 47, 48, 49, 51, 52,
    78, 84, 89, 131, 171, 256, 257, 262, 263, 264,
    266, 268, 272, 273, 274, 276, 277, 278, 280, 281,
    287, 296, 309, 310, 311, 312, 321, 322, 329,
    334, 341, 343, 344, 345, 346, 426
]


def parse_args():
    parser = argparse.ArgumentParser(description='G.988 Attribute Augmenter')

    parser.add_argument('--input', '-i', action='store',
                        default='G.988.Parsed.json',
                        help='Input parsed data filename, default: G.988.Parsed.json')

    parser.add_argument('--existing', '-e', action='store',
                        default='G.988.augment.yaml',
                        help='Existing Augment YAML file to append too, default: G.988.augment.yaml')

    parser.add_argument('--dir', '-d', action='store',
                        default='metadata',
                        help='Directory name to place generated YAML files, default: metadata')

    args = parser.parse_args()
    return args


class Main(object):
    """ Main program """
    def __init__(self):
        self.args = parse_args()
        self.paragraphs = None
        self.parsed = ParsedJson()
        self.metadata = MetadataYAML()

    def start(self):
        try:
            # Load any existing Metadata YAML file
            self.metadata.load(self.args.existing)

            # Load JSON class ID
            self.parsed.load(self.args.input)

            # class_ids = [c for c in self.parsed.class_ids.values()]
            # class_ids.sort(key=lambda x: x.cid)

            for cid, item in self.parsed.class_ids.items():
                if cid not in _class_ids_of_interest:
                    continue

                # Add class if not already present
                self.metadata.add_class(cid, item.name)

                # Walk attributes. Attribute features only added if not already present
                for attribute in item.attributes:
                    default_value = self.type_default(attribute.attribute_type, attribute.size)
                    constraint = self.type_constraint(attribute.attribute_type, attribute.size)
                    self.metadata.add_attribute(cid, attribute.index, attribute.name, attribute.attribute_type,
                                                default_value, constraint)

            # Create output directory
            try:
                os.mkdir(self.args.dir)

            except Exception as _e:
                pass

            # Create the output file
            filepath = os.path.join(self.args.dir, "augmented.yaml")
            self.metadata.save(filepath)

        except Exception as _e:
            raise

        # Done
        print('YAML generation completed successfully')

    @staticmethod
    def type_default(attr_type, size):
        if attr_type == AttributeType.Unknown:
            return None

        if attr_type == AttributeType.Octets:
            octets = bytearray(size.octets)            # Zeros
            return base64.b64encode(octets)

        if attr_type == AttributeType.String:
            octets = bytearray(b' ') * size.octets     # Spaces
            return base64.b64encode(octets)

        if attr_type == AttributeType.UnsignedInteger:
            return 0

        if attr_type == AttributeType.Table:
            octets = bytearray(size.octets)            # Zeros
            return base64.b64encode(octets)

        if attr_type == AttributeType.SignedInteger:
            return 0

        if attr_type == AttributeType.Pointer:
            return 0

        if attr_type == AttributeType.BitField:
            return 0

        if attr_type == AttributeType.Enumeration:
            return 0

        if attr_type == AttributeType.Counter:
            return 0

        assert False, 'Not expected'

    @staticmethod
    def type_constraint(attr_type, size):
        if attr_type == AttributeType.Unknown:
            return None

        if attr_type == AttributeType.Octets:
            return 'len({})'.format(size.octets)

        if attr_type == AttributeType.String:
            return 'len({})'.format(size.octets)

        if attr_type == AttributeType.UnsignedInteger:
            return '0..0x{:X}'.format(0xFF if size.octets == 1 else
                                      0xFFFF if size.octets == 2 else
                                      0xFFFFFFFF if size.octets == 4 else
                                      0xFFFFFFFFFFFFFFFF)

        if attr_type == AttributeType.Table:
            octets = bytearray(size.octets)          # Zeros
            return base64.b64encode(octets)

        if attr_type == AttributeType.SignedInteger:
            return 0

        if attr_type == AttributeType.Pointer:
            return '0..0xFFFF'

        if attr_type == AttributeType.BitField:
            return '0x{:X}'.format(0xFF if size.octets == 1 else
                                   0xFFFF if size.octets == 2 else
                                   0xFFFFFFFF if size.octets == 4 else
                                   0xFFFFFFFFFFFFFFFF)

        if attr_type == AttributeType.Enumeration:
            return '0..0x{:X}'.format(0xFF if size.octets == 1 else
                                      0xFFFF if size.octets == 2 else
                                      0xFFFFFFFF if size.octets == 4 else
                                      0xFFFFFFFFFFFFFFFF)

        if attr_type == AttributeType.Counter:
            return None

        assert False, 'Not expected'


if __name__ == '__main__':
    Main().start()
