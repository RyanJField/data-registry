#!/bin/bash
export DJANGO_SETTINGS_MODULE="drams.local-settings"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SCRC_HOME="$(dirname "${DIR}")"
nohup "$SCRC_HOME"/venv/bin/python "$SCRC_HOME"/manage.py runserver &
unset DJANGO_SETTINGS_MODULE