#!/bin/bash
set -e
export FAIR_HOME=$HOME/.fair/registry
mkdir -p "$FAIR_HOME"
git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME"
python3 -m venv "$FAIR_HOME"/venv
source "$FAIR_HOME"/venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r "$FAIR_HOME"/local-requirements.txt
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
cd "$FAIR_HOME"/scripts || exit
./rebuild-local.sh
