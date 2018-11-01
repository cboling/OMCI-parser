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
from docx import Document

from class_id import ClassIdList
from golang.classIdmap import create_class_id_map


def parse_args():
    parser = argparse.ArgumentParser(description='G.988 Final Parser')

    parser.add_argument('--ITU', '-I', action='store',
                        default='ITU-T G.988-201711.docx',
                        help='Path to ITU G.988 specification document')

    parser.add_argument('--input', '-i', action='store',
                        default='G.988.Parsed.json',
                        help='Path to parsed G.988 data, default: G.988.Parsed.json')

    parser.add_argument('--directory', '-d', action='store',
                        default='generated',
                        help='Output directory filename, default: generated')

    parser.add_argument('--template', '-t', action='store',
                        default='golang',
                        help='Jinja2 template directory, default: golang')

    args = parser.parse_args()
    return args


class Main(object):
    """ Main program """
    def __init__(self):
        self.args = parse_args()

    def load_itu_document(self):
        return Document(self.args.ITU)

    def start(self):
        print("Loading ITU Document '{}' and parsed data file '{}'".format(self.args.ITU,
                                                                           self.args.input))
        document = self.load_itu_document()
        class_ids = ClassIdList.load(self.args.input)

        # Create Class ID MAP
        create_class_id_map(class_ids, self.args.directory, self.args.template)


        # Done


if __name__ == '__main__':
    Main().start()
