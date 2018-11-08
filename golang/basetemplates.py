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
from . import COPYRIGHT, GENERATOR_WARNING, PACKAGE_NAME, camelcase

ME_FILENAME = '{}.go'
ME_TEMPLATES = ['attribute', 'omcidefs', 'messagetypes', 'msgbase']

# Set up filters for this module
jinja2.filters.FILTERS['camelcase'] = camelcase


def create_base_templates(outdir, templateEnv):
    """
    Create some of the common/base files for OMCI

    :param outdir: (str) Output directory for code generation
    :param templateEnv: (Jinja2 Environment) Environment for generator
    """
    for file in ME_TEMPLATES:
        filename = os.path.join(outdir, ME_FILENAME.format(file))
        template = templateEnv.get_template(file + '.go.jinja')

        with open(filename, 'w') as f:
            output = template.render(copyright=COPYRIGHT,
                                     generator_warning=GENERATOR_WARNING,
                                     package_name=PACKAGE_NAME)
            f.write(output)
            pass
