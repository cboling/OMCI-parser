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
from text import *
from tables import Table


def initial_parser(content, paragraphs):
    """
    Parse content for the 'initial' state of an ME.

    Possible transitions include:
        - Relationships  - if 'Relationships' paragraph header found
        - Attributes     - if 'Attributes' paragraph header found
        - Description    - if 'normal' text style

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_relationships_header(paragraph):
            return 'relationship', None

        elif is_attributes_header(paragraph):
            return 'attribute', None

        elif is_description_style(paragraph.style):
            return 'description', ascii_only(paragraph.text)

        elif is_normal_style(paragraph.style):
            return 'normal', ascii_only(paragraph.text)

    return 'failure', None


def description_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    Possible transitions include:
        - Relationships  - if 'Relationships' paragraph header found
        - Attributes     - if 'Attributes' paragraph header found
        - Description    - if 'normal' text style

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_relationships_header(paragraph):
            return 'relationship', None

        elif is_attributes_header(paragraph):
            return 'attribute', None

        elif is_description_text(paragraph) or \
                is_ignored_heading(paragraph) or \
                is_enum_style(paragraph.style):
            return 'normal', ascii_only(paragraph.text)
    else:
        # TODO: Look at 9.1.7 ONU Power shedding ME. Has table in description
        #       that may be of interest.
        return 'normal', None

    return 'failure'


def relationships_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    Possible transitions include:
        - Attributes     - if 'Attributes' paragraph header found
        - Relationships  - if 'normal' text style

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_attributes_header(paragraph):
            return 'attribute', None

        elif is_relationships_text(paragraph) or \
                is_figure_style(paragraph.style) or \
                is_figure_title_style(paragraph.style):
            return 'normal', ascii_only(paragraph.text)
    else:
        # TODO: Implement if needed, otherwise remove and fall through
        raise NotImplementedError('Table support')

    return 'failure'


def attributes_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    Possible transitions include:
        - Actions    - if 'Actions' paragraph header found
        - Attributes    - if 'normal' text style

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_actions_header(paragraph):
            return 'action', None

        elif is_attribute_text(paragraph):
            return 'normal', ascii_only(paragraph.text)

        elif is_normal_style(paragraph.style) or \
                is_figure_style(paragraph.style) or \
                is_figure_title_style(paragraph.style):
            # Before start of some attribute groups, some descriptive
            # text is provided. Ignore that for now.
            return 'normal', None

    elif isinstance(content, Table):
        return 'normal', None

    return 'failure'


def actions_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    Possible transitions include:
        - Notifications - if 'Notifications paragraph header found
        - Action        - if 'normal' text style

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_notifications_header(paragraph):
            return 'notification', None

        elif is_actions_text(paragraph):
            return 'normal', ascii_only(paragraph.text)

        elif is_normal_style(paragraph.style):
            # Before start of some actions, some descriptive
            # text may be provided. Ignore that for now.
            return 'normal', None

    else:
        # TODO: look at 9.3.22 Dot1ag MEP. Actions in lower case and also
        #       has Test action
        return 'normal', None

    return 'failure'


def notifications_parser(content, paragraphs):
    """
    Parse content for this state of an ME.  Unlike other
    ME sections, this will have either the phrase 'None'
    or it may have alarm, avc, or test results subsections.

    Possible transitions include:
        - Alarms        - if 'Alarms paragraph header found
        - AVCs          - if 'Attribute Value Changes paragraph header found
        - Tests         - if 'Test Results paragraph header found
        - Notifications - if 'normal' text style

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_avcs_header(paragraph):
            return 'avc', None

        elif is_alarms_header(paragraph):
            return 'alarm', ascii_only(paragraph.text)

        elif is_tests_header(paragraph):
            return 'test', ascii_only(paragraph.text)

        elif is_eos_heading(paragraph):
            return 'end_of_section', None

        elif is_notifications_text(paragraph):
            return 'normal', ascii_only(paragraph.text)

    elif isinstance(content, Table):
        if is_avcs_table(content):
            return 'avc', None

        elif is_alarms_table(content):
            return 'alarm', None

        elif is_tca_table(content):     # TODO: Merge with alarms
            return 'alarm', None

        elif is_tests_table(content):
            return 'test', None

        else:
            return 'normal', None       # Ignore other table types

    return 'failure'


def alarms_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_avcs_header(paragraph):
            return 'avc', None

        elif is_tests_header(paragraph):
            return 'test', ascii_only(paragraph.text)

        elif is_alarms_text(paragraph):
            return 'normal', ascii_only(paragraph.text)

    elif isinstance(content, Table):
        if is_avcs_table(content):
            return 'avc', None

        elif is_tests_table(content):
            return 'test', None

        elif not is_alarms_table(content):
            # Some MEs have additional descriptions and tables related
            # to the alarms.
            return 'normal', None

    return 'failure'


def avcs_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_alarms_header(paragraph):
            return 'alarm', ascii_only(paragraph.text)

        elif is_tests_header(paragraph):
            return 'test', ascii_only(paragraph.text)

        elif is_eos_heading(paragraph):
            return 'end_of_section', None

        elif is_avcs_text(paragraph) or \
                is_normal_style(paragraph.style) or \
                is_enum_style(paragraph.style) or \
                is_ignored_heading(paragraph):
            return 'normal', ascii_only(paragraph.text)

    elif isinstance(content, Table):
        if is_alarms_table(content):
            return 'alarm', None

        elif is_tca_table(content):     # TODO: Merge with alarms
            return 'alarm', None

        elif is_tests_table(content):
            return 'test', None

    return 'failure'


def tests_parser(content, paragraphs):
    """
    Parse content for this state of an ME

    :param content: (int) or (Table)
    :param paragraphs: (list) Docx Paragraphs

    :return: (str, str) Next state, Associated text (if any)
    """
    if isinstance(content, int):
        paragraph = paragraphs[content]

        if is_avcs_header(paragraph):
            return 'avc', None

        elif is_alarms_header(paragraph):
            return 'alarm', ascii_only(paragraph.text)

        elif is_tests_text(paragraph):
            return 'normal', ascii_only(paragraph.text)

    elif isinstance(content, Table):
        if is_avcs_table(content):
            return 'avc', None

        elif is_alarms_table(content):
            return 'alarm', None

        elif is_tca_table(content):     # TODO: Merge with alarms
            return 'alarm', None

    return 'failure'


def eos_parser(_content, _paragraphs):
    return 'end_of_section', None

