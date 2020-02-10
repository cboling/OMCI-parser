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

#
#  This application takes a newly parsed G.988 JSON file, a new-or-existing Augment YAML
#  file and combines the G.988 JSON with the Augmented YAML to produce an output Augment
#  YAML file.
#
#  So the process from scratch is:
#
#   1. Pre-parse the G.988 Word Document via 'preParse.py' to create the 'G.988.Precompiled.json' file
#
#   2. Parse the G.988 JSON via 'parser.py' to create the G.988.Parsed.json file.  At this point,
#      there is just a minimal fragment 'G.988.augment.yaml' file that really as a little bit of data
#
#   3. Run the 'augmentGenerator.py' file to create an 'augmented.yaml' file in the 'metadata' sub-
#      directory. This will have all the newly parsed JSON converted to YAML form.
#
#   4. Hand edit the augmented.yaml file by hand and adjust the values as needed.  Once you are done,
#      overwrite the base directory's 'G.988.augment.yaml' file with this.  You now have a
#      metadata file that will be used everytime you either run the parser (or code generator) with
#      you updated metadata.
#
#   5. Run the 'parser.py' program again. This will pick up the metadata hint you created in step 4
#      and will create an updated 'G.988.Parsed.json' file with your data.
#
#   6. Run either the C or Go code generator to generate your classes.
#
############################################################################
#
#   If the pre-parser is upgraded or a bug is fixed and needs to be ran again due to updates, run steps 1-6
#
#   If the parser is upgraded or a bug is fixed, you only need to run steps 5 & 6
#
#   If the code generator you are interested in is upgraded or fixed, you only need to run step 6
#
############################################################################

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
