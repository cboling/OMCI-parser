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
    Read = 1
    Write = 2
    SetByCreate = 3

    @staticmethod
    def keywords():
        """ Keywords for searching if text is for Attribute Access """
        return {'r', 'w', 'set-by-create', 'setbycreate'}

    @staticmethod
    def keywords_to_access_set(keywords):
        assert isinstance(keywords, list)
        # assert any(k.lower() in AttributeAccess.keywords() for k in keywords)
        results = set()
        for k in keywords:
            if k.strip() == 'r':
                results.add(AttributeAccess.Read)
            elif k.strip() == 'w':
                results.add(AttributeAccess.Write)
            elif k.strip() [:len('set-by-create')] == 'set-by-create' or k.strip()[:len('setbycreate')] == 'setbycreate':
                results.add(AttributeAccess.SetByCreate)
            else:
                print('Invalid access type: {}'.format(k))

        return results

    @staticmethod
    def load(data):
        access = set()
        for a in data:
            if a.lower() == 'read':
                access.add(AttributeAccess.Read)
            elif a.lower() == 'write':
                access.add(AttributeAccess.Write)
            elif a.lower() == 'setbycreate':
                access.add(AttributeAccess.SetByCreate)
        return access


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

    def remove(self, index):
        del self._attributes[index]

    def to_dict(self):
        return {index: attr.to_dict() for index, attr in enumerate(self._attributes)}

    @staticmethod
    def load(data):
        attr_list = AttributeList()
        key_list = [k for k in data.keys()]
        key_list.sort(key=lambda x: int(x))
        for key in key_list:
            attr_list.add(Attribute.load(data[key]))

        return attr_list


# TODO: Add proper decode for
#       avc
#       tca
#       counter
#       table_support
class Attribute(object):
    def __init__(self):
        self.name = None            # Attribute name (with spaces)
        self.description = []       # Description (text, paragraph numbers & Table objects)
        self.access = set()         # (AttributeAccess) Allowed access
        self.optional = None        # If true, attribute is option, else mandatory
        self.size = None            # (Size) Size object
        self.avc = False            # If true, an AVC notification can occur for the attribute
        self.tca = False            # If true, a threshold crossing alert alarm notification
                                    # can occur for the attribute
        self.counter = False        # Counter attribute
        self.table = None           # (dict) Table information related to attribute
        self.table_support = False  # Supports table operations
        # TODO: Constraints?

    def __str__(self):
        return 'Attribute: {}, Access: {}, Optional: {}, Size: {}, AVC/TCA: {}/{}'.\
            format(self.name, self.access, self.optional, self.size,
                   self.avc, self.tca)

    def to_dict(self):
        # TODO: Save/restore table info?
        return {
            'name': self.name,
            'description': self.description,
            'access': [a.name for a in self.access],
            'optional': self.optional,
            'size': self.size.to_dict(),
            'avc': self.avc,
            'tca': self.tca,
            'counter': self.counter,
            'table-support': self.table_support,
        }

    @staticmethod
    def load(data):
        attr = Attribute()
        attr.name = data.get('name')
        attr.description = data.get('description')
        attr.optional = data.get('optional', False)
        attr.tca = data.get('tca', False)
        attr.avc = data.get('avc', False)
        attr.size = AttributeSize.load(data.get('size'))
        attr.counter = data.get('counter', False)
        attr.access = AttributeAccess.load(data.get('access'))
        attr.table_support = data.get('table-support', False)
        return attr

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
        is_bold = paragraph.runs[0].bold
        style = paragraph.style.name.lower()
        text = paragraph.text.lower()[:20]

        if is_bold and \
                (style not in {'attribute follower', 'attribute list'} or
                 (style == 'attribute follower' and
                  ('aal5 profile pointer' in text or 'deprecated 3' in text))):       # see 9.13.4
            # New attribute
            attribute = Attribute()
            # TODO: Scrub things in '()' from name of attribute
            initial = ascii_only(' '.join(x.text.strip() for x in paragraph.runs
                                          if x.bold)).title()

            attribute.name = ' '.join(x.strip() for x in initial.split(' ')
                                      if len(x.strip()) > 0).title()
            # Some manual cleanups
            fixups = {
                ('N Umber', 'Number'),
                ('C Ounter', 'Counter'),
                ('C Ontrol', 'Control'),
                ('P Ointer', 'Pointer'),
                ('1 St', '1st'),
                ('2 Nd', '2nd'),
                ('3 Rd', '3rd'),
                ('4 Th', '4th'),
                ('/', '_'),
                ('-', '_'),
                ('\+', '_'),
                ('T Cont', 'TCont'),
                ('R Eporting', 'Reporting'),
                ('I Ndication', 'Indication'),
                ('H Ook', 'Hook'),
                ('R Eset', 'Reset'),
                ('I Nterval', 'Interval'),
                ('M Essage', 'Message'),
                ('T Ype', 'Type'),
                ('F Ail', 'Fail'),
                ('P Ayload', 'Payload'),
                ('M Anagement', 'Management'),
                ('Battery B Ackup', 'Battery Backup'),
                ('O Ption', 'Option'),
                ('( S F )', ''),
                ('( Dsl )', ''),
                ('( Arc )', ''),
                ('"', ''),

                # Keep these last
                ('\(\)', ''),
                (' \(', ' '),
                ('\)', ''),
                ('  ', ' '),
                (':', ''),
            }
            for orig, new in fixups:
                attribute.name = re.sub(orig, new, attribute.name)

            attribute.name = attribute.name.strip()
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
            if len(paren_items) < 3:
                return

            for item in paren_items:
                # Mandatory/optional is the easiest
                if item.lower() == 'mandatory':
                    assert self.optional is None or not self.optional, 'Optional flag already decoded'
                    self.optional = False
                    continue

                elif item.lower() == 'optional':
                    assert self.optional is None or self.optional, 'Optional flag already decoded'
                    self.optional = True
                    continue

                # Try to see if the access for the attribute is this item
                access_item = item.replace('-', '').strip()

                # Address type if 9.2.3 Port-ID
                if access_item.lower() == 'rwsc':
                    access_item = 'r, w, set-by-create'

                access_list = access_item.lower().split(',')
                if any(i in AttributeAccess.keywords() for i in access_list):
                    access = AttributeAccess.keywords_to_access_set(access_list)
                    # assert len(self.access) == 0 or all(a in self.access for a in access), \
                    #     'Accessibility has already be decoded'
                    self.access = access
                    continue

                size = AttributeSize.create_from_keywords(item)
                if size is not None:
                    # Take the last 'valid' size item. Some description text for long
                    # byte or bit fields may specify what subsections sizes are and the
                    # total size often will come last
                    if self.size is not None:
                        print('Found additional size info for same attribute {}. Was {}, now {}'.
                              format(self.name, self.size, size))
                    self.size = size

        elif isinstance(content, Table):
            # assert self.table is None, 'Attribute already has a table'
            self.table = content.rows

# TODO: Still need to test/decode AVC flag
# TODO: Still need to test/decode TCA flag
