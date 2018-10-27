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
from text import *


class AttributeSize(object):
    """ Object to help describe the size requirements of an attribute """

    def __init__(self):
        self._octets = None
        self._bits = None
        self._repeat_count = None
        self._repeat_max = None

    def __str__(self):
        return 'Size: {} bytes'.format(self._octets)

    @staticmethod
    def create_from_keywords(keywords):
        size = None

        # TODO: Do some fancy decoding. Return None if not a decodable 'size'

        return size
