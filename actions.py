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
from enum import IntEnum
from text import *


class Actions(IntEnum):
    """ G.988 Message Types """
    Create = 4
    Delete = 6
    Set = 8
    Get = 9
    GetAllAlarms = 11
    GetAllAlarmsNext = 12
    MibUpload = 13
    MibUploadNext = 14
    MibReset = 15
    AlarmNotification = 16
    AttributeValueChange = 17
    Test = 18
    StartSoftwareDownload = 19
    DownloadSection = 20
    EndSoftwareDownload = 21
    ActivateSoftware = 22
    CommitSoftware = 23
    SynchronizeTime = 24
    Reboot = 25
    GetNext = 26
    TestResult = 27
    GetCurrentData = 28
    SetTable = 29  # Defined in Extended Message Set Only

    @staticmethod
    def _action_map():
        return {
            'create'                 : Actions.Create,
            'delete'                 : Actions.Delete,
            'set'                    : Actions.Set,
            'get'                    : Actions.Get,
            'get all alarms'         : Actions.GetAllAlarms,
            'getallalarms'           : Actions.GetAllAlarms,
            'get all alarms next'    : Actions.GetAllAlarmsNext,
            'getallalarmsnext'       : Actions.GetAllAlarmsNext,
            'mib upload'             : Actions.MibUpload,
            'mibupload'              : Actions.MibUpload,
            'mib upload next'        : Actions.MibUploadNext,
            'mibuploadnext'          : Actions.MibUploadNext,
            'mib reset'              : Actions.MibReset,
            'mibreset'               : Actions.MibReset,
            'alarm'                  : Actions.AlarmNotification,
            'attribute value change' : Actions.AttributeValueChange,
            'attributevaluechange'   : Actions.AttributeValueChange,
            'test'                   : Actions.Test,
            'start software download': Actions.StartSoftwareDownload,
            'start download'         : Actions.StartSoftwareDownload,
            'startsoftwaredownload'  : Actions.StartSoftwareDownload,
            'download section'       : Actions.DownloadSection,
            'downloadsection'        : Actions.DownloadSection,
            'end software download'  : Actions.EndSoftwareDownload,
            'end download'           : Actions.EndSoftwareDownload,
            'endsoftwaredownload'    : Actions.EndSoftwareDownload,
            'activate software'      : Actions.ActivateSoftware,
            'activate image'         : Actions.ActivateSoftware,
            'activatesoftware'       : Actions.ActivateSoftware,
            'commit software'        : Actions.CommitSoftware,
            'commit image'           : Actions.CommitSoftware,
            'commitsoftware'         : Actions.CommitSoftware,
            'synchronize time'       : Actions.SynchronizeTime,
            'synchronizetime'        : Actions.SynchronizeTime,
            'reboot'                 : Actions.Reboot,
            'get next'               : Actions.GetNext,
            'getnext'                : Actions.GetNext,
            'test result'            : Actions.TestResult,
            'testresult'             : Actions.TestResult,
            'get current data'       : Actions.GetCurrentData,
            'getcurrentdata'         : Actions.GetCurrentData,
            'set table'              : Actions.SetTable,
            'settable'               : Actions.SetTable,
        }

    @staticmethod
    def keywords():
        """ Keywords for searching if text is for a supported Action/message=type """
        return Actions._action_map.keys()

    @staticmethod
    def keywords_to_access_set(keyword):
        return Actions._action_map().get(ascii_only(keyword).strip().lower())

    @staticmethod
    def load(data):
        actions = set()
        for keyword in data:
            a = Actions.keywords_to_access_set(keyword)
            if a is not None:
                actions.add(a)
        return actions

    @staticmethod
    def create_from_paragraph(paragraph):
        if paragraph.runs[0].bold:
            # New action
            text = ascii_only(' '.join(x.text for x in paragraph.runs if x.bold))

            names = text.split(',')
            actions = {Actions.keywords_to_access_set(a) for a in names}
            optional = set()  # Currently always matches the non-bold case

            if all(a is None for a in actions):
                actions = None
            else:
                # TODO: Change next to a return None after debugging all actions in doc
                assert all(a is not None for a in actions), \
                    'Partial decode: {}'.format(text)
        else:
            actions = None
            optional = None
            # Some actions are not in bold. Check text until no keywords found
            if 'optional' not in paragraph.text.lower():
                text = paragraph.text.split(',')
                actions = set()

                for name in text:
                    if len(name.strip()):
                        action = Actions.keywords_to_access_set(name.strip())
                        if action is None:
                            break
                        actions.add(action)
            else:
                optional = set()
                text = re.split(', |: |\(|\*|\n', paragraph.text.lower())
                for name in text:
                    if len(name.strip()):
                        if 'optional' in name:
                            break
                        action = Actions.keywords_to_access_set(name.strip())
                        if action is None:
                            break
                        optional.add(action)

        return actions, optional
