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
from .versions import VersionList, VersionHeading
from .class_id import ClassIdList, ClassId


class ParsedJson(object):
    def __init__(self):
        self._versions = VersionList()
        self._class_ids = ClassIdList()

    def add(self, item):
        assert isinstance(item, (VersionHeading, ClassId)), 'Invalid type'

        if isinstance(item, VersionHeading):
            self._versions.add(item)
        elif isinstance(item, ClassId):
            self._class_ids.add(item)
        return self

    @property
    def versions(self):
        return self._versions

    @property
    def class_ids(self):
        return self._class_ids

    def save(self, filepath):
        final = dict()      # Key = class-id, Value = data

        for cid, me_class in self._class_ids.items():
            if me_class.state != 'complete':
                continue
            assert cid not in final, 'Duplicate Class ID: {}'.format(cid)
            final[cid] = me_class.to_dict()

        # Convert to JSON
        data = {
            'versions': self._versions.as_dict_list(),
            'classes': final
        }
        json_data = json.dumps(data, indent=2, separators=(',', ': '))
        with open(filepath, 'w') as json_file:
            json_file.write(json_data)

    def load(self, filepath):
        self._class_ids = ClassIdList()

        with open(filepath, 'r') as json_file:
            data = json.load(json_file)
            self._versions.load(data.get('versions', dict()))
            self._class_ids = ClassIdList.load(data.get('classes', dict()))

    def dump(self):
        print('Version Info:')
        for _num, entry in enumerate(self._versions):
            entry.dump()

        print('')
        print('Class Info:')
        for _cid, entry in self._class_ids.items():
            entry.dump()
