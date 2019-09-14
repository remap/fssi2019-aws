#!/bin/bash
CWD="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ENV=$CWD/../env
REPO=$CWD/..
PY_COMMON=$REPO/lambda/common
TOUCH=$HOME
# PYMODULES=`ls $ENV/lib/python3.7/site-packages/`
# export PYTHONPATH=$PYTHONPATH:$PYMODULES
echo -e "import sys\nfor p in sys.path:  print(p)" | ${ENV}/bin/python > $TOUCH/sys-paths.txt
echo "${PY_COMMON}" >> $TOUCH/sys-paths.txt
