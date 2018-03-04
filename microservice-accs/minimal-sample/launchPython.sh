#!/bin/sh
pip --no-cache-dir install -r python/requirements.txt -t ${PYTHONPATH}
uname --help
ls --help
whereis sh
pwd
export FLASK_APP=${APP_HOME}/python/sample.py
flask run --host=$HOST --port=$PORT