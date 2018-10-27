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
from docx import Document
import json


def parse_args():
    return {
        'input': 'T-REC-G.988-201711-I!!MSW-E.docx'
    }


class Main(object):
    """ Main program """
    def __init__(self):
        self.args = parse_args()

    def start(self):
        replacements = {
            160  : u'-',
            174  : u'r',        # Registered sign
            176  : u"degree-",  # Degree sign
            177  : u"+/-",
            181  : u"u",        # Micro
            189  : u"1/2",
            215  : u'*',
            224  : u"`a",
            946  : u'B',
            956  : u'v',
            969  : u'w',
            8211 : u'-',
            8217 : u"'",
            8220 : u"``",
            8221 : u"''",
            8230 : u"...",
            8722 : u'-',
            8804 : u'<=',
            61664: u'->',
            8805 : u'>=',
            8226 : u'o',  # Bullet
        }
        good = replacements.keys()
        bad_uni = dict()
        document = Document(self.args['input'])
        paragraphs = document.paragraphs

        for num, paragraph in enumerate(paragraphs):
            print '{} of {}'.format(num, len(paragraphs))
            try:
                text = paragraph.text
                bad = [ord(i) for i in text if ord(i) > 127 and ord(i) not in good]

                for uni in bad:
                    if uni not in bad_uni:
                        bad_uni[uni] = {
                            'uni': uni,
                            'count': 1,
                            'text': [text]
                        }
                    else:
                        bad_uni[uni]['count'] = bad_uni[uni]['count'] + 1
                        bad_uni[uni]['text'].append(text)

            except Exception as _e:
                pass

        unijson = json.dumps(bad_uni)
        print(unijson)


if __name__ == '__main__':
    Main().start()
