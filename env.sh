#!/usr/bin/env bash
#
# Copyright (c) 2018 - present.  Boling Consulting Solutions (bcsw.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# sourcing this file is needed to make local development and integration testing work

export PARSER_BASE=$PWD

# load local python virtualenv if exists, otherwise create it
VENVDIR="venv-$(uname -s | tr '[:upper:]' '[:lower:]')"

if [ ! -e "$VENVDIR/.built" ]; then
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Initializing OS-appropriate virtual env."
    echo "This will take a few minutes."
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    virtualenv -p python3 ${VENVDIR}
    . ${VENVDIR}/bin/activate
    pip install --upgrade pip
    if pip install -r requirements.txt; \
	    then \
	        uname -s > ${VENVDIR}/.built; \
	    fi
	(cd ${VENVDIR}/lib && find . -name python3\* -exec ln -s {} python3 \;)
fi
. ${VENVDIR}/bin/activate

# add top-level parser dir to pythonpath
export PYTHONPATH=${PARSER_BASE}/${VENVDIR}/lib/python3/site-packages:${PYTHONPATH}:${PARSER_BASE}
