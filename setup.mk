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
#
# Makefile Setup
#
## VERBOSE  Option - Set V (for verbose) on the command line (make V=1 <targets...>) to see additional output
ifeq ("$(origin V)", "command line")
export Q=
else
export Q=@
export MAKEFLAGS+=--no-print-directory
endif

## NO_COLOR Option - Set NO_COLOR on the command line (make NO_COLOR=1 <targets...>) to not colorize output
ifeq ("$(origin NO_COLOR)", "command line")
export GREEN  :=
export YELLOW :=
export WHITE  :=
export CYAN   :=
export RESET  :=
else
export GREEN  := $(shell tput -Txterm setaf 2)
export YELLOW := $(shell tput -Txterm setaf 3)
export WHITE  := $(shell tput -Txterm setaf 7)
export CYAN   := $(shell tput -Txterm setaf 6)
export RESET  := $(shell tput -Txterm sgr0)
endif

