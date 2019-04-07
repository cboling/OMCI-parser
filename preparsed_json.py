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
import json
from versions import VersionList, VersionHeading
from section import SectionList, SectionHeading


class PreParsedJson(object):
    def __init__(self):
        self._versions = VersionList()
        self._sections = SectionList()

    def add(self, item):
        assert isinstance(item, (VersionHeading, SectionHeading)), 'Invalid type'

        if isinstance(item, VersionHeading):
            self._versions.add(item)
        elif isinstance(item, SectionHeading):
            self._sections.add(item)
        return self

    @property
    def versions(self):
        return self._versions.versions

    @property
    def sections(self):
        return self._sections.sections

    def save(self, filepath):
        # {
        #     "versions": [
        #         {
        #             "version": "0.3.4",
        #             "name": "pre-parser",
        #             "create_time": 123.456,
        #             "itu_document": "abc.docx",
        #             "sha256": "12434"
        #         },
        #         ...
        #     ]
        #     "sections": [
        #         {
        #             section data
        #         },
        #         ...
        #     ]
        # }
        data = {
            'versions': self._versions.as_dict_list(),
            'sections': self._sections.as_dict_list()
        }
        json_data = json.dumps(data, indent=2, separators=(',', ': '))
        with open(filepath, 'w') as f:
            f.write(json_data)

    def load(self, filepath):
        self._versions = VersionList()
        self._sections = SectionList()

        with open(filepath, 'r') as f:
            data = json.load(f)
            self._versions.load(data.get('versions', dict()))
            self._sections.load(data.get('sections', dict()))

    def dump(self):
        print('Version Info:')
        for num, entry in enumerate(self.versions):
            entry.dump()

        print('')
        print('Section Info:')
        for num, entry in enumerate(self.sections):
            entry.dump()
