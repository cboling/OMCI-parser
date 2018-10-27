#
# Copyright (c) 2018 - present.  Boling Consulting Solutions (bcsw.net)
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
import re
from enum import IntEnum
from text import *
from size import AttributeSize
from tables import Table


class AttributeAccess(IntEnum):
    R = 1
    W = 2
    SBC = 3

    @staticmethod
    def keywords():
        """ Keywords for searching if text is for Attribute Access """
        return {'r', 'w', 'set-by-create'}

    @staticmethod
    def keywords_to_access_set(keywords):
        assert isinstance(keywords, list) and len(keywords) > 0
        assert all(k.lower() in AttributeAccess.keywords() for k in keywords)
        results = set()
        for k in keywords:
            if k == 'r':
                results.add(AttributeAccess.R)
            elif k == 'w':
                results.add(AttributeAccess.W)
            elif k == 'set-by-create':
                results.add(AttributeAccess.SBC)
            else:
                raise ValueError('Invalid access type: {}', k)

        return results


class AttributeList(object):
    def __init__(self):
        self._attributes = list()

    def __getitem__(self, item):
        return self._attributes[item]  # delegate to li.__getitem__

    def __iter__(self):
        for attribute in self._attributes:
            yield attribute

    def __len__(self):
        return len(self._attributes)

    def add(self, attribute):
        assert isinstance(attribute, Attribute), 'Invalid type'
        self._attributes.append(attribute)
        return self

    def get(self, index):
        return self._attributes[index]


class Attribute(object):
    def __init__(self):
        self.name = None         # Attribute name (with spaces)
        self.description = []    # Description (text, paragraph numbers & Table objects)
        self.access = None       # (AttributeAccess) Allowed access
        self.optional = None     # If true, attribute is option, else mandatory
        self.size = None         # (Size) Size object
        self.avc = False         # If true, an AVC notification can occur for the attribute
        self.tca = False         # If true, a threshold crossing alert alarm notification
                                 # can occur for the attribute
        self.table = None        # (dict) Table information related to attribute
        # TODO: Constraints?

    def __str__(self):
        return 'Attribute: {}, Access: {}, Optional: {}, Size: {}, AVC/TCA: {}/{}'.\
            format(self.name, self.access, self.optional, self.size,
                   self.avc, self.tca)

    @staticmethod
    def create_from_paragraph(content, paragraph):
        """
        Create an attribute from passed in paragraph information if it refers to a
        new attribute.  If not, this paragraph is for the previously created attribute.

        :param content: (int) Document paragraph number
        :param paragraph: (Paragraph) Docx Paragraph

        :return: (Attribute) new attribute or None if this is additional text
                             for a previous attribute
        """
        attribute = None

        if paragraph.runs[0].bold:
            # New attribute
            attribute = Attribute()
            # TODO: Scrub things in '()' from name of attribute
            attribute.name = ascii_only(' '.join(x.text for x in paragraph.runs
                                                 if x.bold)).title()
            attribute.description.append(content)

        return attribute

    def parse_attribute_settings_from_text(self, content, paragraph):
        # Any content?

        if isinstance(content, int):
            text = ascii_only(paragraph.text).strip()
            if len(text) == 0:
                return

            self.description.append(content)

            # Check for access, mandatory/optional, and size keywords.  These are in side
            # one or more () groups
            paren_items = re.findall('\(([^)]+)*', text)

            for item in paren_items:
                # Mandatory/optional is the easiest
                if item.lower() == 'mandatory':
                    assert self.optional is None, 'Optional flag already decoded'
                    self.optional = False
                    continue

                elif item.lower() == 'optional':
                    assert self.optional is None, 'Optional flag already decoded'
                    self.optional = True
                    continue

                # Try to see if the access for the attribute is this item
                access_item = item.replace('-', '').strip()
                access_list = access_item.lower().split(',')
                if all(i in AttributeAccess.keywords() for i in access_list):
                    access = AttributeAccess.keywords_to_access_set(access_list)
                    assert self.access is None or all(a in self.access for a in access), \
                        'Accessibility has already be decoded'
                    self.access = access
                    continue

                # Finally, is a size thing
                size = AttributeSize.create_from_keywords(item)
                if size is not None:
                    assert self.size is None, 'Size has already been decoded'
                    self.size = size

        elif isinstance(content, Table):
            assert self.table is None, 'Attribute already has a table'
            self.table = content.rows

# TODO: Still need to test/decode AVC flag
# TODO: Still need to test/decode TCA flag
