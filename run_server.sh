#!/bin/bash
export DJANGO_SETTINGS_MODULE="drams.local-settings"
nohup "$SCRC_HOME"/venv/bin/python "$SCRC_HOME"/manage.py runserver &
unset DJANGO_SETTINGS_MODULE