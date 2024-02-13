#!/usr/bin/env python3
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
import argparse
import json
import os
from re import sub

from parser_lib.parsed_json import ParsedJson


############################################################################
# This program is used to create the initial JSON test string that will be
# used to verify all GOLANG generated attribute name constants remain consistent
# in following releases of the OMCI library
############################################################################

def parse_args():
    parser = argparse.ArgumentParser(description='G.988 Extract Class Attribute Names')

    parser.add_argument('--input', '-i', action='store',
                        default='G.988.Parsed.json',
                        help='Input parsed data filename, default: G.988.Parsed.json')

    parser.add_argument('--output', '-o', action='store',
                        default='.',
                        help='Directory name to save JSON output, default: working-directory')

    args = parser.parse_args()
    return args


class Main(object):
    """ Main program """
    def __init__(self):
        self.args = parse_args()
        self.parsed = ParsedJson()
        self.filepath = self.args.output + os.path.sep + "attrNames_test.json"

    @staticmethod
    def camelCase(input: str) -> str:
        s = sub(r"(_|-|\.|/)+", " ", input).title().replace(" ", "")
        output = ''.join([s[0].upper(), s[1:]])
        return output

    @staticmethod
    def golangfile(input: str) -> str:
        s = sub(r"(|/)+", " ", input).title().replace(" ", "")
        output = ''.join([s[0].lower(), s[1:].lower()]) + ".go"
        return output

    def start(self):
        try:
            # Directory exists
            if not os.path.isdir(self.args.output):
                print("Directory '{}' does not exist", self.args.output)
                return

            # Load JSON class ID list and sort by ID
            self.parsed.load(self.args.input)

            class_ids = [c for c in self.parsed.class_ids.values()]
            class_ids.sort(key=lambda x: x.cid)

            results = {}
            for entry in class_ids:
                entry_camelCase = self.camelCase(entry.name)
                entry_filename = self.golangfile(entry.name)
                results[entry.cid] = {
                    "Name":       f"{entry.name}",
                    "Filename":   entry_filename,
                    "CamelCase":  entry_camelCase,
                    "ClassID":    entry.cid,
                    "Attributes": {},
                }
                for attribute in entry.attributes:
                    camelCase = self.camelCase(attribute.name)
                    results[entry.cid]["Attributes"][attribute.index] = {
                        "Name":       f"{attribute.name}",
                        "CamelCase":  camelCase,
                        "Final":      f"{entry_camelCase}_{camelCase}" if attribute.index != 0 else f"{camelCase}",
                        "Index":      attribute.index,
                    }
            # Output results
            json_data = json.dumps(results, indent=2, separators=(',', ': '))

        except Exception as _e:
            raise

        # Done output results
        with open(self.filepath, 'w') as json_file:
            json_file.write(json_data)
        print('Done')

if __name__ == '__main__':
    Main().start()
