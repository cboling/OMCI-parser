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

# Variables
THIS_MAKEFILE	:= $(abspath $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))
WORKING_DIR		:= $(dir $(THIS_MAKEFILE) )
PACKAGE_DIR     := $(WORKING_DIR)

include setup.mk

VENVDIR         := venv
TESTVENVDIR		:= $(VENVDIR)-test
PYVERSION       ?= ${"3.8"}
PYTHON          := python${PYVERSION}
REQUIREMENTS    ?= ${PACKAGE_DIR}/requirements.txt

G988_SOURCE     ?= T-REC-G.988-202211-I!!MSW-E.docx
#G988_SOURCE     ?= T-REC-G.988-202003-I!Amd3!MSW-E.docx
#G988_SOURCE     ?= T-REC-G.988-201711-I!!MSW-E.docx
PRE_COMPILED	?= G.988.PreCompiled.json
PARSED_JSON		?= G.988.Parsed.json
AUGMENT_YAML	?= G.988.augment.yaml
HINT_INPUT		?= --hints ${AUGMENT_YAML}

PARSER_SRC		:= $(wildcard ${WORKING_DIR}*.py) $(wildcard ${WORKING_DIR}/parser_lib*.py)

GO_OUTPUT		?= generated
GO_INPUT		?= golang
GOLANG_SRC		:= $(wildcard ${GO_INPUT}/*.py) $(wildcard ${GO_INPUT}/*.jinja)


## Defaults
default: help ## Default operation is to print this help text

## Virtual Environment
venv: requirements.txt $(VENVDIR)/.built		    ## Application virtual environment

$(VENVDIR)/.built:
	$(Q) ${PYTHON} -m venv ${VENVDIR}
	$(Q) (source ${VENVDIR}/bin/activate && \
	    if python -m pip install --disable-pip-version-check -r $(REQUIREMENTS); \
	    then \
	        uname -s > ${VENVDIR}/.built; \
	    fi)

## Parsing
#
#   The word version of the ITU document requires a TIES account.  I am not positive at this time that
#   it can be shared without one.  Should I find that I can, I will check a version in at that time
#
${G988_SOURCE}:
	@ echo "--------------------------------------------------------------"
	@ echo "You must download the ${G988_SOURCE} from the ITU website"
	@ echo "--------------------------------------------------------------"
	@ exit 1

${PRE_COMPILED}: ${VENVDIR}/.built Makefile ${G988_SOURCE} ${PARSER_SRC}  ## Preparse WORD document
	@ echo "Performing preparsing of the standards document to extract paragraph information"
	@ echo "Target is $@. Building due to dependency: $?"
	$(Q) ./preParse.py --input ${G988_SOURCE} --output ${PRE_COMPILED}

${PARSED_JSON}: ${PRE_COMPILED} ${AUGMENT_YAML}
	@ echo "Performing final parsing of the OMCI ME sections"
	@ echo "Target is $@. Building due to dependency: $?"
	$(Q) ./parser.py --ITU ${G988_SOURCE} --input ${PRE_COMPILED} --output ${PARSED_JSON} ${HINT_INPUT}

generate: preparse parse go-generate		## Create the code-generated code
	@ echo "Code generation complete"

preparse: ${PRE_COMPILED}	## Preparse the ITU Word document sections

parse: preparse ${PARSED_JSON}	    ## Parse the ITU OMCI Managed Entities specific settings

go-generate: ${GO_OUTPUT}/version.go

${GO_OUTPUT}/version.go: ${PARSED_JSON} ${GOLANG_SRC}
	./goCodeGenerator.py --force --ITU ${G988_SOURCE} --input ${PARSED_JSON} --dir ${GO_OUTPUT}

######################################################################
## License and security checks support
show-licenses:		## Show imported modules and licenses
	$(Q) (. ${VENVDIR}/bin/activate && \
       pip install pip-licenses && \
       pip-licenses)

bandit-test:  ## Run bandit security test on package code
	@ echo "Running python security check with bandit on module code"
	$(Q) (. ${VENVDIR}/bin/activate && pip install --upgrade bandit && bandit -n 3 -r $(WORKING_DIR))

bandit-test-all: venv bandit-test  ## Run bandit security test on package and imported code
	@ echo "Running python security check with bandit on imports"
	$(Q) (. ${VENVDIR}/bin/activate && pip install --upgrade bandit && bandit -n 3 -r ${VENVDIR})

######################################################################
## pylint support

lint: clean		## Run pylint on package
	@ echo "Executing pylint"
	$(Q) . ${VENVDIR}/bin/activate && pip install --upgrade pylint && $(MAKE) lint-omci-parser

lint-omci-parser:
	- pylint --rcfile=${WORKING_DIR}/.pylintrc ${WORKING_DIR} 2>&1 | tee ${PYLINT_OUT}
	@ echo
	@ echo "See \"file://${PYLINT_OUT}\" for lint report"
	@ echo

######################################################################
## Utility

clean:	## Cleanup directory of build and test artifacts
	@ find . -name '*.pyc' | xargs rm -f
	@ find . -name '__pycache__' | xargs rm -rf
	@ -find . -name 'pylint.out.*' | xargs rm -rf
	@ rm -f ${PRE_COMPILED} ${PARSED_JSON}
	@ rm -rf ${GO_OUTPUT}

distclean: clean	## Cleanup all build, test, and virtual environment artifacts
	@ rm -rf ${VENVDIR}

help: ## Print help for each Makefile target
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target> [<target> ...]${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} { \
		if (/^[a-zA-Z_-]+:.*?##.*$$/) {printf "    ${YELLOW}%-23s${GREEN}%s${RESET}\n", $$1, $$2} \
		else if (/^## .*$$/) {printf "  ${CYAN}%s${RESET}\n", substr($$1,4)} \
		}' $(MAKEFILE_LIST)

# end file
