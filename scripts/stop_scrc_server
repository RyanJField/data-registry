#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SCRC_HOME="$(dirname "${DIR}")"
pgrep -f "$SCRC_HOME/manage.py runserver" | xargs kill
