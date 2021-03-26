#!/bin/bash
ps -ef | grep "$SCRC_HOME/manage.py runserver" | grep -v grep | awk '{print $2}' | xargs kill
