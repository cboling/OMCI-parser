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

import copy
import re
from enum import IntEnum

from .size import AttributeSize
from .tables import Table
from .text import ascii_only
from errors import RecoverableException


# pylint: disable=anomalous-backslash-in-string


class AttributeType(IntEnum):
    Unknown = 0          # Not known
    Octets = 1           # Series of zero or more octets
    String = 2           # Readable String
    UnsignedInteger = 3  # Integer (0..max)
    Table = 4            # Table (of Octets)
    SignedInteger = 5    # Signed integer, often expressed as 2's complement
    Pointer = 6          # Managed Entity ID or pointer to a Managed instance
    BitField = 7         # Bitfield
    Enumeration = 8      # Fixed number of values (Unsigned Integers)
    Counter = 9          # Incrementing counter


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
            elif k.strip()[:len('set-by-create')] == 'set-by-create' or k.strip()[:len('setbycreate')] == 'setbycreate':
                results.add(AttributeAccess.SetByCreate)
            else:
                print('Invalid access type: {}'.format(k))

        return results

    @staticmethod
    def load(data):
        access = set()
        for acc in data:
            if acc.lower() == 'read':
                access.add(AttributeAccess.Read)
            elif acc.lower() == 'write':
                access.add(AttributeAccess.Write)
            elif acc.lower() == 'setbycreate':
                access.add(AttributeAccess.SetByCreate)
        return access


class AttributeList(object):
    def __init__(self):
        self._attributes = list()

    def __getitem__(self, item):
        return self._attributes[item]  # delegate to li.__getitem__

    def __setitem__(self, key, value):
        # Extend with filler if needed
        while len(self._attributes) <= key:
            self.add(Attribute())
        self._attributes[key] = copy.deepcopy(value)

    def __iter__(self):
        for attribute in self._attributes:
            yield attribute

    def __len__(self):
        return len(self._attributes)

    def add(self, attribute):
        assert isinstance(attribute, Attribute), 'Invalid type'
        if attribute.index is None:
            attribute.index = len(self._attributes)
        self._attributes.append(attribute)
        return self

    def insert(self, index, attribute):
        return self._attributes.insert(index, attribute)

    def get(self, index):
        return self._attributes[index]

    def remove(self, index):
        del self._attributes[index]

    def to_dict(self):
        return {index: attr.to_dict() for index, attr in enumerate(self._attributes)}

    @staticmethod
    def load(data):
        attr_list = AttributeList()
        key_list = list(data.keys())
        key_list.sort(key=lambda x: int(x))     # pylint: disable=unnecessary-lambda
        index = 0
        for key in key_list:
            attr_list.add(Attribute.load(data[key], index))
            index += 1

        return attr_list


# TODO: Add proper decode for
#       tca
#       counter
class Attribute(object):
    def __init__(self):
        self.name = None             # Attribute name (with spaces)
        self.index = None            # Sequence in the attribute list (0..n)
        self.description = []        # Description (text, paragraph numbers & Table objects)
        self.access = set()          # (AttributeAccess) Allowed access
        self.optional = None         # If true, attribute is option, else mandatory
        self.size = None             # (Size) Size object
        self.avc = False             # If true, an AVC notification can occur for the attribute
        self.tca = False             # If true, a threshold crossing alert alarm notification
                                     # can occur for the attribute
        self.deprecated = False      # If true, attribute is deprecated (may still be mandatory)
        self.default = None          # Default value
        self.table = None            # (dict) Table information related to attribute
        self.attribute_type = AttributeType.Unknown

        ###################################################################################
        # Constraints will always be a string (or None) composed of substrings separated
        # by a comma. If no constraint string (None) is specified, the attribute can take on'
        # any value allowed for the type within the limits of the attribute 'size'. The
        # substrings are:
        #   integer           Discrete value that is allowed.  Used for Integers, Pointers,
        #                     Enumerations, an strings. If string, this is the maximum length
        #                     allowed for the string
        #   integer..integer  Range of values allowed. Used for Integers, Pointers, Enumerations,
        #                     and strings. If string, this is the minimum..maximum length of the
        #                     string allowed.
        #   'reg-ex'          Regular expression (strings). Commonly followed by an 'integer' or''
        #                     'integer..integer' field to specify string length limits
        #   :integer:         A bitmask of valid bits. Integer may be in decimal or hexadecimal format
        #
        self.constraint = None

    def __str__(self):
        return 'Attribute: {}, Access: {}, Optional: {}, Size: {}, AVC/TCA: {}/{}'.\
            format(self.name, self.access, self.optional, self.size,
                   self.avc, self.tca)

    @property
    def table_support(self):
        return self.attribute_type == AttributeType.Table

    @table_support.setter
    def table_support(self, value):
        if value:
            assert self.attribute_type in (AttributeType.Unknown, AttributeType.Table)
            self.attribute_type = AttributeType.Table
        else:
            assert self.attribute_type != AttributeType.Table

    @property
    def counter(self):
        return self.attribute_type == AttributeType.Counter

    def to_dict(self):
        # TODO: Save/restore table info?
        return {
            'name': self.name,
            'description': sorted(list(set(self.description))),
            'access': [a.name for a in self.access],
            'optional': self.optional,
            'deprecated': self.deprecated,
            'size': self.size.to_dict(),
            'avc': self.avc,
            'tca': self.tca,
            'table-support': self.table_support,
            'type': self.attribute_type.name,
            'constraint': self.constraint,
            'default': self.default,
        }

    def dump(self, prefix="      "):
        print('{}Attribute: {}'.format(prefix, self.name))
        print('{}    Index     : {}'.format(prefix, self.index))
        print('{}    Access    : {}'.format(prefix, self.access))
        print('{}    Optional  : {}'.format(prefix, self.optional))
        print('{}    Deprecated: {}'.format(prefix, self.deprecated))
        print('{}    Size      : {}'.format(prefix, self.size))
        print('{}    Avc       : {}'.format(prefix, self.avc))
        print('{}    Tca       : {}'.format(prefix, self.tca))
        print('{}    Type      : {}'.format(prefix, self.attribute_type.name))
        print('{}    Constraint: {}'.format(prefix, self.constraint))
        print('{}    Default   : {}'.format(prefix, self.default))
        print('')

    @staticmethod
    def load(data, index):
        attr = Attribute()
        attr.name = data.get('name')
        attr.index = index
        attr.description = sorted(list(set(data.get('description', []))))
        attr.optional = data.get('optional', False)
        attr.deprecated = data.get('deprecated', False)
        attr.tca = data.get('tca', False)
        attr.avc = data.get('avc', False)
        attr.size = AttributeSize.load(data.get('size'))
        attr.default = data.get('default', None)
        attr.access = AttributeAccess.load(data.get('access'))
        attr.attribute_type = AttributeType[data.get('type', AttributeType.Unknown.name)]
        attr.constraint = data.get('constraint', None)
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
        text = paragraph.text.lower()[:80]

        if is_bold and \
                (style not in {'attribute follower', 'attribute list'} or
                 (style == 'attribute follower' and
                 ('aal5 profile pointer' in text or 'deprecated 3' in text  # see 9.13.4
                  or 'grandmaster id:' in text or 'steps removed:' in text or 'time source:' in text))):  # see 9.12.19

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
                ('T Ime', 'Time'),
                ('B Lock', 'Block'),
                ('R Evision', 'Revision'),
                ('A Dditional', 'Additional'),
                ('D Ate', 'Date'),
                ('N Ame', 'Name'),
                ('P Art', 'Part'),
                ('1 St', '1st'),
                ('2 Nd', '2nd'),
                ('3 Rd', '3rd'),
                ('4 Th', '4th'),
                ('1St', '1st'),
                ('2Nd', '2nd'),
                ('3Rd', '3rd'),
                ('4Th', '4th'),
                ('1 /2', '1/2'),
                ('1/ 2', '1/2'),
                ('1 _2', '1_2'),
                ('1_ 2', '1_2'),
                ('/', '_'),
                ('-', '_'),
                ('C=0+1', 'C01'),
                ('C-= 0', 'C0'),
                ('C_= 0', 'C0'),
                ('\+', '_'),
                (',', ' '),
                ('Packets, Usable', 'Packets Usable'),
                ('T Cont', 'TCont'),
                ('R Eporting', 'Reporting'),
                ('I Ndication', 'Indication'),
                ('H Ook', 'Hook'),
                ('R Eset', 'Reset'),
                ("R'S'", 'R S'),
                ('I Nterval', 'Interval'),
                ('M Essage', 'Message'),
                ('M Ulticast', 'Multicast'),
                ('T Ype', 'Type'),
                ('F Ail', 'Fail'),
                ('P Ayload', 'Payload'),
                ('M Anagement', 'Management'),
                ('Battery B Ackup', 'Battery Backup'),
                ('O Ption', 'Option'),
                ('U Nit', 'Unit'),
                ('B It', 'Bit'),
                ('FailThreshold', 'Fail Threshold'),
                ('Failthreshold', 'Fail Threshold'),
                ('DegradeThreshold', 'Degrade Threshold'),
                ('LineClass', 'Line Class'),
                ('Lineclass', 'Line Class'),
                ('"leftr"', 'leftr'),
                ('"Leftr"', 'Leftr'),
                ('( S F )', ''),
                (' Sd ', ''),
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

            attribute.name = ' '.join(attribute.name.strip().split())
            attribute.description.append(content)
            attribute.description.sort()
            attribute.deprecated = attribute.name.lower()[:10] == 'deprecated'

        return attribute

    def parse_attribute_settings_from_text(self, content, paragraph):
        # Any content?
        if isinstance(content, int):
            text = ascii_only(paragraph.text).strip()
            if len(text) == 0:
                return

            self.description.append(content)
            self.description.sort()

            # Check for access, mandatory/optional, and size keywords.  These are in side
            # one or more () groups
            paren_items = re.findall('\(([^)]+)*', text)
            if len(paren_items) < 3:
                return

            for item in paren_items:
                if item.lower() == 'all zero bytes':
                    return

                # Mandatory/optional is the easiest
                if item.lower() == 'mandatory':
                    if self.optional is True:
                       print(f"{self.name}: Optional flag already decoded as True")
                    else:
                        self.optional = False
                    continue

                if item.lower() == 'optional':
                    if self.optional is False:
                       print(f"{self.name}: Optional flag already decoded as False")
                    else:
                        self.optional = True
                    continue

                # Try to see if the access for the attribute is this item
                access_item = item.replace('-', '').strip()

                if access_item.lower() == 'rwsc':                # Address type if 9.2.3 Port-ID
                    access_item = 'r, w, set-by-create'
                elif access_item.lower() == 'r, w setbycreate':  # Section 9.7.4
                    access_item = 'r, w, set-by-create'
                elif access_item.lower() == 'r,w if applicable, setbycreate if applicable':  # Section 9.1.10
                    access_item = 'r, w, set-by-create'

                access_list = [item for item in access_item.lower().split(',')
                               if item.strip() != '']
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

    def find_type(self, managed_entity):
        read_only = {AttributeAccess.Read}
        try:
            if self.index == 0:        # Always a pointer
                if self.size is None or self.size.octets != 2:
                    return
                self.attribute_type = AttributeType.Pointer
                return

            # PM Counters are a pain, but manageable
            if 'history data' in managed_entity.name.lower() or 'extended pm' in managed_entity.name.lower():
                if 'end time' not in self.name.lower() and self.access == read_only and not self.table_support:
                    self.attribute_type = AttributeType.Counter
                    return

            if self.attribute_type == AttributeType.Unknown and self.size is not None:
                # Do some more investigation.  So far Counter, ME Instance(pointer), and Table have been identified
                # above or during previous parsing.
                if self.size.octets in (1, 2, 4, 8):
                    self.attribute_type = AttributeType.UnsignedInteger
                    return

                self.attribute_type = AttributeType.Octets
                return
            #
            if self.attribute_type == AttributeType.Unknown:
                return
                #
                # String = 2           # Readable String
                # SignedInteger = 5    # Signed integer, often expressed as 2's complement
                # Pointer = 6          # Managed Entity ID or pointer to a Managed instance
                # BitField = 7         # Bitfield
                # Enumeration = 8      # Fixed number of values (Unsigned Integers)

        except Exception as _e:
            pass
#
#
#
# TODO: Still need to test/decode AVC flag
# TODO: Still need to test/decode TCA flag
