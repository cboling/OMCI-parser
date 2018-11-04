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
    SIZE_KEYWORDS = {'byte', 'bit'}   # TODO: More to come
    SKIP_KEYWORDS = {'note'}

    def __init__(self):
        self._octets = None
        self._bits = None
        self._repeat_count = 1
        self._repeat_max = 1
        self.getnext_required = False  # Attribute could span several messages

    def __str__(self):
        return 'Size: {} bytes'.format(self.octets)

    @staticmethod
    def create_from_keywords(text):
        # Finally, is it a size item (watch out for bits and bytes in description text)
        if any(s in text.lower() for s in AttributeSize.SKIP_KEYWORDS) or \
            not any(s in text.lower() for s in AttributeSize.SIZE_KEYWORDS) or \
                len(text) >= 14:
            return None

        size = AttributeSize()
        # print("Size text is:\t'{}'".format(text), end="")
        try:
            if 'byte' in text:
                try:
                    size._octets = int(text.replace('-', ' ').split(' ')[0])
                    # print('... {}'.format(size._octets))
                except ValueError:
                    # Some Known others that trigger this are:
                    #  N * 20 bytes, N * 7 bytes, ...
                    #  all zero bytes
                    #  N bytes
                    #  18N bytes, 5N bytes
                    if text.lower()[:len('n * ')] == 'n * ':
                        # TODO: figure out what N refers to
                        size._octets = int(text.split(' ')[2])
                    elif 'n bytes' == text.lower():
                        # So far the MEs that use this are:
                        # ONU Remote debug 'Reply Table', Need to do get/getNext size size is not specified
                        # OMCI
                        size._octets = 0
                        size.getnext_required = True

                    elif 'n bytes' in text.lower():
                        # TODO: figure out what N refers to
                        size._octets = int(text[:-len('n bytes')])
                    else:
                        print("TODO: Further decode work needed here")
                        raise    # TODO: more work needed here

            elif 'bit' in text:
                size._bits = int(text.replace('-', ' ').split(' ')[0])
                # print('... {}'.format(size._bits))
            else:
                # Some Known others are:
                #
                print('... Not Decoded')
                size = None

        except Exception as _e:
            # Some Known others that trigger this are:
            #  all zero bytes
            #
            print('... Opps')
            size = None

        return size

    @property
    def octets(self):
        if self._octets is not None:
            return self._octets

        if self._bits is not None:
            return self._bits / 8

        return None