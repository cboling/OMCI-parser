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

VERSION_FILENAME = 'version.go'
VERSION_TEMPLATE = VERSION_FILENAME + '.jinja'

# Set up filters for this module
jinja2.filters.FILTERS['camelcase'] = camelcase


def create_version_file(versions, outdir, templateEnv):
    """
    Create the version file
    :param versions: (VersionList) List of Versions used to create the generate code
    :param outdir: (str) Output directory for code generation
    :param templateEnv: (Jinja2 Environment) Environment for generator
    """
    try:
        filename = os.path.join(outdir, VERSION_FILENAME)
        template = templateEnv.get_template(VERSION_TEMPLATE)

        with open(filename, 'w') as f:
            output = template.render(copyright=COPYRIGHT,
                                     generator_warning=GENERATOR_WARNING,
                                     package_name=PACKAGE_NAME,
                                     versions=versions)
            f.write(output)

    except Exception as _e:
        raise
