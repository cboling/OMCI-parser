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
import json
from text import ascii_only
from tables import Table


class SectionList(object):
    """ A list of sections (Headings + Paragraphs + Tables) that can be saved/restored"""

    def __init__(self):
        self._sections = list()

    def __getitem__(self, item):
        return self._sections[item]  # delegate to li.__getitem__

    def __iter__(self):
        for section in self._sections:
            yield section

    def __len__(self):
        return len(self._sections)

    def add(self, section):
        assert isinstance(section, SectionHeading), 'Invalid type'
        self._sections.append(section)
        return self

    def get(self, index):
        return self._sections[index]

    def save(self, filepath):
        data = json.dumps(self.as_dict_list(), indent=2, separators=(',', ': '))
        with open(filepath, 'w') as f:
            f.write(data)

    def load(self, filepath):
        self._sections = list()
        with open(filepath, 'r') as f:
            data = json.load(f)
            for head in data:
                section = SectionHeading()
                section.style_name = head['style_name']
                section.section_number = head['section_number']
                section.title = head['title']
                section.section_points = head['section_points']

                for content in head['contents']:
                    if isinstance(content, int):
                        section.contents.append(content)
                    elif isinstance(content, dict):
                        table = Table()

                        table.heading = content.get('heading')
                        table.doc_table_number = content.get('doc_table_number')
                        table.table_number = content.get('table_number')
                        table.num_columns = content.get('num_columns')
                        table.full_title = content.get('full_title')
                        table.short_title = content.get('short_title')

                        if isinstance(content.get('rows'), list):
                            for row in content['rows']:
                                table.rows.append(row)

                        section.contents.append(table)
                    else:
                        print('Unknown type: {}'.format(type(content)))

                self._sections.append(section)

    def as_dict_list(self):
        # Contents is special
        results = list()

        for item in self._sections:
            contents = [x if isinstance(x, int) else x.__dict__ for x in item.contents]
            results.append(
                {
                    'contents': contents,
                    'style_name': item.style_name,
                    'section_number': item.section_number,
                    'title': item.title,
                    'section_points': item.section_points,
                })
        return results

    def dump(self):
        for num, entry in enumerate(self):
            print('Section: {}'.format(num))
            entry.dump()

    def find_section(self, section_number):
        entry = next((s for s in self if s.section_number == section_number), None)

        if entry is not None:
            return entry

        raise KeyError('Section {} not found'.format(section_number))

    def find_section_by_name(self, name):
        name_lower = name.replace(' ', '').lower()
        return next((s for s in self
                    if s.title.replace(' ', '').lower() == name_lower), None)


class SectionHeading(object):
    """
    A section object holds both the title of a given section as well as the
    paragraph numbers of text and table entries within it (until the next section)

    NOTE: This should not be confused with the docx Section object that is
          provides page setting and format information
    """
    def __init__(self):
        self.contents = list()     # First paragraph holds the heading paragraph
                                   # If (int) then paragraph number, else (Table)
                                   # then our Table object
        self.style_name = None
        self.section_number = None
        self.title = None
        self.section_points = []

    def __str__(self):
        return 'Section: {}: {}, paragraphs: {}'.format(self.section_number,
                                                        self.title,
                                                        self.paragraph_numbers)

    @property
    def paragraph_numbers(self):
        return [p for p in self.contents if isinstance(p, int)]

    @property
    def tables(self):
        return [p for p in self.contents if isinstance(p, Table)]

    def add_contents(self, content):
        self.contents.append(content)

    @staticmethod
    def create(number, paragraph):
        section = SectionHeading()

        section._contents = [number]

        if paragraph is  None:
            return section

        section.style_name = paragraph.style.name

        try:
            assert 'heading ' in section.style_name.lower(), 'Heading style not found'
            if isinstance(paragraph.text, list):
                heading_txt = ascii_only(" ".join(paragraph.text))
            else:
                heading_txt = ascii_only(paragraph.text)

            # Split into section number and section title
            headings = re.findall(r"[^\s']+", heading_txt)

            assert len(headings) >= 2, \
                "Foreign Heading string format: '{}'".format(paragraph.text)

            section.section_number = headings[0]
            section.title = ' '.join(headings[1:])
            section.section_points = [pt for pt in section.section_number.split('.')]

            return section

        except Exception as _e:
            raise

    def dump(self, prefix="  "):
        tbls = [t for t in self.contents if isinstance(t, Table)]

        print('{}Number      : {} / pts: {}'.format(prefix,
                                                    self.section_number,
                                                    self.section_points))
        print('{}# Paragraphs: {}'.format(prefix, len(self.paragraph_numbers)))
        print('{}# Tables    : {}'.format(prefix, len(tbls)))

        if len(tbls):
            for tnum, tbl in enumerate(tbls):
                print('{}  List Entry:  {}'.format(prefix, tnum))
                tbl.dump(prefix="  " + prefix)
            print('{}-------------------------------------'.format(prefix))


