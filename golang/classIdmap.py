#!/usr/bin/env python
# #
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
import jinja2
import os
from . import COPYRIGHT, GENERATED_WARNING, PACKAGE_NAME

CLASSMAP_FILENAME = 'classidmap.go'
CLASSMAP_TEMPLATE = CLASSMAP_FILENAME + '.jinja'


def create_class_id_map(class_ids, outdir, templateEnv):
    filename = os.path.join(outdir, CLASSMAP_FILENAME)
    template = templateEnv.get_template(CLASSMAP_TEMPLATE)

    with open(filename, 'w') as f:
        f.write(COPYRIGHT)

        for cid, classId in class_ids.items():
            pass