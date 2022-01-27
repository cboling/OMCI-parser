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

import types


def camelcase(inp):
    """
    Convert input into CamelCase variable
    """
    return ''.join(i for i in inp.title() if not i.isspace())


def ascii_only(input_text):
    """
    Map Word Text to best ASCII equivalents
    See the 'findunicode.py' program for how to search for these

    :param input_text: (str) input text
    :return: (str) Ascii only text
    """
    replacements = {
        160  : u'-',
        174  : u'r',        # Registered sign
        176  : u"degree-",  # Degree sign
        177  : u"+/-",
        181  : u"u",        # Micro
        189  : u"1/2",
        215  : u'*',
        224  : u"`a",
        946  : u'B',        # Beta
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
        8226 : u'o',        # Bullet
    }
    if isinstance(input_text, types.GeneratorType):
        text = ''.join(i for i in input_text)
    else:
        text = input_text

    return ''.join(
            [u'' if len(i) == 0
             else replacements[ord(i)] if ord(i) >= 128 and ord(i) in replacements
             else i if ord(i) < 128
             else u' ' for i in text])


def ascii_no_control(input_text):
    return ascii_only(input_text).replace('\n', ' ').replace('\r', '').strip()


########################################################################
# Headers
def is_heading_style(style):
    """ True if this is a style used as a heading """
    return 'heading' in style.name.lower()[:len('heading')]


def is_ignored_heading(paragraph):
    text = paragraph.text[:12].lower()
    return 'Heading' in paragraph.style.name[:len('Heading')] and \
        any(x[:12].lower() in text for x in ('Fundamental usage',
                                             'todo - abc'))


def is_eos_heading(paragraph):          # End of ME section - ignore rest
    text = paragraph.text[:12].lower()
    return ('Heading' in paragraph.style.name[:len('Heading')] and
            any(x[:12].lower() in text for x in ('Vendor-specific usage',
                                                 'Supplementary information'))) or \
           (is_normal_style(paragraph.style) and
            any(x[:12].lower() in text for x in ('Supplementary explanation',
                                                 'Table 9.3.13-1')))


def is_relationships_header(paragraph):
    """ True if this  paragraph is a heading for the Relationships section """
    text = ascii_only(paragraph.text).strip()
    return text == 'Relationships' and \
           (is_heading_style(paragraph.style) or
            is_style(paragraph.style, 'Relationships') or
            is_style(paragraph.style, 'Normal'))    # See section 9.9.10


def is_attributes_header(paragraph):
    """ True if this paragraph is a heading for the Attributes section """
    text = ascii_only(paragraph.text).strip()
    return text == 'Attributes' and \
           (is_heading_style(paragraph.style) or
            is_style(paragraph.style, 'Relationships'))  # See section 9.3.34


def is_actions_header(paragraph):
    """ True if this paragraph is a heading for the Actions/Message-Types section """
    text = ascii_only(paragraph.text).strip()
    return text == 'Actions' and \
           (is_heading_style(paragraph.style) or
            is_normal_style(paragraph.style) or
            is_style(paragraph.style, 'Relationships') or  # See section 9.3.34
            is_style(paragraph.style, 'Attribute'))        # See section 9.1.15


def is_notifications_header(paragraph):
    """ True if this paragraph is a heading for the Notifications section """
    text = ascii_only(paragraph.text).strip()
    return text == 'Notifications' and \
           (is_heading_style(paragraph.style) or
            is_normal_style(paragraph.style) or
            is_style(paragraph.style, 'Relationships'))  # See section 9.3.34


def is_avcs_header(paragraph):
    """ True if this paragraph is a heading for the AVC section """
    text = ascii_only(paragraph.text).strip()
    # TODO: If AVCs are always tables, clean this up
    is_avc = text == 'Attribute Value Change' and is_heading_style(paragraph.style)
    return is_avc


def is_alarms_header(paragraph):
    """ True if this paragraph is a heading for the Alarms section """
    text = ascii_only(paragraph.text).strip()
    # TODO: If Alarms are always tables, clean this up
    is_alarm = text == 'Alarm' and is_heading_style(paragraph.style)
    return is_alarm


def is_tests_header(paragraph):
    """ True if this paragraph is a heading for the Test Results section """
    text = ascii_only(paragraph.text).strip()
    # TODO: If Alarms are always paragraphs without headers, clean this up
    is_test = text == 'Test Result' and is_heading_style(paragraph.style)
    return is_test

########################################################################
# Text section styles

def is_style(style, text):
    return text in style.name[:len(text)]


def is_normal_style(style):
    """ True if this is a style used for normal paragraph text """
    return is_style(style, 'Normal')


def is_description_style(style):
    """ True if this is a style used for Relationships paragraph text """
    return is_style(style, 'Normal') or is_style(style, 'Note') or is_style(style, 'Equation')


def is_relationships_style(style):
    """ True if this is a style used for Relationships paragraph text """
    return is_style(style, 'Description') or \
           is_style(style, 'Relations')


def is_attribute_style(style):
    """ True if this is a style used for Attributes paragraph text """
    return is_style(style, 'Attribute') or \
           is_style(style, 'attribute') or \
           is_style(style, 'Normal') or \
           is_style(style, 'Note')


def is_actions_style(style):
    """ True if this is a style used for Actions paragraph text """
    return is_style(style, 'Attribute') or is_style(style, 'toc')      # See 9.1.14


def is_notifications_style(style):
    """ True if this is a style used for Notifications paragraph text """
    return is_style(style, 'Attribute') or is_normal_style(style) or\
        is_style(style, 'Description') or\
        is_style(style, 'toc')                          # See 9.1.14


def is_avcs_style(style):
    """ True if this is a style used for AVCs paragraph text """
    return is_style(style, 'Attribute')


def is_alarms_style(style):
    """ True if this is a style used for Alarms paragraph text """
    return is_style(style, 'Attribute') or is_style(style, 'Note') or \
           is_style(style, 'Normal') or is_figure_style(style) or \
           is_figure_title_style(style)


def is_tests_style(style):
    """ True if this is a style used for Test Results paragraph text """
    return is_style(style, 'Attribute')


def is_figure_style(style):
    """ True if this is a style used for a figure"""
    return is_style(style, 'Figure') and not is_figure_title_style(style)


def is_figure_title_style(style):
    """ True if this is a style used for text under a figure or before a table"""
    return is_style(style, 'Figure_') or is_style(style, 'Table_')


def is_enum_style(style):
    """ True if this is a style used for enumeration (bullet lists, ...)"""
    return is_style(style, 'enumlev')


########################################################################
# Text sections text

def is_description_text(paragraph):
    """ True if this is a style used for Attributes paragraph text """
    return is_description_style(paragraph.style) or \
        is_style(paragraph.style, 'Attribute follower') or \
           (is_heading_style(paragraph.style) and
            ('Multicast interworking GEM ' in ascii_only(paragraph.text) or
             'Discovery of multicast ' in ascii_only(paragraph.text)))   # See 9.2.5


def is_relationships_text(paragraph):
    """ True if this is a style used for Attributes paragraph text """
    return not is_relationships_header(paragraph) and \
        (is_relationships_style(paragraph.style) or
         is_attribute_style(paragraph.style) or
         is_normal_style(paragraph.style) or
         is_style(paragraph.style, 'Description'))  # see 9.9.10


def is_attribute_text(paragraph):
    """ True if this is a style used for Attributes paragraph text """
    return not is_attributes_header(paragraph) and \
           (is_attribute_style(paragraph.style) or
            is_enum_style(paragraph.style) or                      # Bullet lists
            is_style(paragraph.style, 'toc') or                    # See CID: 336 (last attribute)
            (is_heading_style(paragraph.style) and                 # For bad formatting in
                'Value\tINPmin' in ascii_only(paragraph.text)) or  # section 9.7.7
            (is_normal_style(paragraph.style) and                  # section 9.2.5
                'multicast address table:' in ascii_only(paragraph.text)) or
            (is_normal_style(paragraph.style) and                  # section 9.2.12
             any(txt in ascii_only(paragraph.text) for txt in
                 ('Multicast MAC address filtering capability:',
                  'Multicast MAC address registration mode:',
                  'Multicast MAC address filtering table:',
                  'Aging timer:'))))


def is_actions_text(paragraph):
    """ True if this is a style used for Actions/msg-types paragraph text """
    return not is_actions_header(paragraph) and is_actions_style(paragraph.style)


def is_notifications_text(paragraph):
    """ True if this is a style used for Notifications paragraph text """
    return not is_notifications_header(paragraph) and is_notifications_style(paragraph.style)


def is_avcs_text(paragraph):
    """ True if this is a style used for Attribute Value Change paragraph text """
    return not is_avcs_header(paragraph) and is_avcs_style(paragraph.style)


def is_alarms_text(paragraph):
    """ True if this is a style used for Alarms paragraph text """
    return not is_alarms_header(paragraph) and is_alarms_style(paragraph.style)


def is_tests_text(paragraph):
    """ True if this is a style used for Test Results paragraph text """
    return not is_tests_header(paragraph) and is_tests_style(paragraph.style)


########################################################################
# Table support

def is_avcs_table(table):
    """ True if table of AVC notifications """
    phrase = 'attribute value change'
    return phrase == table.short_title[:len(phrase)].lower()


def is_alarms_table(table):
    """ True if table of alarms notifications """
    phrase = 'alarm'
    return phrase == table.short_title[:len(phrase)].lower()


def is_tca_table(table):
    """ True if table of Threshold Crossing Alarm notifications """
    phrase = 'threshold crossing alert'
    return phrase == table.short_title[:len(phrase)].lower()


def is_tests_table(table):
    """ True if table of Test Results notifications """
    # TODO: Dig into best way to automate test results decode!!!
    phrase = 'TODO: Test results not yet supported'
    return phrase == table.short_title[:len(phrase)].lower()
