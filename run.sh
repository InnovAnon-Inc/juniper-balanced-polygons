#! /usr/bin/env bash
set -euxo nounset -o pipefail
(( UID ))
(( ! $# ))
[[ -n ${VIRTUAL_ENV:-} ]] ||
. ~/venv/bin/activate
pip install .
#python app.py
python -m juniper_polygons.app
