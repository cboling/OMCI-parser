#!/usr/bin/env python
# #
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
try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest
from transitions import Machine
from contents import *
from attributes import AttributeList, Attribute
from actions import Actions
from avc import AVC
from alarms import Alarm
import json


class ClassIdList(object):
    def __init__(self):
        self._entities = dict()     # Key -> (int) class_id,  Value-> (ClassId)

    def __getitem__(self, item):
        return self._entities[item]  # delegate to li.__getitem__

    def __iter__(self):
        for entry in self._entities:
            yield entry

    def __len__(self):
        return len(self._entities)

    def keys(self):
        return self._entities.keys()

    def values(self):
        return self._entities.values()

    def items(self):
        return self._entities.items()

    def has_key(self, k):
        return k in self._entities

    def add(self, class_id):
        assert isinstance(class_id, ClassId), 'Invalid type'
        assert class_id.cid not in self._entities, \
            'Entity already exists: {}'.format(class_id)
        self._entities[class_id.cid] = class_id
        return self

    @staticmethod
    def parse_sections(sections, cid_section):
        """
        Look for a specific section and determine the table it is in.

        After finding the section, this is more focused on the latest
        G.988 document where the list is in the one and only table
        """
        cid_list = ClassIdList()
        cid_heading_section = sections.find_section(cid_section)

        if cid_heading_section is not None:
            cid_table = next((t for t in cid_heading_section.contents
                              if isinstance(t, Table)), None)
            if cid_table is not None:
                # We know that the Class ID table has a width of 2. See if a
                # table fixup is needed (and not detected during pre-parse)
                cid_table = ClassIdList.fix_me_table(cid_table, 2)

                headings = cid_table.heading
                for row in cid_table.rows:
                    try:
                        cid = ClassId()
                        cid.cid = int(row.get(headings[0]))
                        cid.name = row.get(headings[1])
                        cid_list.add(cid)

                        cid.section = sections.find_section_by_name(cid.name)

                    except ValueError as _e:
                        pass        # Expected for reserved range statements

                    except Exception as _e:
                        raise              # Not expected

        return cid_list

    @staticmethod
    def fix_me_table(orig_table, width):
        if orig_table.num_columns == width:
            return orig_table

        table = Table()
        table.num_columns = width
        table.full_title = orig_table.full_title
        table.short_title = orig_table.short_title
        table.doc_table_number = orig_table.doc_table_number
        table.table_number = orig_table.table_number
        table.heading = tuple(orig_table.heading[n] for n in range(width))

        try:
            all_cells = [orig_table.heading[n] for n in range(width, orig_table.num_columns)]
            for row in orig_table.rows:
                if len(row) == orig_table.num_columns:
                    all_cells.extend([row[key] for key in orig_table.heading])

                elif len(row) > 0:
                    heading = [orig_table.heading[n] for n in range(len(row))]
                    all_cells.extend([row[key] for key in heading])

            def grouper(iterable, length, fillvalue=''):
                args = [iter(iterable)] * length
                return zip_longest(*args, fillvalue=fillvalue)

            for text in grouper(all_cells, table.num_columns):
                row_data = dict(zip(table.heading, text))
                table.rows.append(row_data)

        except Exception as e:
            print('Table parse error in table {} - {}: {}'.format(table.doc_table_number,
                                                                  table.full_title,
                                                                  e))
        return table

    def save(self, output):
        final = dict()      # Key = class-id, Value = data

        try:
            for cid, me_class in self._entities.items():
                if me_class.state != 'complete':
                    continue
                assert cid not in final, 'Duplicate Class ID: {}'.format(cid)
                final[cid] = me_class.to_dict()

            # Convert to JSON
            data = json.dumps(final, indent=2, separators=(',', ': '))
            with open(output, 'w') as f:
                f.write(data)

        except Exception as _e:
            raise


class ClassId(object):
    """ Managed Entity Class Information """
    STATES = ['initial', 'description', 'relationships', 'attributes', 'actions',
              'notifications', 'alarms', 'avcs', 'tests', 'complete', 'failure',
              'end_of_section']

    TRANSITIONS = [
        # While in initial 'basic' state
        {'trigger': 'normal', 'source': 'initial', 'dest': 'description'},
        {'trigger': 'description', 'source': 'initial', 'dest': 'description'},
        {'trigger': 'relationship', 'source': 'initial', 'dest': 'relationships'},
        {'trigger': 'attribute', 'source': 'initial', 'dest': 'attributes'},

        # While in 'description' state
        {'trigger': 'normal', 'source': 'description', 'dest': 'description'},
        {'trigger': 'relationship', 'source': 'description', 'dest': 'relationships'},
        {'trigger': 'attribute', 'source': 'description', 'dest': 'attributes'},

        # While in 'relationships' state
        {'trigger': 'normal', 'source': 'relationships', 'dest': 'relationships'},
        {'trigger': 'attribute', 'source': 'relationships', 'dest': 'attributes'},

        # While in 'attributes' state
        {'trigger': 'normal', 'source': 'attributes', 'dest': 'attributes'},
        {'trigger': 'action', 'source': 'attributes', 'dest': 'actions'},

        # While in 'actions' state
        {'trigger': 'normal', 'source': 'actions', 'dest': 'actions'},
        {'trigger': 'notification', 'source': 'actions', 'dest': 'notifications'},

        # While in 'notifications' state
        {'trigger': 'normal', 'source': 'notifications', 'dest': 'notifications'},
        {'trigger': 'alarm', 'source': 'notifications', 'dest': 'alarms'},
        {'trigger': 'avc', 'source': 'notifications', 'dest': 'avcs'},
        {'trigger': 'test', 'source': 'notifications', 'dest': 'tests'},

        # While in 'alarms' state
        {'trigger': 'normal', 'source': 'alarms', 'dest': 'alarms'},
        {'trigger': 'avc', 'source': 'alarms', 'dest': 'avcs'},
        {'trigger': 'test', 'source': 'alarms', 'dest': 'tests'},

        # While in 'avc' state
        {'trigger': 'normal', 'source': 'avcs', 'dest': 'avcs'},
        {'trigger': 'alarm', 'source': 'avcs', 'dest': 'alarms'},
        {'trigger': 'test', 'source': 'avcs', 'dest': 'tests'},

        # While in 'tests' state
        {'trigger': 'normal', 'source': 'tests', 'dest': 'tests'},
        {'trigger': 'alarm', 'source': 'tests', 'dest': 'alarms'},
        {'trigger': 'avc', 'source': 'tests', 'dest': 'avcs'},

        # Do wildcard triggers last so it covers all previous states
        {'trigger': 'end_of_section', 'source': '*', 'dest': 'end_of_section'},
        {'trigger': 'complete', 'source': '*', 'dest': 'complete'},
        {'trigger': 'failure', 'source': '*', 'dest': 'failure'},
    ]

    def __init__(self):
        self.cid = None                   # Class Id
        self.name = None                  # Title
        self.section = None               # Document section

        self.parser = initial_parser
        self._paragraphs = None
        self.machine = Machine(model=self, states=ClassId.STATES,
                               transitions=ClassId.TRANSITIONS,
                               initial='initial',
                               queued=True,
                               name='{}-{}'.format(self.name, self.cid))

        # Following hold lists of paragraph numbers
        self._description = list()         # Description (paragraph numbers)
        self._relationships = list()       # Relationships paragraph # (if any)
        # Following hold lists of associated objects
        # TODO: Make next three None so we can tell if they ever get decoded
        self.attributes = AttributeList()  # Ordered list of attributes
        self.actions = set()               # Mandatory actions/message-types
        self.optional_actions = set()      # Allowed actions/message-types
        self.alarms = None                 # Alarm list (if any)
        self.avcs = None                   # Attribute Value Change (if any)
        self.test_results = None           # Test Results (if any)
        self.hidden = False                # Not reported or ignore in MIB upload

    def __str__(self):
        return 'Class ID: {}: {}, State: {}'.format(self.cid, self.name, self.state)

    def to_dict(self):
        return {
            'class_id': self.cid,                       # int
            'name': self.name,                          # str
            'section': self.section.to_dict(),          # dict()
            'description': self._description,           # [ paragraph numbers - int ]
            'relationships': self._relationships,       # [ paragraph numbers - int ]
            'actions': [a.name for a in self.actions],
            'optional_actions': [a.name for a in self.optional_actions],
            'attributes': self.attributes.to_dict(),    # Key is index
            'alarms': self.alarms.to_dict() if self.alarms is not None else {},
            'avcs': self.avcs.to_dict() if self.avcs is not None else {},
            'test_results': {},                         # TODO: self.test_results.to_dict()
            'hidden': self.hidden                       # bool
        }

    def deep_parse(self, paragraphs):
        """ Fill out detailed class information """
        if self.section is None:
            return self

        self._paragraphs = paragraphs
        for content in self.section.contents:
            try:
                if isinstance(content, int):
                    # Paragraph number
                    trigger, text = self.parser(content, paragraphs)

                elif isinstance(content, Table):
                    # Table object
                    # TODO: trigger = self.parser(content, paragraphs)
                    trigger, text = self.parser(content, None)

                else:
                    raise NotImplementedError('Unknown content type: {}'.
                                              format(type(content)))
                # process info
                getattr(self, trigger)(text, content)

            except Exception as e:
                self.failure(None, None)
                print("FAILURE: During deep parsing. Content: {}: '{}'".format(content,
                                                                               e.message))
                raise

        self.complete(None, None)
        return self

    def on_enter_initial(self, _text, _content):
        self.parser = initial_parser
        raise NotImplementedError('Start in initial state, but never transition to it')

    def on_enter_description(self, text, content):
        """
        Detected description text for the ME. Save paragraph number
        if parser returned text
        """
        self.parser = description_parser

        if text is not None and len(text):
            self._description.append(content)

    def on_enter_relationships(self, text, content):
        """
        Detected description text for the ME. Save paragraph number
        if parser returned text
        """
        self.parser = relationships_parser

        if text is not None and len(text):
            self._description.append(content)

    def on_enter_attributes(self, text, content):
        self.parser = attributes_parser
        if isinstance(content, int):
            if text is not None and len(text):
                attribute = Attribute.create_from_paragraph(content,
                                                            self._paragraphs[content])
                if attribute is not None:
                    self.attributes.add(attribute)

                last = self.attributes[-1] if len(self.attributes) else None
                if last is None:
                    raise KeyError('Unable to decode initial attribute: class_id: {}'.
                                   format(self))

                last.parse_attribute_settings_from_text(content,
                                                        self._paragraphs[content])
        elif isinstance(content, Table):
            last = self.attributes[-1] if len(self.attributes) else None
            if last is None:
                raise KeyError('Unable to decode initial attribute: class_id: {}'.
                               format(self))

            last.parse_attribute_settings_from_text(content, None)

    def on_enter_actions(self, text, content):
        self.parser = actions_parser
        if text is not None and len(text):
            if isinstance(content, int):
                action = Actions.create_from_paragraph(self._paragraphs[content])

                if action is not None:
                    self.actions.update(action)
                pass

            else:
                raise NotImplementedError('TODO: Support Tables')

    def on_enter_notifications(self, text, content):
        self.parser = notifications_parser
        # TODO: Need to be smarter here.  Will get tables and Test Results are formatted
        #       much like attributes sometimes.
        if isinstance(content, int):
            if text is not None and len(text):
                # Typical to get 'None.' if no notifications supported
                # TODO: Breakpoint if it is not 'None.' for debugging
                if 'none' not in ascii_only(text).strip().lower():
                    print('Found something. {}'.format(text))

        elif isinstance(content, Table):
            pass        # ignore tables at the 'notification' state

    def on_enter_alarms(self, text, content):
        self.parser = alarms_parser
        if isinstance(content, int):
            # We currently ignore extra alarm text
            # TODO: verify no ME uses this to describe alarms
            pass

        elif isinstance(content, Table):
            alarms = Alarm.create_from_table(content)
            if alarms is not None:
                assert self.alarms is None, 'Alarms have already been decoded'
                self.alarms = alarms
            else:
                # Some MEs have additional descriptions and tables related
                # to the alarms, but we do not have any interest in them.
                pass

    def on_enter_avcs(self, text, content):
        self.parser = avcs_parser
        if isinstance(content, int):
            # TODO: Delete if no one calls this
            if text is not None and len(text):
                pass

        elif isinstance(content, Table):
            avc = AVC.create_from_table(content)
            if avc is not None:
                assert self.avcs is None, 'AVCs have already been decoded'
                self.avcs = avc

    def on_enter_tests(self, text, content):
        self.parser = tests_parser
        if text is not None and len(text):
            if isinstance(content, int):
                pass
                # attribute = Attribute.create_from_paragraph(content,
                #                                             self._paragraphs[content])
                # if attribute is not None:
                #     self.attributes.add(attribute)
                # else:
                #     last = self.attributes[-1:] if len(self.attributes) else None
                #     if last is None:
                #         raise KeyError('Unable to decode initial attribute: class_id: {}'.
                #                        format(self))
                #
                #     last.description.append(content)
            else:
                raise NotImplementedError('TODO: Support Tables')

    def on_enter_complete(self, _text, _content):
        # TODO: Good place for test/verification all was found
        #       that we are looking fo
        self.parser = None

    def on_enter_failure(self, _text, _content):
        self.parser = None

    def on_enter_end_of_section(self, _text, _content):
        """ Handles trailing information that we do not care or support"""
        self.parser = eos_parser


if __name__ == '__main__':
    """
    Run this as a program and it will produce a PNG image of the ClassID
    state machine to the current working directory with a name of
    
                ClassID-StageDiagram.png
    """
    from transitions.extensions import GraphMachine as Machine

    c = ClassId()
    machine = c.machine

    # in cases where auto transitions should be visible
    # Machine(model=m, show_auto_transitions=True, ...)

    # draw the whole graph ...
    machine.get_graph().draw('ClassID-StageDiagram.png', prog='dot')
