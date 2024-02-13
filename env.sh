#!/usr/bin/env bash

# load local python virtualenv if exists
VENVDIR=${VENVDIR:-venv}
PACKAGEDIR=${PACKAGEDIR:-PonAuto}

if [ -e "${VENVDIR}/.built" ]; then
    . $VENVDIR/bin/activate
else
   echo "Creating python development environment"
 	 virtualenv --python=python3.8 -v ${VENVDIR} &&\
        source ./${VENVDIR}/bin/activate && set -u && \
        pip install --disable-pip-version-check -r ${PACKAGEDIR}/requirements.txt && \
        uname -s > ${VENVDIR}/.built
fi
