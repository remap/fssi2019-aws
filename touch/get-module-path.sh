#!/bin/bash
CWD="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ENV=$CWD/../env
TOUCH=$HOME
PYMODULES=$ls env/lib/python3.7/site-packages/

export PYTHONPATH=$PYTHONPATH:$PYMODULES
echo -e "import sys\nfor p in sys.path:  print(p)" | python > $TOUCH/sys-paths.txt
