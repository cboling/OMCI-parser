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
import datetime


class VersionList(object):
    """ A list of versions that can be saved/restored"""
    def __init__(self):
        self._versions = list()

    def __getitem__(self, item):
        return self._versions[item]  # delegate to li.__getitem__

    def __iter__(self):
        for version in self._versions:
            yield version

    def __len__(self):
        return len(self._versions)

    @property
    def versions(self):
        return self._versions

    def add(self, version):
        assert isinstance(version, VersionHeading), 'Invalid type'
        self._versions.append(version)
        return self

    def get(self, index):
        return self._versions[index]

    def load(self, versions):
        self._versions = [VersionHeading.load(info) for info in versions]

    def as_dict_list(self):
        return [version.to_dict() for version in self._versions]

    def dump(self):
        for num, entry in enumerate(self):
            entry.dump()


class VersionHeading(object):
    def __init__(self):
        self.version = ''
        self.name = ''
        self.create_time = 0.0
        self.itu_document = ''
        self.sha256 = ''

    def __str__(self):
        return '  Version: {}: {}'.format(self.name, self.version)

    def to_dict(self):
        return {
            'version': self.version,
            'name': self.name,
            'create_time': self.create_time,
            'itu_document': self.itu_document,
            'sha256': self.sha256
        }

    @staticmethod
    def load(data):
        version = VersionHeading()
        version.version = data['version']
        version.name = data['name']
        version.create_time = data['create_time']
        version.itu_document = data['itu_document']
        version.sha256 = data['sha256']
        return version

    def dump(self, prefix="    "):
        ts = datetime.datetime.fromtimestamp(self.create_time)
        print('{}Name        : {}'.format(prefix, self.name))
        print('{}Version     : {}'.format(prefix, self.version))
        print('{}Create Time : {}'.format(prefix, ts.strftime('%Y-%m-%d %H:%M:%S.%f (UTC)')))
        print('{}Document    : {}'.format(prefix, self.itu_document))
        print('{}SHA-256 Hash: {}'.format(prefix, self.sha256))
        print('')
