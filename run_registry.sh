#!/bin/bash
mkdir ~/.scrc
export SCRC_HOME=~/.scrc
git clone -b local-registry https://github.com/ScottishCovidResponse/data-registry.git $SCRC_HOME
python3 -m venv $SCRC_HOME/venv
source $SCRC_HOME/venv/bin/activate
python -m pip install -r $SCRC_HOME/local-requirements.txt
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
cd $SCRC_HOME || exit
./rebuild-local.sh