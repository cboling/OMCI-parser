#!/usr/bin/env python
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
import argparse
import time
from docx import Document

from class_id import ClassIdList
from parsed_json import ParsedJson
from preparsed_json import PreParsedJson
from versions import VersionHeading
from text import camelcase


MEClassSection = "11.2.4"       # Class IDs


def parse_args():
    parser = argparse.ArgumentParser(description='G.988 Final Parser')

    parser.add_argument('--ITU', '-I', action='store',
                        default='T-REC-G.988-201711-I!!MSW-E.docx',
                        help='Path to ITU G.988 specification document')

    parser.add_argument('--input', '-i', action='store',
                        default='G.988.PreCompiled.json',
                        help='Path to pre-parsed G.988 data, default: G.988.PreCompiled.json')

    parser.add_argument('--output', '-o', action='store',
                        default='G.988.Parsed.json',
                        help='Output filename, default: G.988.Parsed.json')

    parser.add_argument('--classes', '-c', action='store',
                        default='11.2.4',
                        help='Document section number with ME Class IDs, default: 11.2.4')

    args = parser.parse_args()
    return args


class Main(object):
    """ Main program """
    def __init__(self):
        self.args = parse_args()
        self.paragraphs = None
        self.body = None

        self.preparsed = PreParsedJson()
        self.parsed = ParsedJson()
        version = VersionHeading()
        version.name = 'parser'
        version.create_time = time.time()
        version.itu_document = self.args.ITU
        version.version = self.get_version()
        version.sha256 = self.get_file_hash(version.itu_document)
        self.parsed.add(version)

    @staticmethod
    def get_version():
        with open('VERSION', 'r') as f:
            for line in f:
                line = line.strip().lower()
                if len(line) > 0:
                    return line

    @staticmethod
    def get_file_hash(filename):
        import hashlib
        with open(filename, 'rb') as f:
            data = f.read()
            return hashlib.sha256(data).hexdigest()

    @property
    def sections(self):
        return self.preparsed.sections

    @property
    def section_list(self):
        return self.preparsed.section_list

    @property
    def class_ids(self):
        return self.parsed.class_ids

    def load_itu_document(self):
        return Document(self.args.ITU)

    def start(self):
        print("Loading ITU Document '{}' and parsed data file '{}'".format(self.args.ITU,
                                                                           self.args.input))
        self.preparsed.load(self.args.input)
        for version in self.preparsed.versions:
            self.parsed.add(version)

        document = self.load_itu_document()
        self.paragraphs = document.paragraphs
        # doc_sections = document.sections
        # styles = document.styles
        # self.body = document.element.body

        print('Extracting ME Class ID values')
        class_ids = ClassIdList.parse_sections(self.section_list,
                                               self.args.classes)
        for _cid, me_class in class_ids.items():
            self.parsed.add(me_class)

        print('Found {} ME Class ID entries. {} have sections associated to them'.
              format(len(self.class_ids),
                     len([c for c in self.class_ids.values()
                          if c.section is not None])))

        num_att_before = len([c for c in self.class_ids.values() if c.cid in att_openomci])

        # TODO: These need more work. skipping for now
        crazy_formatted_mes = \
            {23, 319, 320,  # CES physical interface performance MEs
             164,           # MoCA interface performance
             165,           # VDLS2 line config extensions
             157,           # Large String                      (part of AT&T OpenOMCI v3.0)
             309,           # Multicast operations (Dot1ag)     (part of AT&T OpenOMCI v3.0)
             415}

        print('Skipping the following MEs due to complex document formatting')
        print("    {}".format(crazy_formatted_mes))
        todo_class_ids = {k: v for k, v in self.class_ids.items()
                          if k not in crazy_formatted_mes}

        # num_att_after_hard_me = len([c for c in todo_class_ids.values() if c.cid in att_openomci])

        print('Managed Entities without Sections')
        for c in [c for c in todo_class_ids.values() if c.section is None]:
            print('    {:>4}: {}'.format(c.cid, c.name))

        # Work with what we have
        todo_class_ids = {cid: c for cid, c in todo_class_ids.items()
                          if c.section is not None}

        # num_att_end = len([c for c in todo_class_ids.values() if c.cid in att_openomci])
        #
        # print('Of {} AT&T OpenOMCI MEs, {} after eliminating hard ones, and {} after ones with sections'.
        #       format(num_att_before, num_att_after_hard_me, num_att_end))
        #
        # final_class_ids = ClassIdList()
        # for cid, c in todo_class_ids.items():
        #     if c.cid in att_openomci:
        #         final_class_ids.add(c)
        print('')
        print('working on {} OpenOMCI MEs'.format(len(todo_class_ids)))
        print('')
        print('Parsing deeper for managed Entities with Sections')

        # Of 317 MEs, 220 were parsed successfully and 97 failed if we do all
        final_class_ids = todo_class_ids
        #
        # If we just do AT&T, can do 61 total

        for c in final_class_ids.values():
            if c.section is None:
                c.failure(None, None)
                continue

            print('    {:>9}:  {:>4}: {} -> {}'.format(c.section.section_number,
                                                       c.cid,
                                                       c.name,
                                                       camelcase(c.name)))
            c.deep_parse(self.paragraphs)

        # Some just need some manual intervention
        final_class_ids = self.fix_difficult_class_ids(final_class_ids)

        completed = len([c for c in final_class_ids.values() if c.state == 'complete'])
        failed = len([c for c in final_class_ids.values() if c.state == 'failure'])

        print('Of {} MEs, {} were parsed successfully and {} failed'.format(len(final_class_ids),
                                                                            completed,
                                                                            failed))
        # Run some sanity checks
        print('\n\n\nValidating ME Class Information, total of {}:\n'.
              format(len(final_class_ids)))

        class_with_issues = 0
        class_with_no_actions = 0
        class_with_no_attributes = 0
        attributes_with_no_access = 0
        attributes_with_no_size = 0
        class_with_too_many_attributes = 0
        num_attributes = 0

        for c in final_class_ids.values():
            print('  ID: {}: {} -\t{}'.format(c.cid, c.section.section_number, c.name),
                  end='')

            if c.state != 'complete':
                print('\t\tParsing ended in state {}', c.state)
                class_with_issues += 1

            if len(c.actions) == 0:
                print('\t\tActions: No actions decoded for ME')
                class_with_issues += 1
                class_with_no_actions += 1
                c.failure(None, None)       # Mark invalid
            else:
                print('\t\tActions: {}'.format({a.name for a in c.actions}))

            if len(c.attributes) == 0:
                print('\t\tNO ATTRIBUTES')      # TODO Look for 'set' without 'get'
                class_with_issues += 1
                class_with_no_attributes += 1
                c.failure(None, None)       # Mark invalid

            elif len(c.attributes) > 17:        # Entity ID counts as well in this list
                print('\t\tTOO MANY ATTRIBUTES')
                class_with_issues += 1
                class_with_too_many_attributes += 1
                c.failure(None, None)       # Mark invalid

            else:
                for attr in c.attributes:
                    num_attributes += 1
                    print('\t\t\t\t{}'.format(attr.name), end='')
                    if attr.access is None or len(attr.access) == 0:
                        print('\t\t\t\tNO ACCESS INFORMATION')
                        attributes_with_no_access += 1
                        c.failure(None, None)       # Mark invalid
                    else:
                        print('\t\t\t\tAccess: {}'.format({a.name for a in attr.access}))
                    if attr.size is None:
                        attributes_with_no_size += 1
                        print('\t\t\t\tNO SIZE INFORMATION')
                        c.failure(None, None)       # Mark invalid

        print('Section parsing is complete, saving JSON output...')
        print('=======================================================')

        # Output the results to a JSON file so it can be used by a code-generation
        # tool
        self.parsed.save(self.args.output)

        # Restore and verify
        self.parsed.load(self.args.output)
        self.parsed.dump()

        # Results
        print("Of the {} class ID, {} had issues: {} had no actions and {} had no attributes and {} with too many".
              format(len(final_class_ids), class_with_issues, class_with_no_actions,
                     class_with_no_attributes, class_with_too_many_attributes))

        print("Of the {} attributes, {} had no access info and {} had no size info".
              format(num_attributes, attributes_with_no_access, attributes_with_no_size))

    def fix_difficult_class_ids(self, class_list):
        # Special exception. Ethernet frame performance monitoring history data downstream
        # is in identical upstream and only a note of that exists. Fix it now
        if 321 in class_list.keys() and 322 in class_list.keys():
            down = class_list[321]
            up = class_list[322]
            down.attributes = up.attributes
            down.actions = up.actions
            down.optional_actions = up.optional_actions
            down.alarms = up.alarms
            down.avcs = up.avcs
            down.test_results = up.test_results
            down.hidden = up.hidden

        # For SIP user data, the Username&Password attribute is a pointer
        # to a security methods ME and is 2 bytes but is in the document as
        # just (2)
        if 153 in class_list.keys():
            from size import AttributeSize
            sip = class_list[153]
            sz = AttributeSize()
            sz._octets = 2
            sip.attributes[4].size = sz

        # For multicast subscriber config info. very hard to decode automatically
        if 310 in class_list.keys():
            from size import AttributeSize
            msci = class_list[310]
            msci.attributes.remove(8)
            msci.attributes.remove(7)
            sz = AttributeSize()
            sz._octets = 22
            sz.getnext_required = True
            msci.attributes[6].size = sz

        # Extended vlan config table.  Table is 16 octets
        if 171 in class_list.keys():
            from size import AttributeSize
            exvlan = class_list[171]
            sz = AttributeSize()
            sz._octets = 16
            exvlan.attributes[6].size = sz

        # Mcast gem interworking.  IPv6 Table is 24N octets
        if 281 in class_list.keys():
            from size import AttributeSize
            item = class_list[281]
            item.attributes.remove(8)
            item.attributes.remove(4)
            sz = AttributeSize()
            sz._octets = 24
            sz.getnext_required = True
            item.attributes[7].size = sz

        # OMCI.  IPv6 Table is 24N octets
        if 287 in class_list.keys():
            from size import AttributeSize
            item = class_list[287]
            sz = AttributeSize()
            sz._octets = 2
            sz.getnext_required = True
            item.attributes[1].size = sz

            sz = AttributeSize()
            sz._octets = 1
            sz.getnext_required = True
            item.attributes[2].size = sz

        # Dot1ag maintenance domain
        if 299 in class_list.keys():
            from size import AttributeSize
            item = class_list[299]
            sz = AttributeSize()
            sz._octets = 25
            sz._repeat_count = 2
            sz._repeat_max = 2
            item.attributes[3].size = sz

        # Dot1ag maintenance domain
        if 300 in class_list.keys():
            from size import AttributeSize
            item = class_list[300]
            sz = AttributeSize()
            sz._octets = 25
            sz._repeat_count = 2
            sz._repeat_max = 2
            item.attributes[3].size = sz

            sz = AttributeSize()
            sz._octets = 24
            item.attributes[5].size = sz

        # xDSL line inventory and status data part 5
        if 325 in class_list.keys():
            item = class_list[325]
            try:
                from actions import Actions
                # Type in document, not table attributes present
                item.actions.remove(Actions.GetNext)
            except KeyError:
                pass

        # xDSL line inventory and status data part 8
        if 414 in class_list.keys():
            item = class_list[414]
            try:
                from actions import Actions
                # Type in document, not table attributes present
                item.actions.remove(Actions.GetNext)
            except KeyError:
                pass

        return class_list


att_openomci = {
    2,
    5,
    6,
    7,
    11,
    24,
    45,
    47,
    53,
    58,
    84,
    130,
    131,
    133,
    134,
    135,
    136,
    137,
    138,
    139,
    142,
    143,
    148,
    150,
    151,
    152,
    153,
    155,
    156,
    157,
    158,
    171,
    256,
    257,
    262,
    263,
    264,
    266,
    268,
    272,
    273,
    274,
    277,
    278,
    280,
    281,
    287,
    290,
    299,
    300,
    302,
    305,
    309,
    310,
    312,
    321,
    322,
    329,
    332,
    335,
    336,
    340,
    341,
    344,
    345,
    346,
    349,
}


if __name__ == '__main__':
    try:
        Main().start()

    except Exception as _e:
        raise
