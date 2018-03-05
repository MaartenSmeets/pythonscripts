#!/bin/sh
echo Args: $@
export PYTHONPATH=`pwd`/python/modules
echo PYTHONPATH: $PYTHONPATH
pip --no-cache-dir install -r python/requirements.txt -t $PYTHONPATH
export FLASK_APP=$APP_HOME/python/sample.py
echo FLASK_APP: $FLASK_APP
ls -altr python
python -m flask run --host=$1 --port=$2