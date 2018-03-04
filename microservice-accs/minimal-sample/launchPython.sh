#!/bin/sh

# Install Python packages into python/modules folder
pip --no-cache-dir install -r python/requirements.txt -t ${PYTHONPATH}

#launch
cd python
export FLASK_APP=sample.py
flask run --host=$HOST --port=$PORT