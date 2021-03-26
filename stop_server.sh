#!/bin/bash
SCRC_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pgrep -f "$SCRC_HOME/manage.py runserver" | xargs kill
