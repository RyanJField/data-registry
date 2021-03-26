#!/bin/bash
export SCRC_HOME="{$SCRC_HOME:-$HOME/.scrc}" >> "$HOME"/.profile
mkdir "$SCRC_HOME"
git clone -b local-registry https://github.com/ScottishCovidResponse/data-registry.git "$SCRC_HOME"
python3 -m venv "$SCRC_HOME"/venv
source "$SCRC_HOME"/venv/bin/activate
python -m pip install -r "$SCRC_HOME"/local-requirements.txt
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
cd "$SCRC_HOME" || exit
./rebuild-local.sh