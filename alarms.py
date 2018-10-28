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
from tca import ThresholdCrossingAlert


class Alarm(object):
    """
    Alarm Notification information.
    """
    def __init__(self, table):
        # Table number for debug purposes
        self._table_no = table.doc_table_number

        # Only defined alarms are in the table
        #   key   -> Alarm number
        #   value -> (Name, Description)
        self._alarms = dict()

    def to_dict(self):
        return self._alarms

    @staticmethod
    def create_from_table(table):
        if len(table.rows) == 0:
            return None

        try:
            alarm = Alarm(table)

            for row_num, row in enumerate(table.rows):
                number = row.get('Alarm number')
                name = row.get('Alarm')
                description = row.get('Description')
                tca = row.get('Threshold crossing alert')

                if number is None or (name is None and tca is None):
                    return None

                if row_num == 0:
                    col3 = table.heading[2].lower() if table.num_columns > 2 else ''
                    attribute = 'threshold value attribute' in col3 or \
                                'threshold data counter' in col3

                    if description is None and attribute:
                        # This is a TCA table
                        return ThresholdCrossingAlert.create_from_table(table)

                try:
                    value = int(number.strip())
                    assert 0 <= value <= 223, 'Invalid alarm number: {}'.format(value)

                    is_alarm = name.strip().lower() not in ('n/a',
                                                            'Reserved',
                                                            'Vendor-specific')
                    if is_alarm:
                        assert value not in alarm._alarms, \
                            'Alarm {} already defined'.format(value)
                        alarm._alarms[value] = (name.strip(),
                                                description.strip())

                except ValueError:  # Expected if of form  n..m
                    # Watch out for commentary text in Alarm tables
                    if 'note' == number[:4].lower():
                        continue

                    elif '(note)' == number[-6:].lower():
                        continue    # See 9.9.3

                    # There is one type with the format n.m
                    values = number.strip().split('.')
                    if len(values) == 2 and \
                            0 <= int(values[0]) <= 223 and \
                            0 <= int(values[1]) <= 223:
                        continue

                    values = number.strip().split('..')
                    assert len(values) == 2 and \
                           0 <= int(values[0]) <= 223 and \
                           0 <= int(values[1]) <= 223, 'Unexpected format in alarms'
                    pass  # Do not save (just verify n..m assumption)

            return alarm

        except Exception as e:
            print('Table number parsing error: {}'.format(e.message))
            return None
