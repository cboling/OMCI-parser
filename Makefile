#
# Copyright (c) 2019 - present.  Boling Consulting Solutions (bcsw.net)
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
# Configure shell
SHELL = bash -eu -o pipefail

# Variables
VERSION                  ?= $(shell cat ../VERSION)

THIS_MAKEFILE	:= $(abspath $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))
WORKING_DIR		:= $(dir $(THIS_MAKEFILE) )
VENVDIR			:= venv-$(shell uname -s | tr '[:upper:]' '[:lower:]')
VENV_BIN		?= virtualenv
VENV_OPTS		?= --python=python3.6 -v
PYLINT_OUT		= $(WORKING_DIR)pylint.out

G988_SOURCE		?= T-REC-G.988-201711-I!!MSW-E.docx
PRE_COMPILED	?= G.988.PreCompiled.json
PARSED_JSON		?= G.988.Parsed.json
AUGMENT_YAML	?= G.988.augment.yaml
HINT_INPUT		?= --hints ${AUGMENT_YAML}

PARSER_SRC		:= $(wildcard ${WORKING_DIR}/*.py)

GO_OUTPUT		?= generated
GO_INPUT		?= golang
GOLANG_SRC		:= $(wildcard ${GO_INPUT}/*.py) $(wildcard ${GO_INPUT}/*.jinja)

default: help

# This should to be the first and default target in this Makefile
help:
	@echo "Usage: make [<target>]"
	@echo "where available targets are:"
	@echo
	@echo "generate        : Create the code-generated code"
	@echo
	@echo "help            : Print this help"
	@echo
	@echo "venv            : Build local Python virtualenv"
	@echo "lint            : Run pylint on package"
	@echo
	@echo "show-licenses   : Show imported modules and licenses"
	@echo "bandit-test     : Run bandit security test on package code"
	@echo "bandit-test-all : Run bandit security test on package and imported code"
	@echo
	@echo "clean           : Remove files created by the build"
	@echo "distclean       : Remove files created by the build and virtual environments"

${VENVDIR}/.built: requirements.txt
	@ VIRTUAL_ENV_DISABLE_PROMPT=true $(VENV_BIN) ${VENV_OPTS} ${VENVDIR};\
        source ./${VENVDIR}/bin/activate ; set -u ;\
        pip install -r requirements.txt && date >> ${VENVDIR}/.built

######################################################################
# Parsing
#
#   The word version of the ITU document requires a TIES account.  I am not positive at this time that
#   it can be shared without one.  Should I find that I can, I will check a version in at that time
#
${G988_SOURCE}:
	@ echo "--------------------------------------------------------------"
	@ echo "You must download the ${G988_SOURCE} from the ITU website"
	@ echo "--------------------------------------------------------------"
	@ exit 1

${PRE_COMPILED}: ${VENVDIR}/.built Makefile ${G988_SOURCE} ${PARSER_SRC}
	./preParse.py --input ${G988_SOURCE} --output ${PRE_COMPILED}

${PARSED_JSON}: ${PRE_COMPILED} ${PRE_COMPILED} ${AUGMENT_YAML}
	./parser.py --ITU ${G988_SOURCE} --input ${PRE_COMPILED} --output ${PARSED_JSON} ${HINT_INPUT}

generate: go-generate
	@ echo "Code generation complete"

go-generate: ${GO_OUTPUT}/version.go

${GO_OUTPUT}/version.go: ${PARSED_JSON} ${GOLANG_SRC}
	./goCodeGenerator.py --force --ITU ${G988_SOURCE} --input ${PARSED_JSON} --dir ${GO_OUTPUT}

######################################################################
# License and security checks support

show-licenses:
	@ (. ${VENVDIR}/bin/activate && \
       pip install pip-licenses && \
       pip-licenses)

bandit-test:
	@ echo "Running python security check with bandit on module code"
	@ (. ${VENVDIR}/bin/activate && pip install --upgrade bandit && bandit -n 3 -r $(WORKING_DIR))

bandit-test-all: venv bandit-test
	@ echo "Running python security check with bandit on imports"
	@ (. ${VENVDIR}/bin/activate && pip install --upgrade bandit && bandit -n 3 -r ${VENVDIR})

######################################################################
# pylint support

lint: clean
	@ echo "Executing pylint"
	@ . ${VENVDIR}/bin/activate && pip install --upgrade pylint && $(MAKE) lint-omci-parser

lint-omci-parser:
	- pylint --rcfile=${WORKING_DIR}/.pylintrc ${WORKING_DIR} 2>&1 | tee ${PYLINT_OUT}
	@ echo
	@ echo "See \"file://${PYLINT_OUT}\" for lint report"
	@ echo

######################################################################
# Cleanup

clean:
	@ find . -name '*.pyc' | xargs rm -f
	@ find . -name '__pycache__' | xargs rm -rf
	@ -find . -name 'pylint.out.*' | xargs rm -rf
	@ rm -f ${PRE_COMPILED} ${PARSED_JSON}
	@ rm -rf ${GO_OUTPUT}

distclean: clean
	@ rm -rf ${VENVDIR}

# end file
