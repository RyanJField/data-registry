#!/bin/bash
pgrep -f "$SCRC_HOME/manage.py runserver" | xargs kill
